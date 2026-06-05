#!/usr/bin/env python3
import os, sys
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
#from HiggsDalitz.NanoBridge.xAnaProducer import xAnaProducer
from HiggsDalitz.NanoBridge.xAnaProducer_writtenByChatGPTcorrectedByClaude import xAnaProducer

def main():
    if len(sys.argv) < 4:
        print("Usage: run_postproc.py <input_list.txt> <output_dir> <data|mc>")
        sys.exit(1)

    list_path = sys.argv[1]
    out_dir   = sys.argv[2]
    mode      = sys.argv[3].lower()
    is_mc = (mode == "mc")
    if mode not in ("data","mc"):
        print("Third arg must be data|mc")
        sys.exit(1)

    with open(list_path) as f:
        files = [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

    if not files:
        print("[ERROR] empty file list")
        sys.exit(1)

    os.makedirs(out_dir, exist_ok=True)

    p = PostProcessor(
        out_dir,
        files,
        cut=None,
        branchsel=None,
        modules=[xAnaProducer(isMC=is_mc)],
        postfix="_xAna",
        noOut=False,          # write outputs
        histFileName=None,
        histDirName=None,
    )
    p.run()
    print(f"[DONE] Outputs in: {out_dir}")

if __name__ == "__main__":
    main()
