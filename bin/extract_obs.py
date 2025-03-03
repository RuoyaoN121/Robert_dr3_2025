import os
import subprocess
import glob
import sys
import shutil

# Define base directory
base_dir = "/fred/oz002/users/mbailes/astral/timing2025"

# Read pulsar names from psr_list.txt
pulsar_file = os.path.join(base_dir, "psr_list.txt")
try:
    with open(pulsar_file, "r") as f:
        psrnames = [line.strip() for line in f if line.strip()]  # Remove empty lines and spaces
except FileNotFoundError:
    print(f"Error: {pulsar_file} not found!")
    exit(1)

# Source directory for par files
par_source_dir = "/fred/oz002/users/mmiles/MPTA_GW/partim_frank/pp_8"

failed_obs = []
# Process each pulsar
for psrname in psrnames:
    pulsar_dir = os.path.join(base_dir, 'partim_obs', psrname)
    os.makedirs(pulsar_dir, exist_ok=True)
    print(f"Processing {psrname}...")

    pattern_mode = f"/fred/oz005/timing_processed/{psrname}/2*/?/timing/PTA/J*_chopped.32ch_1p_mode*ar.tim"
    mode_files = sorted(glob.glob(pattern_mode))  # sorted for consistent output order
    print(f"Found {len(mode_files)} mode files for {psrname}")

    # Process each file
    for f in mode_files:
        if os.path.getsize(f) > 1000:
            selected_file = f
        else:
            # Try corresponding max file
            print(f"Warning: {f} is too small, trying corresponding max file...")
            max_file = f.replace("_mode", "_max")
            if os.path.exists(max_file) and os.path.getsize(max_file) > 1000:
                selected_file = max_file
            else:
                warning = f"Warning: {max_file} is too small or does not exist"
                failed_obs.append(f'{max_file}\\n')
                continue

        # Extract the timestamp from the filename
        filename = os.path.basename(selected_file)
        timestamp = filename.split('_')[1]
        new_filename = f"{timestamp}.tim"
        new_filepath = os.path.join(pulsar_dir, new_filename)

        # Copy the file to the new directory with the new name
        try:
            shutil.copy(selected_file, new_filepath)
            print(f"Copied {selected_file} to {new_filepath}")
        except IOError as e:
            print(f"Error copying {selected_file} to {new_filepath}: {e}")

print("Processing complete!")