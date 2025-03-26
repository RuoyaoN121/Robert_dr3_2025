#!/bin/bash

# --- USER CONFIGURATION ---
# Directory with your par and tim files
DATA_DIR="../GWB_search_1_no2025_TOAerr"

# Output directory for updated par files and moving originals
OUTPUT_DIR="../test"

mkdir -p "$OUTPUT_DIR"

for PARFILE in "$DATA_DIR"/*.par; do
    BASENAME=$(basename "$PARFILE" .par)
    TIMFILE="$DATA_DIR/$BASENAME.tim"

    if [[ ! -f "$TIMFILE" ]]; then
        echo "WARNING: No matching tim file for $BASENAME, skipping."
        continue
    fi

    echo "Processing $BASENAME..."

    # Run tempo2 without GUI, fit F0 and DM, and output directly to a file
    tempo2 -nofit -f "$PARFILE" "$TIMFILE" -fit F0 -fit F1 -fit F2 -fit DM -fit DM1 -fit DM2 -newpar

    mv new.par "$OUTPUT_DIR/${BASENAME}_fit.par"
    echo "Updated par file saved to $OUTPUT_DIR/${BASENAME}_fit.par"

    # Copy the original par and tim files to the output directory
    cp "$TIMFILE" "$OUTPUT_DIR/"

    echo "Copied original files to $OUTPUT_DIR/"
done

echo "All done!"
