# Save as: run_dataset.sh
#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./run_dataset.sh path/to/list.txt [data|mc] [ERA]
# Examples:
#   ./run_dataset.sh lists/myDataset.txt mc Run3_2024
#   ./run_dataset.sh lists/SingleMuon_2024C.txt data Run3_2024

LIST_FILE="${1:?Usage: $0 path/to/list.txt [data|mc] [ERA]}"
MODE="${2:-mc}"            # "mc" or "data"
ERA="${3:-Run3_2024}"      # analysis era tag

# Derive output directory name from input list filename (without .txt)
DATASET_NAME="$(basename "${LIST_FILE%.*}")"
OUTDIR="outputs/${DATASET_NAME}"

# If OUTDIR already exists, warn and exit without overwriting
if [[ -d "$OUTDIR" ]]; then
  echo "[WARN] Output directory '${OUTDIR}' already exists. Refusing to overwrite."
  echo "       Please remove or rename it, or choose a different list file."
  exit 2
fi

# Create the fresh output directory
mkdir -p "$OUTDIR"

# Placeholder correctionlib JSONs — replace with real ones when ready
MUJSON="corrections/muon_rochester_placeholder.json"
PHJSON="corrections/photon_energy_placeholder.json"
JETJSON="corrections/jet_jerc_placeholder.json"

# MC flag
ISMC_FLAG=()
if [[ "$MODE" == "mc" ]]; then
  ISMC_FLAG=(--isMC)
fi

# Process each file listed in LIST_FILE
while IFS= read -r FILE; do
  [[ -z "$FILE" ]] && continue
  BASE="$(basename "$FILE" .root)"
  OUT="${OUTDIR}/mini_${BASE}.root"
  echo "[INFO] $FILE -> $OUT"
  python3 nano_to_miniTree_Claude.py \
    -i "$FILE" \
    -o "$OUT" \
    --era "$ERA" \
    "${ISMC_FLAG[@]}" \
    --mujson "$MUJSON" \
    --phjson "$PHJSON" \
    --jetjson "$JETJSON"
done < "$LIST_FILE"

echo "[DONE] Outputs in: $OUTDIR"
