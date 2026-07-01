#!/bin/bash
#---------------------------------------------------------------
# condor_wrapper.sh
# Called by each CONDOR job with a single input file path.
# Usage: condor_wrapper.sh <input_file> <output_dir> <data|mc> <year>
#---------------------------------------------------------------

INPUT_FILE=$1
OUTPUT_DIR=$2
MODE=$3
YEAR=$4

CMSSW_BASE=/afs/cern.ch/work/d/dbhowmik/public/NCU/HiggsDalitz/Run3Analysis/CMSSW_15_0_19
PYTHON_DIR=${CMSSW_BASE}/src/HiggsDalitz/NanoBridge/python

echo "=============================================="
echo " CONDOR job starting"
echo " Input  : ${INPUT_FILE}"
echo " Output : ${OUTPUT_DIR}"
echo " Mode   : ${MODE}"
echo " Year   : ${YEAR}"
echo " Host   : $(hostname)"
echo " Date   : $(date)"
echo "=============================================="

# Grid proxy: CONDOR transfers the proxy file into the job's working
# directory when x509userproxy is set in the .jdl. Worker nodes don't
# inherit your interactive proxy, so we must point X509_USER_PROXY at
# the transferred copy explicitly.
if [ -n "${X509_USER_PROXY}" ] && [ -f "$(pwd)/$(basename ${X509_USER_PROXY})" ]; then
    export X509_USER_PROXY="$(pwd)/$(basename ${X509_USER_PROXY})"
fi
echo " X509_USER_PROXY=${X509_USER_PROXY}"
echo "=============================================="

# Set up CMSSW environment
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd ${CMSSW_BASE}
eval `scramv1 runtime -sh`   # cmsenv equivalent in batch
cd ${PYTHON_DIR}

# Each CONDOR job processes exactly one file, but run_xAnaProducerMultiFiles_fixed.py
# writes its failure list as listFilesNotProcessed.txt directly inside OUTPUT_DIR
# (overwrite mode). Since OUTPUT_DIR is SHARED across all jobs in this submission,
# many jobs writing that same filename concurrently would clobber each other,
# leaving only the last job's single failure on record.
#
# Fix: run the python script with a job-private OUTPUT_DIR (a unique scratch
# subfolder), so its listFilesNotProcessed.txt write never collides with any
# other job. The actual _xAna.root output still gets written into a job-private
# folder too — we then move just the root file into the real shared OUTPUT_DIR,
# and if a failure list was produced, rename it uniquely before moving it there.

JOB_SCRATCH="${OUTPUT_DIR}/.job_scratch_$(basename ${INPUT_FILE} .root)_${$}"
mkdir -p "${JOB_SCRATCH}"

python3 run_xAnaProducerMultiFiles_fixed.py <(echo "${INPUT_FILE}") "${JOB_SCRATCH}" ${MODE} ${YEAR}
EXIT_CODE=$?

# Move any produced ROOT output into the real shared output directory
for f in "${JOB_SCRATCH}"/*_xAna.root; do
    [ -e "$f" ] && mv "$f" "${OUTPUT_DIR}/"
done

# If this job's file failed, its listFilesNotProcessed.txt will contain
# exactly one line (this job processed exactly one file). Rename it
# uniquely so it doesn't collide with other jobs' failure records, then
# move it into the shared output directory.
if [ -f "${JOB_SCRATCH}/listFilesNotProcessed.txt" ]; then
    SAFE_NAME=$(basename "${INPUT_FILE}" .root | tr -c 'A-Za-z0-9_' '_')
    mv "${JOB_SCRATCH}/listFilesNotProcessed.txt" \
       "${OUTPUT_DIR}/FAILED_${SAFE_NAME}_${$}.txt"
fi

# Clean up the now-empty job scratch directory
rmdir "${JOB_SCRATCH}" 2>/dev/null

echo "=============================================="
echo " Job finished with exit code: ${EXIT_CODE}"
echo " Date: $(date)"
echo "=============================================="
exit ${EXIT_CODE}
