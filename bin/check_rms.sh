#!/bin/bash

# Check if directory argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIRECTORY="$1"
# Save output file in the same directory as the input files
OUTPUT_FILE="../info/timing_results_2.csv"

# Create CSV header
echo "Pulsar, pre-fit, post-fit, Chi2r, Npoints" > "$OUTPUT_FILE"

# Modify the chi2r extraction to get the exact value (1.02094 in your example)
for parfile in "$DIRECTORY"/*.par; do
    # Extract filename without extension
    basename=$(basename "$parfile" .par)
    timfile="$DIRECTORY/$basename.tim"
    
    # Check if corresponding tim file exists
    if [ -f "$timfile" ]; then
        echo "Processing $basename..."
        
        # Run tempo2 commands and extract the required information
        postfit=$(tempo2 -f "$parfile" "$timfile" | grep 'RMS post-fit residual =' | awk '{print $(NF-1)}')
        prefit=$(tempo2 -f "$parfile" "$timfile" | grep 'RMS post-fit residual =' | awk '{print $(NF-7)}')
        chi2r=$(tempo2 -f "$parfile" "$timfile" | grep 'Chisqr' | awk '{print $(NF-3)}')
        npoints=$(tempo2 -f "$parfile" "$timfile" | grep 'Number of points in fit =' | awk '{print $NF}')
        
        # Write results to CSV
        echo "$basename,$prefit,$postfit,$chi2r,$npoints"
        echo "$basename,$prefit,$postfit,$chi2r,$npoints" >> "$OUTPUT_FILE"
    else
        echo "Warning: No matching tim file found for $basename.par"
    fi
done
echo "Results saved to $OUTPUT_FILE"