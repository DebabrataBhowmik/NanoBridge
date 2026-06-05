# NanoBridge

NanoBridge is a lightweight NanoAOD analysis framework developed for CMS Run-3 H → γ*γ → ℓℓγ studies.

It provides tools to:

* Read CMS NanoAOD datasets
* Build reduced analysis ntuples (mini-trees)
* Perform object-level studies of muons, photons, and jets
* Produce analysis-ready ROOT trees for further processing

## Recommended CMSSW Setup

For Run-3 NanoAODv15:

```bash
cmsrel CMSSW_15_0_19
cd CMSSW_15_0_19/src
cmsenv

git cms-init
```

Clone NanoBridge:

```bash
git clone git@github.com:DebabrataBhowmik/NanoBridge.git HiggsDalitz/NanoBridge
```

Retrieve required CMSSW packages:

```bash
git cms-addpkg PhysicsTools/NanoAOD
```

Compile:

```bash
scram b -j 8
```

## Directory Structure

```text
HiggsDalitz/
└── NanoBridge/
    ├── plugins/
    ├── python/
    ├── test/
    └── README.md
```

## Running

Example:

```bash
cd HiggsDalitz/NanoBridge/python

python run_xAnaProducer.py
```

or

```bash
python run_xAnaProducerMultiFiles.py
```

## Output

NanoBridge produces reduced ROOT ntuples containing:

* Event information
* Muon collections
* Photon collections
* Jet collections
* Derived H → γ*γ → ℓℓγ analysis variables

for subsequent physics analysis and plotting.

## Author

Debabrata Bhowmik

CMS Experiment — Run 3 Higgs Dalitz Analysis
