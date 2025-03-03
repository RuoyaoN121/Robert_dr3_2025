import os
import subprocess

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

# Process each pulsar
for psrname in psrnames:
    # Create directory for pulsar if it doesn't exist
    pulsar_dir = os.path.join(base_dir, psrname)
    os.makedirs(pulsar_dir, exist_ok=True)
    print(f"Processing {psrname}...")

    # Extract tim files using cat command
    source_pattern = f"/fred/oz005/timing_processed/{psrname}/2*/?/timing/PTA/J*_chopped.32ch_1p_mode*ar.tim"
    output_tim = os.path.join(pulsar_dir, f"{psrname}.tim")
    
    if os.path.exists(output_tim):
        print(f"Skipping {psrname}.tim - file already exists")
    else:
        try:
            # Using subprocess to run the cat command and redirect output
            cmd = f"cat {source_pattern} > {output_tim}"
            subprocess.run(cmd, shell=True, check=True)
            print(f"Created {psrname}.tim")
        except subprocess.CalledProcessError as e:
            print(f"Error creating {psrname}.tim: {e}")

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

print("Processing complete!")