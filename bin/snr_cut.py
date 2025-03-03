#this code performs an snr cut for snr less than 10 for all tim files

import os

# Base directory
base_dir = "/fred/oz002/users/mbailes/astral/timing2025"

#SNR cut
snr_cutoff = 10

# Read pulsar list
pulsar_file = os.path.join(base_dir, "psr_list.txt")
with open(pulsar_file, "r") as f:
    pulsars = [line.strip() for line in f if line.strip()]  # Remove empty lines and spaces

# Directory to process
partim_dir = os.path.join(base_dir, "partim_snrcut")

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
            if "-snr" in line:
                try:
                    # Split the line and find the number after -snr
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "-snr" and i + 1 < len(parts):
                            snr_value = float(parts[i + 1])
                            if snr_value >= snr_cutoff:
                                filtered_lines.append(line)
                            break
                except (ValueError, IndexError):
                    # If there's any error parsing the number, keep the line
                    filtered_lines.append(line)
            else:
                # Keep lines that don't contain -snr
                filtered_lines.append(line)
        
        # Write the filtered lines back to the file
        with open(tim_file, 'w') as f:
            f.writelines(filtered_lines)
        print(f"Processed: {tim_file}")
    else:
        print(f"Warning: {tim_file} not found")

print("Processing complete!")