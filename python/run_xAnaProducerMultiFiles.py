from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor

from HiggsDalitz.NanoBridge.xAnaProducer import *

files = []

with open("input2024C.txt") as f:
    for line in f:
        files.append(line.strip())

p = PostProcessor(
    "outputDir",
    files,
    cut=None,
    branchsel=None,
    modules=[xAnaProducer(isMC=False)],
    postfix="_xAna",
    noOut=False
)

p.run()
