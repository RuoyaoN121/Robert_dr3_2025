import os
import shutil
import subprocess
import sys
import time

pulsar_file = r"/fred/oz002/users/mbailes/astral/timing2025/psr_list.txt"
with open(pulsar_file, "r") as f:
    pulsars = [line.strip() for line in f if line.strip()]  # Remove empty lines and spaces

failed_pulsars = []

# pulsars = ['J2322-2650']

# Base directories
timing_dir = r"/fred/oz002/users/mbailes/astral/timing2025"
par_source_dir = r"/fred/oz002/users/mmiles/MPTA_GW/partim_frank/pp_8"

for psrname in pulsars:
    # Create subdirectory for the pulsar
    pulsar_dir = os.path.join(timing_dir, psrname)
    try:
        os.makedirs(pulsar_dir, exist_ok=True)
    except:
        print(f'{psrname} directory already exists')

    # Extract the tim file using the command
    tim_filename = f"toa_{psrname}_PTA_mode_nsub_nchan32_npol1.tim"
    cmd = [
        "psrdb", "toa", "download", "--nsub_type", "mode", psrname,
        "--project", "PTA", "--nchan", "32", "--npol", "1"
    ]
    
    '''subprocess.run(cmd, check=True)  # Run the command'''

    try:
        # Run the command and capture output
        result = subprocess.run(
            cmd,
            check=True,           # Raise an exception if the command fails
            capture_output=True,  # Capture stdout and stderr
            text=True             # Return output as strings, not bytes
        )
        print(f"Successfully ran psrdb for {psrname}")
    except subprocess.CalledProcessError as e:
        # Handle the error and display detailed output
        print(f"Error running psrdb for {psrname}:")
        print(f"Exit code: {e.returncode}")
        print(f"Standard output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        failed_pulsars.append(psrname)
        continue  # Skip to the next pulsar if this one fails

    time.sleep(10)
    print('finished sleep')

    # Rename and move the .tim file
    if os.path.exists(tim_filename):
        new_tim_path = os.path.join(pulsar_dir, f"{psrname}.tim")
        shutil.move(tim_filename, new_tim_path)
        print(f"created {psrname} tim file")
    else:
        print(f"created {psrname} tim file already exists")
    
    # Copy contents of .par file and create a new one in the target directory
    par_filename = f"{psrname}.par"
    src_par_path = os.path.join(par_source_dir, par_filename)
    dest_par_path = os.path.join(pulsar_dir, par_filename)
    
    if os.path.exists(src_par_path):
        with open(src_par_path, "r") as src_file, open(dest_par_path, "w") as dest_file:
            dest_file.write(src_file.read())
        print(f"created {psrname} par file")
    else:
        print(f"created {psrname} par file already exists")

print("created all")

print(f"list of failed pulsars: {failed_pulsars}")
