#!/usr/bin/env python3
import sys, os, subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: run_dataset.py path/to/list.txt [data|mc] [ERA]")
        sys.exit(1)

    list_file = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "mc"       # "mc" or "data"
    era  = sys.argv[3] if len(sys.argv) > 3 else "Run3_2024"

    dataset_name = os.path.splitext(os.path.basename(list_file))[0]
    outdir = os.path.join("outputs", dataset_name)

    if os.path.isdir(outdir):
        print(f"[WARN] Output directory '{outdir}' already exists. Refusing to overwrite.")
        print("       Remove/rename it or change the list file name.")
        sys.exit(2)
    os.makedirs(outdir, exist_ok=False)

    mujson = "corrections/muon_rochester_placeholder.json"
    phjson = "corrections/photon_energy_placeholder.json"
    jetjson= "corrections/jet_jerc_placeholder.json"

    ismc_flag = ["--isMC"] if mode.lower() == "mc" else []

    with open(list_file) as f:
        for line in f:
            file = line.strip()
            if not file:
                continue
            base = os.path.basename(file)
            if base.endswith(".root"):
                base = base[:-5]
            out = os.path.join(outdir, f"mini_{base}.root")
            print(f"[INFO] {file} -> {out}")
            cmd = [
                sys.executable, "nano_to_minitree_corr.py",
                "-i", file,
                "-o", out,
                "--era", era,
                "--mujson", mujson,
                "--phjson", phjson,
                "--jetjson", jetjson,
            ] + ismc_flag
            subprocess.check_call(cmd)

    print(f"[DONE] Outputs in: {outdir}")

if __name__ == "__main__":
    main()
