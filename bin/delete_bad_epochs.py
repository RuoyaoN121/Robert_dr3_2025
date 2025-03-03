import os
import re

# Base directory
base_dir = "/fred/oz002/users/mbailes/astral/timing2025"

# Read pulsar list
pulsar_file = os.path.join(base_dir, "psr_list.txt")
with open(pulsar_file, "r") as f:
    pulsars = [line.strip() for line in f if line.strip()]  # Remove empty lines and spaces

# Directory to process
partim_dir = os.path.join(base_dir, "partim_snrbwepoch")

epochs = ["2021-06-13", "2021-06-21", "2020-01-21", "2021-06-22"]
epoch_pattern = re.compile("|".join(map(re.escape, epochs)))

# Process each pulsar
for psrname in pulsars:
    # Construct path to pulsar directory and .tim file
    psr_dir = os.path.join(partim_dir, psrname)
    tim_file = os.path.join(psr_dir, f"{psrname}.tim")
    
    # Check if the .tim file exists
    if os.path.exists(tim_file):
        # Read all lines from the .tim file
        with open(tim_file, 'r') as f:
            lines = f.readlines()
        
        # Process lines: keep only lines where -snr value is >= 10 or doesn't contain -snr
        filtered_lines = []
        for line in lines:
        # Check if any epoch is in the line
            if not epoch_pattern.search(line):
                filtered_lines.append(line)
            else:
                print(f"deleted bad epoch for {psrname}")
        
        # Write the filtered lines back to the file
        with open(tim_file, 'w') as f:
            f.writelines(filtered_lines)
            print(f'written {psrname}.tim')
    else:
        print(f"Warning: {tim_file} not found")

print("Processing complete!")