#!/bin/bash

# Directory containing the original .tim files
INPUT_DIR="../GWB_search_1_no2025"  # change this if your tim files are elsewhere

# Output directory
OUTPUT_DIR="../GWB_search_1_cut10_no2025"

# Path to your .par file (assuming it's the same for all tim files)
PAR_FILE="mypar.par"  # replace with the actual par file you're using

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Loop through all .tim files in the input directory
for TIM_FILE in "$INPUT_DIR"/*.tim; do
    # Get the base name of the .tim file (without the path)
    TIM_BASENAME=$(basename "$TIM_FILE")
    
    # Define the output file path
    OUTPUT_TIM_FILE="$OUTPUT_DIR/$TIM_BASENAME"
    
    echo "Processing $TIM_FILE -> $OUTPUT_TIM_FILE"

    # Run tempo2 with the general2 plugin to filter TOAs
    tempo2 -gr general2 -f "$PAR_FILE" "$TIM_FILE" -filterE 10 -writeTim "$OUTPUT_TIM_FILE"
    
    echo "Finished processing $TIM_FILE"
done

echo "All files processed! Filtered .tim files are in $OUTPUT_DIR"
