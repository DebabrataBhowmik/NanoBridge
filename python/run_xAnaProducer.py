from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor

from HiggsDalitz.NanoBridge.xAnaProducer import *

p = PostProcessor(
    ".",
    ["053f1ca6-f80f-4d61-8419-482dc0e639d8.root"],
    cut=None,
    branchsel=None,
    modules=[xAnaProducer(isMC=False)],
    postfix="_xAna"
)

p.run()
