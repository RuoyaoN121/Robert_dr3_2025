#!/bin/bash

# Directory where pulsar data is stored
SOURCE_DIR="/fred/oz002/users/mbailes/astral/timing2025/partim_obs_2"
# Destination directory
DEST_DIR="/fred/oz002/users/mbailes/astral/timing2025/GWB_search_2"  # Replace with actual destination

# Check if destination directory exists, create if not
if [ ! -d "$DEST_DIR" ]; then
    mkdir -p "$DEST_DIR"
    echo "Created destination directory: $DEST_DIR"
fi

# Enter source directory
cd "$SOURCE_DIR" || { echo "Error: Cannot access $SOURCE_DIR"; exit 1; }

# Loop through each pulsar directory
for pulsar_dir in */; do
    # Remove trailing slash
    pulsar_dir=${pulsar_dir%/}
    
    # Extract Jname from directory name
    Jname=$pulsar_dir
    
    echo "Processing $Jname..."
    
    # Enter pulsar directory
    cd "$pulsar_dir" || { echo "Error: Cannot access $pulsar_dir"; cd ..; continue; }
    
    # Check and copy .par file
    if [ -f "$Jname.par" ]; then
        cp "$Jname.par" "$DEST_DIR/"
        echo "  Copied $Jname.par"
    else
        echo "  Warning: $Jname.par not found"
    fi
    
    # Check and copy .gwb.tim file, rename to .tim
    if [ -f "$Jname.gwb.tim" ]; then
        cp "$Jname.gwb.tim" "$DEST_DIR/$Jname.tim"
        echo "  Copied $Jname.gwb.tim to $DEST_DIR/$Jname.tim"
    else
        echo "  Warning: $Jname.gwb.tim not found"
    fi
    
    # Return to source directory
    cd ..
done

echo "All pulsars processed."