import os
import subprocess
import glob
import sys

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
    pulsar_dir = os.path.join(base_dir, psrname)
    os.makedirs(pulsar_dir, exist_ok=True)
    print(f"Processing {psrname}...")

    pattern_mode = f"/fred/oz005/timing_processed/{psrname}/2*/?/timing/PTA/J*_chopped.32ch_1p_mode*ar.tim"
    mode_files = sorted(glob.glob(pattern_mode))  # sorted for consistent output order
    print(f"Found {len(mode_files)} mode files for {psrname}")

    # Gather all files to concatenate
    selected_files = []
    for f in mode_files:
        if os.path.getsize(f) > 1000:
            selected_files.append(f)
        else:
            # Try corresponding max file
            print(f"Warning: {f} is too small, trying corresponding max file...")
            max_file = f.replace("_mode", "_max")
            if os.path.exists(max_file) and os.path.getsize(max_file) > 1000:
                selected_files.append(max_file)
            else:
                warining = f"Warning: {max_file} is too small or does not exist"
                failed_obs.append(f'{max_file}\\n')

    print(f"Selected {len(selected_files)} files for {psrname}")

    output_tim = os.path.join(pulsar_dir, f"{psrname}.tim")
    if selected_files:
        try:
            cat_cmd = "cat " + " ".join(selected_files) + f" > {output_tim}"
            subprocess.run(cat_cmd, shell=True, check=True)
            print(f"Created {psrname}.tim with {len(selected_files)} file(s).")
        except subprocess.CalledProcessError as e:
            print(f"Error creating {psrname}.tim: {e}")
    else:
        print(f"No suitable tim files found for {psrname}")


    # Extract par files
    par_filename = f"{psrname}.par"
    src_par_path = os.path.join(par_source_dir, par_filename)
    dest_par_path = os.path.join(pulsar_dir, par_filename)
    
    if os.path.exists(dest_par_path):
        print(f"Skipping {psrname}.par - file already exists")
    else:
        if os.path.exists(src_par_path):
            try:
                with open(src_par_path, "r") as src_file, open(dest_par_path, "w") as dest_file:
                    dest_file.write(src_file.read())
                print(f"Created {psrname}.par")
            except IOError as e:
                print(f"Error copying {psrname}.par: {e}")
        else:
            print(f"Warning: Source par file for {psrname} not found at {src_par_path}")

print(failed_obs)
print("Processing complete!")