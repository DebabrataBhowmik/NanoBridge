#!/usr/bin/env python3
#---------------------------------How to run-----------------------
# cmsenv
# python run_xAnaProducerMultiFiles_fixed.py input2024C.txt /output/dir data 2024
# python run_xAnaProducerMultiFiles_fixed.py input2024MC.txt /output/dir mc 2024
# 4th argument: year (2022, 2023, 2024, 2025, 2026)
# For MC the JSON is ignored even if provided.
#------------------------------------------------------------------

#================================================================
#   Golden JSON URLs — one per year.
#   If a year has no JSON yet, set it to None.
#   The script will warn but NOT crash if the URL is None or
#   if the download fails — it will simply run without JSON
#   filtering and tell you clearly.
#================================================================
GOLDEN_JSON_URLS = {
    "2022": "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json",
    "2023": "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json",
    "2024": "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions24/Cert_Collisions2024_378981_386951_Golden.json",
    "2025": "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions25/Cert_Collisions2025_391658_398903_Golden.json",
    "2026": None,   # not available yet
}

#================================================================
import os, sys, tempfile, urllib.request
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from HiggsDalitz.NanoBridge.xAnaProducer_fixed import xAnaProducer


def fetch_golden_json(year, is_mc):
    """
    Download the golden JSON for the given year to a temp file.
    Returns the local path on success, or None if:
      - mode is MC (no JSON needed)
      - year is not in the known list
      - URL is None (not available yet)
      - download fails
    In all non-success cases, prints a clear message but does NOT crash.
    The caller must delete the returned file when done.
    """
    if is_mc:
        return None

    if year not in GOLDEN_JSON_URLS:
        print(f"\033[93m[WARN] No golden JSON entry for year '{year}'.\033[0m")
        print(f"\033[93m       Known years: {list(GOLDEN_JSON_URLS.keys())}\033[0m")
        print(f"\033[93m       Running WITHOUT lumi filtering.\033[0m")
        return None

    url = GOLDEN_JSON_URLS[year]
    if url is None:
        print(f"\033[93m[WARN] Golden JSON for year {year} is not available yet (URL is None).\033[0m")
        print(f"\033[93m       Running WITHOUT lumi filtering.\033[0m")
        return None

    print(f"[INFO] Downloading golden JSON for {year}:\n       {url}")
    try:
        tmp = tempfile.NamedTemporaryFile(
            suffix=".json", prefix=f"golden_json_{year}_", delete=False
        )
        urllib.request.urlretrieve(url, tmp.name)
        print(f"[INFO] Golden JSON saved to: {tmp.name}")
        return tmp.name
    except Exception as e:
        print(f"\033[93m[WARN] Failed to download golden JSON: {e}\033[0m")
        print(f"\033[93m       Running WITHOUT lumi filtering.\033[0m")
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)
        return None


def check_file(path):
    """
    Try to open the file and verify it has a readable Events TTree.
    Returns (True, "") on success, (False, reason) on failure.
    """
    try:
        f = ROOT.TFile.Open(path)
        if not f or f.IsZombie():
            return False, "TFile::Open returned null or zombie"
        if f.TestBit(ROOT.TFile.kRecovered):
            f.Close()
            return False, "file was recovered (likely corrupt)"
        t = f.Get("Events")
        if not t:
            f.Close()
            return False, "no 'Events' TTree found inside file"
        n = t.GetEntries()   # triggers actual I/O — catches broken files
        f.Close()
        return True, ""
    except Exception as e:
        return False, str(e)


def main():
    if len(sys.argv) < 5:
        print("Usage: run_xAnaProducerMultiFiles_fixed.py "
              "<input_list.txt> <output_dir> <data|mc> <year>")
        print("  year: 2022, 2023, 2024, 2025, 2026")
        sys.exit(1)

    list_path = sys.argv[1]
    out_dir   = sys.argv[2]
    mode      = sys.argv[3].lower()
    year      = sys.argv[4]

    if mode not in ("data", "mc"):
        print("[ERROR] Third arg must be 'data' or 'mc'")
        sys.exit(1)
    is_mc = (mode == "mc")

    with open(list_path) as f:
        files = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    if not files:
        print("[ERROR] empty file list")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    # ── Download golden JSON once per job (data only) ─────────────────────────
    json_path = fetch_golden_json(year, is_mc)

    bad_files = []
    n_total   = len(files)
    n_ok      = 0
    n_bad     = 0

    try:
        for i, fpath in enumerate(files, 1):
            print(f"\n[{i}/{n_total}] Checking: {fpath}")

            ok, reason = check_file(fpath)
            if not ok:
                print(f"\033[93m[WARN] Skipping file — {reason}\033[0m")
                print(f"\033[93m       {fpath}\033[0m")
                bad_files.append((fpath, reason))
                n_bad += 1
                continue

            print(f"[{i}/{n_total}] Processing...")
            try:
                p = PostProcessor(
                    out_dir,
                    [fpath],
                    cut          = None,
                    branchsel    = None,
                    modules      = [xAnaProducer(isMC=is_mc, outDir=out_dir)],
                    postfix      = "_xAna",
                    noOut        = True,
                    jsonInput    = json_path,   # None → no filtering
                    histFileName = None,
                    histDirName  = None,
                )
                p.run()
                n_ok += 1
            except Exception as e:
                print(f"\033[93m[WARN] Processing failed — {e}\033[0m")
                print(f"\033[93m       {fpath}\033[0m")
                bad_files.append((fpath, f"processing error: {e}"))
                n_bad += 1

    finally:
        # Always clean up the temp JSON file, even if something crashed
        if json_path and os.path.exists(json_path):
            os.unlink(json_path)
            print(f"[INFO] Cleaned up temporary JSON file.")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Total files   : {n_total}")
    print(f"  Processed OK  : {n_ok}")
    print(f"  Skipped/failed: {n_bad}")
    print(f"  Outputs in    : {out_dir}")
    print(f"{'='*60}")

    if bad_files:
        bad_list_path = os.path.join(out_dir, "listFilesNotProcessed.txt")
        with open(bad_list_path, "w") as bf:
            bf.write("# Files that could not be opened or processed\n")
            bf.write(f"# Run: {' '.join(sys.argv)}\n\n")
            for path, reason in bad_files:
                bf.write(f"{path}  # {reason}\n")
        print(f"\n\033[93m[WARN] {n_bad} file(s) skipped — see: {bad_list_path}\033[0m")

    print(f"\n[DONE]")


if __name__ == "__main__":
    main()
