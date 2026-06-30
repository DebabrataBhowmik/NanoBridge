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

python3 run_xAnaProducerMultiFiles_fixed.py input2024C.txt outputs/2024C data
```

---------------------------------------------------------------------
## For condor submission:

The workflow for each new era is just:

Open submit_condor.py, change DATASET, ERA, MODE at the top

```bash
python3 submit_condor.py
```

If anything looks wrong in the first box, condor_rm <ClusterId> before jobs start running

The printout on the terminal will tell you exactly what to be done to monitor your jobs, your job id etc etc...

If any input file is not readable or non-processable, a file with the name of the root file would be written in the output directory.

However, if you are lazy enough even to do what is being printed out on the terminal, or working from somwhere else

you can just run:

```bash
python3 check_status.py <Output_DirectoryName> (without "")
```

This will tells you almost everything, also will merge the failed file lists into a single file called "listFilesNotProcessed.txt" so that you can have a full list in one place.


And for resubmission, open resubmit_failed.py, set FAILED_LIST to point to the right listFilesNotProcessed.txt, adjust ERA/MODE if needed, and

```bash
python3 resubmit_failed.py.
```

-------------------------------------------------------------------------
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
