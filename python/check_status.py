#!/usr/bin/env python3
#================================================================
# check_status.py
#
# Run anytime to check on ONE submission's CONDOR jobs:
#   - jobs still queued/running for this submission
#   - output _xAna.root files found in this directory
#   - files still listed as failed (reads listFilesNotProcessed.txt
#     directly — run merge_failed.py first if the batch just finished)
#
# Point OUTPUT_DIR at whichever directory you care about right
# now — the original submission, or a later resubmission.
#
# Run with: python3 check_status.py <output_directory>
#================================================================

import os, sys, glob, subprocess

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <output_directory>")
    sys.exit(1)

OUTPUT_DIR = sys.argv[1]

#================================================================

def box(lines):
    width = max(len(l) for l in lines) + 4
    bar   = "+" + "-" * (width - 2) + "+"
    print(bar)
    for l in lines:
        print(f"|  {l:<{width-4}}  |")
    print(bar)

def get_cluster_id(out_dir):
    path = os.path.join(out_dir, "cluster_id.txt")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read().strip()

def get_jobs_in_cluster(cluster_id):
    """Returns (n_active, n_held) for a given ClusterId, or (None, None) on failure."""
    try:
        result = subprocess.run(
            ["condor_q", cluster_id, "-format", "%d\n", "JobStatus"],
            capture_output=True, text=True
        )
    except FileNotFoundError:
        return None, None
    if result.returncode != 0:
        return None, None
    statuses = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
    n_active = sum(1 for s in statuses if s in ("1", "2"))   # idle or running
    n_held   = sum(1 for s in statuses if s == "5")
    return n_active, n_held

def count_lines(path):
    if not os.path.exists(path):
        return 0
    with open(path) as f:
        return sum(1 for ln in f if ln.strip() and not ln.startswith("#"))

def main():
    if not os.path.exists(OUTPUT_DIR):
        print(f"[ERROR] Output directory not found: {OUTPUT_DIR}")
        sys.exit(1)

    n_expected = count_lines(os.path.join(OUTPUT_DIR, "input_filelist.txt"))
    out_files  = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_xAna.root")]
    n_done     = len(out_files)
    n_failed   = count_lines(os.path.join(OUTPUT_DIR, "listFilesNotProcessed.txt"))

    # Warn if there are unmerged per-job failure markers sitting around —
    # these mean some files failed but haven't been combined into
    # listFilesNotProcessed.txt yet.
    unmerged_markers = glob.glob(os.path.join(OUTPUT_DIR, "FAILED_*.txt"))

    cluster_id = get_cluster_id(OUTPUT_DIR)
    n_active, n_held = (None, None)
    if cluster_id:
        n_active, n_held = get_jobs_in_cluster(cluster_id)

    # ── Print summary box ────────────────────────────────────────────────────
    lines = [
        f"  Status check",
        "",
        f"  Output dir          :  {OUTPUT_DIR}",
    ]
    if cluster_id:
        lines.append(f"  ClusterId            :  {cluster_id}")
    else:
        lines.append(f"  ClusterId            :  not found (cluster_id.txt missing)")

    lines.append(f"  Expected files       :  {n_expected}")
    lines.append(f"  Output files found   :  {n_done}")
    lines.append(f"  Failed (logged)      :  {n_failed}")

    if n_active is not None:
        lines.append(f"  Jobs running/idle    :  {n_active}")
        lines.append(f"  Jobs held (stuck)    :  {n_held}")
    else:
        lines.append(f"  Jobs in queue        :  could not determine")

    lines.append("")
    if n_active is not None:
        if n_active == 0 and n_held == 0:
            if n_failed == 0:
                lines.append("  >>> COMPLETE — all files processed successfully <<<")
            else:
                lines.append(f"  >>> Finished, but {n_failed} file(s) failed <<<")
                lines.append("  >>> Resubmit with resubmit_failed.py <<<")
        else:
            lines.append(f"  >>> Still running: {n_active} active, {n_held} held <<<")
            if n_held:
                lines.append("  >>> WARNING: held jobs need attention — condor_q -hold <<<")
    else:
        accounted = n_done + n_failed
        remaining = n_expected - accounted
        if remaining <= 0:
            lines.append("  >>> All files accounted for on disk <<<")
        else:
            lines.append(f"  >>> {remaining} file(s) unaccounted for (queue status unknown) <<<")

    print()
    box(lines)
    print()

    if unmerged_markers:
        print(f"\033[93m[WARN] {len(unmerged_markers)} unmerged FAILED_*.txt marker(s) found.\033[0m")
        print(f"\033[93m       Run this first to update listFilesNotProcessed.txt:\033[0m")
        print(f"\033[93m       python3 merge_failed.py {OUTPUT_DIR}\033[0m")
        print()

if __name__ == "__main__":
    main()
