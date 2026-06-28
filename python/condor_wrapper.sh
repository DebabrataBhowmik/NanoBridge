#!/bin/bash
#---------------------------------------------------------------
# condor_wrapper.sh
# Called by each CONDOR job with a single input file path.
# Usage: condor_wrapper.sh <input_file> <output_dir> <data|mc>
#---------------------------------------------------------------

INPUT_FILE=$1
OUTPUT_DIR=$2
MODE=$3

CMSSW_BASE=/eos/user/d/dbhowmik/NCU/HiggsDalitz/Run3Analysis/2024Analysis/CMSSW_15_0_19
PYTHON_DIR=${CMSSW_BASE}/src/HiggsDalitz/NanoBridge/python

echo "=============================================="
echo " CONDOR job starting"
echo " Input  : ${INPUT_FILE}"
echo " Output : ${OUTPUT_DIR}"
echo " Mode   : ${MODE}"
echo " Host   : $(hostname)"
echo " Date   : $(date)"
echo "=============================================="

# Set up CMSSW environment
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd ${CMSSW_BASE}
eval `scramv1 runtime -sh`   # cmsenv equivalent in batch
cd ${PYTHON_DIR}

# Run the producer on this single file
python3 run_xAnaProducerMultiFiles_fixed.py <(echo "${INPUT_FILE}") ${OUTPUT_DIR} ${MODE}

EXIT_CODE=$?
echo "=============================================="
echo " Job finished with exit code: ${EXIT_CODE}"
echo " Date: $(date)"
echo "=============================================="
exit ${EXIT_CODE}
