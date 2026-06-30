#!/usr/bin/env python3
#================================================================
# resubmit_failed.py
#
# Reads listFilesNotProcessed.txt and resubmits failed jobs.
# Run with: python3 resubmit_failed.py
#================================================================

#================================================================
#            *** CONFIGURE HERE BEFORE RUNNING ***
#================================================================

FAILED_LIST = "/eos/user/d/dbhowmik/NCU/HiggsDalitz/Run3Analysis/2024Analysis/CMSSW_15_0_19/src/HiggsDalitz/NanoBridge/python/outputs/2024C/listFilesNotProcessed.txt"
ERA         = "2024C"
MODE        = "data"       # "data" or "mc"
FLAVOUR     = "testmatch"  # longlunch=2h | workday=8h | tomorrow=24h

#================================================================
#   Fixed paths — change only if you move your CMSSW area
#================================================================

#CMSSW_BASE  = "/eos/user/d/dbhowmik/NCU/HiggsDalitz/Run3Analysis/2024Analysis/CMSSW_15_0_19"
CMSSW_BASE  = "/afs/cern.ch/work/d/dbhowmik/public/NCU/HiggsDalitz/Run3Analysis/CMSSW_15_0_19"
WORK_DIR    = f"{CMSSW_BASE}/src/HiggsDalitz/NanoBridge/python"
OUTPUT_BASE = "/eos/user/d/dbhowmik/NCU/HiggsDalitz/Run3Analysis/2024Analysis/NanoBridge_outputs"
LOG_BASE    = f"{WORK_DIR}/condor_logs"
WRAPPER     = f"{WORK_DIR}/condor_wrapper.sh"

#================================================================
import os, sys, shutil, subprocess
from datetime import datetime

FLAVOUR_TIMES = {
    "espresso":    "20 min",
    "microcentury":"1 h",
    "longlunch":   "2 h",
    "workday":     "8 h",
    "tomorrow":    "24 h",
    "testmatch":   "3 h",
    "nextweek":    "168 h",
}

def make_versioned_dir(base):
    if not os.path.exists(base):
        os.makedirs(base)
        return base
    for v in range(2, 100):
        c = f"{base}_v{v}"
        if not os.path.exists(c):
            os.makedirs(c)
            return c
    c = f"{base}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(c)
    return c

def box(lines):
    width = max(len(l) for l in lines) + 4
    bar   = "+" + "-" * (width - 2) + "+"
    print(bar)
    for l in lines:
        print(f"|  {l:<{width-4}}  |")
    print(bar)

def get_valid_proxy():
    """
    Check for a valid grid proxy (via voms-proxy-info). If missing or
    expired, print instructions and exit — CONDOR jobs need this to
    access files via xrootd.
    """
    try:
        result = subprocess.run(
            ["voms-proxy-info", "--exists"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            raise RuntimeError("no valid proxy")
    except (FileNotFoundError, RuntimeError):
        print("[ERROR] No valid grid proxy found.")
        print("        Generate one with:")
        print("          voms-proxy-init --voms cms --valid 168:00")
        print("        Then re-run this script.")
        sys.exit(1)

    path_result = subprocess.run(
        ["voms-proxy-info", "--path"], capture_output=True, text=True
    )
    proxy_path = path_result.stdout.strip()

    # voms-proxy-info can report a path that no longer exists on disk
    # (e.g. /tmp cleared, stale session). CONDOR's file transfer will
    # fail with a cryptic "No such file or directory" hold if we don't
    # catch this here first.
    if not proxy_path or not os.path.isfile(proxy_path):
        print(f"[ERROR] Proxy path reported by voms-proxy-info does not exist on disk:")
        print(f"        {proxy_path or '(empty)'}")
        print("        Regenerate it with:")
        print("          voms-proxy-init --voms cms --valid 168:00")
        print("        Then re-run this script.")
        sys.exit(1)

    # CONDOR's remote schedd (e.g. bigbird13) cannot read your local /tmp
    # on lxplus — that's machine-local storage, not shared. Rather than
    # requiring you to permanently relocate your proxy (which other tools
    # may expect at the default /tmp location), we copy it to an
    # AFS-visible staging area just for this submission.
    if proxy_path.startswith("/tmp"):
        staging_dir = os.path.join(WORK_DIR, ".proxy_staging")
        os.makedirs(staging_dir, exist_ok=True)
        staged_path = os.path.join(staging_dir, os.path.basename(proxy_path))
        shutil.copyfile(proxy_path, staged_path)
        os.chmod(staged_path, 0o600)
        print(f"[INFO] Proxy is under /tmp (not visible to the CONDOR schedd).")
        print(f"       Copied to AFS-visible staging location for this submission:")
        print(f"       {staged_path}")
        proxy_path = staged_path

    timeleft_result = subprocess.run(
        ["voms-proxy-info", "--timeleft"], capture_output=True, text=True
    )
    try:
        timeleft = int(timeleft_result.stdout.strip())
    except ValueError:
        timeleft = None

    if timeleft is not None and timeleft < 3600:
        print(f"[WARN] Proxy valid for less than 1 hour ({timeleft}s left).")
        print("       Consider renewing: voms-proxy-init --voms cms --valid 168:00")

    return proxy_path

def main():
    if MODE not in ("data", "mc"):
        print("[ERROR] MODE must be 'data' or 'mc'"); sys.exit(1)

    if not os.path.exists(FAILED_LIST):
        print(f"[ERROR] File not found: {FAILED_LIST}"); sys.exit(1)

    failed_files = []
    with open(FAILED_LIST) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            path = line.split("#")[0].strip()
            if path:
                failed_files.append(path)

    if not failed_files:
        print("[INFO] No failed files found. Nothing to resubmit.")
        sys.exit(0)

    era_base = os.path.join(OUTPUT_BASE, ERA)
    out_dir  = make_versioned_dir(era_base)
    log_dir  = os.path.join(LOG_BASE, ERA + "_resub",
                            datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(log_dir, exist_ok=True)

    flavour_time = FLAVOUR_TIMES.get(FLAVOUR, "?")
    proxy_path = get_valid_proxy()

    # ── Print config box ─────────────────────────────────────────────────────
    print()
    box([
        "  xAnaProducer  —  CONDOR Resubmission",
        "",
        f"  Failed list :  {FAILED_LIST}",
        f"  Era         :  {ERA}",
        f"  Mode        :  {MODE}",
        f"  Flavour     :  {FLAVOUR}  ({flavour_time} per job)",
        f"  Files       :  {len(failed_files)} to resubmit",
        f"  Output      :  {out_dir}",
        f"  Logs        :  {log_dir}",
        f"  Submitted   :  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Proxy       :  {proxy_path}",
    ])
    print()

    # ── Write CONDOR submit file ──────────────────────────────────────────────
    submit_path = os.path.join(out_dir, f"condor_resub_{ERA}.jdl")
    lines = [
        f"# CONDOR resubmit file — generated by resubmit_failed.py",
        f"# Source  : {FAILED_LIST}",
        f"# Era     : {ERA}   Mode: {MODE}",
        f"# Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "universe              = vanilla",
        f"executable            = {WRAPPER}",
        "should_transfer_files = YES",
        "when_to_transfer_output = ON_EXIT",
        f"x509userproxy         = {proxy_path}",
        "",
        f'+JobFlavour           = "{FLAVOUR}"',
        "",
        f"log    = {log_dir}/job_$(ClusterId).log",
        f"output = {log_dir}/job_$(ClusterId)_$(ProcId).out",
        f"error  = {log_dir}/job_$(ClusterId)_$(ProcId).err",
        "",
        "max_retries           = 2",
        "",
    ]
    for fpath in failed_files:
        lines += [f"arguments = {fpath} {out_dir} {MODE}", "queue", ""]

    with open(submit_path, "w") as sf:
        sf.write("\n".join(lines))

    # ── Submit ────────────────────────────────────────────────────────────────
    print(f"[INFO] Resubmitting {len(failed_files)} jobs to CONDOR ...")
    result = subprocess.run(["condor_submit", submit_path], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(f"[ERROR] condor_submit failed:\n{result.stderr}")
        sys.exit(1)

    cluster_id = None
    for line in result.stdout.splitlines():
        if "cluster" in line.lower():
            parts = line.strip().rstrip(".").split()
            cluster_id = parts[-1]
            break

    # Save ClusterId so check_status.py can track this resubmission's queue status
    if cluster_id:
        with open(os.path.join(out_dir, "cluster_id.txt"), "w") as cf:
            cf.write(cluster_id + "\n")

    # Save the resubmitted file list (so check_status.py can compute "expected" count for this dir)
    with open(os.path.join(out_dir, "input_filelist.txt"), "w") as fl:
        fl.write(f"# Resubmission of failed files from: {FAILED_LIST}\n")
        fl.write(f"# Era: {ERA}   Mode: {MODE}\n\n")
        for fpath in failed_files:
            fl.write(fpath + "\n")

    print()
    box([
        f"  {len(failed_files)} jobs resubmitted successfully!",
        "",
        f"  ClusterId : {cluster_id or 'see condor_submit output above'}",
        "",
        "  Useful commands:",
        f"    Monitor  :  condor_q {cluster_id or '<ClusterId>'}",
        f"    Kill all :  condor_rm {cluster_id or '<ClusterId>'}",
        "    Details  :  condor_q -better-analyze <ClusterId>.<ProcId>",
        "",
        f"  Outputs  :  {out_dir}",
        f"  Logs     :  {log_dir}",
    ])
    print()

if __name__ == "__main__":
    main()
