#!/usr/bin/env python3
#---------------------------------How to run-----------------------
# cmsenv
# python run_xAnaProducerMultiFiles_fixed.py input2024C.txt outputs/2024C data
#------------------------------------------------------------------
import os, sys
import ROOT
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from HiggsDalitz.NanoBridge.xAnaProducer_fixed import xAnaProducer

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
    if len(sys.argv) < 4:
        print("Usage: run_postproc.py <input_list.txt> <output_dir> <data|mc>")
        sys.exit(1)

    list_path = sys.argv[1]
    out_dir   = sys.argv[2]
    mode      = sys.argv[3].lower()

    if mode not in ("data", "mc"):
        print("Third arg must be data|mc")
        sys.exit(1)
    is_mc = (mode == "mc")

    with open(list_path) as f:
        files = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    if not files:
        print("[ERROR] empty file list")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    bad_files    = []
    n_total      = len(files)
    n_ok         = 0
    n_bad        = 0

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
