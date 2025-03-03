import os
import glob
import re
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# Base directory
base_dir = "/fred/oz005/timing_processed"

# Get all pulsar directories
pulsar_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

# Initialize dictionaries to store results
timing_missing_underscores = {pulsar: [] for pulsar in pulsar_dirs}
timing_missing_corresponding = {pulsar: [] for pulsar in pulsar_dirs}
decimated_missing_underscores = {pulsar: [] for pulsar in pulsar_dirs}
decimated_missing_corresponding = {pulsar: [] for pulsar in pulsar_dirs}

# Regular expressions to match file patterns
# Pattern for files without proper underscores - e.g. .16ch1p14t.ar.tim
no_underscore_pattern = re.compile(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar')
# Pattern for corresponding files with underscores - e.g. .16ch_1p_max_14t.ar.tim
with_underscore_pattern = re.compile(r'.*_zap_chopped\.(\d+)ch_(\d+)p_(\w+)_(\d+)t\.ar')

print("Starting search for file patterns...")

# For each pulsar directory
for pulsar in pulsar_dirs:
    print(f"Processing {pulsar}...")
    pulsar_dir = os.path.join(base_dir, pulsar)
    
    # === TIMING DIRECTORIES ===
    # Find all timing directories (matching the pattern */[0-9]/)
    timing_dirs_pattern = os.path.join(pulsar_dir, "*/[0-9]/")
    timing_dirs = glob.glob(timing_dirs_pattern)
    
    for timing_dir in timing_dirs:
        # Now look inside timing/ subdirectory
        timing_subdir = os.path.join(timing_dir, "timing")
        
        if os.path.isdir(timing_subdir):
            # Get all subdirectories inside timing/
            sub_dirs = [d for d in os.listdir(timing_subdir) if os.path.isdir(os.path.join(timing_subdir, d))]
            
            for sub_dir in sub_dirs:
                full_sub_path = os.path.join(timing_subdir, sub_dir)
                
                # Get all .tim files
                tim_files = glob.glob(os.path.join(full_sub_path, "*.tim"))
                
                for tim_file in tim_files:
                    filename = os.path.basename(tim_file)
                    
                    # Check for files missing underscores
                    no_underscore_match = no_underscore_pattern.match(filename)
                    if no_underscore_match:
                        ch, p, t = no_underscore_match.groups()
                        # Store the date from the filename (YYYY-MM-DD-HH:MM:SS)
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                        if date_match:
                            date = date_match.group(1)
                            timing_missing_underscores[pulsar].append(date)
                            
                            # Check for corresponding files with underscores
                            corresponding_files = []
                            for modifier in ["max", "mode", "all"]:
                                corresponding_pattern = f"*{ch}ch_{p}p_{modifier}_{t}t.ar.tim"
                                corresponding_files.extend(glob.glob(os.path.join(full_sub_path, corresponding_pattern)))
                            
                            if not corresponding_files:
                                timing_missing_corresponding[pulsar].append(date)
    
    # === DECIMATED DIRECTORY ===
    decimated_dir = os.path.join(pulsar_dir, "decimated")
    
    if os.path.isdir(decimated_dir):
        # Get all .ar files (no need to go into subdirectories)
        ar_files = glob.glob(os.path.join(decimated_dir, "*.ar"))
        
        for ar_file in ar_files:
            filename = os.path.basename(ar_file)
            
            # Check for files missing underscores
            no_underscore_match = re.search(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar$', filename)
            if no_underscore_match:
                ch, p, t = no_underscore_match.groups()
                # Store the date from the filename
                date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                if date_match:
                    date = date_match.group(1)
                    decimated_missing_underscores[pulsar].append(date)
                    
                    # Check for corresponding files with underscores
                    corresponding_files = []
                    for modifier in ["max", "mode", "all"]:
                        corresponding_pattern = f"*{ch}ch_{p}p_{modifier}_{t}t.ar"
                        corresponding_files.extend(glob.glob(os.path.join(decimated_dir, corresponding_pattern)))
                    
                    if not corresponding_files:
                        decimated_missing_corresponding[pulsar].append(date)

# Remove duplicates in all lists
for pulsar in pulsar_dirs:
    timing_missing_underscores[pulsar] = list(set(timing_missing_underscores[pulsar]))
    timing_missing_corresponding[pulsar] = list(set(timing_missing_corresponding[pulsar]))
    decimated_missing_underscores[pulsar] = list(set(decimated_missing_underscores[pulsar]))
    decimated_missing_corresponding[pulsar] = list(set(decimated_missing_corresponding[pulsar]))

# Create DataFrames
timing_no_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_missing_underscores.items()]))
timing_no_corresponding_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_missing_corresponding.items()]))
decimated_no_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_missing_underscores.items()]))
decimated_no_corresponding_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_missing_corresponding.items()]))

# Save to CSV
timing_no_underscores_df.to_csv("timing_missing_underscores.csv", index=False)
timing_no_corresponding_df.to_csv("timing_missing_corresponding_files.csv", index=False)
decimated_no_underscores_df.to_csv("decimated_missing_underscores.csv", index=False)
decimated_no_corresponding_df.to_csv("decimated_missing_corresponding_files.csv", index=False)

print("Results saved to:")
print("- timing_missing_underscores.csv")
print("- timing_missing_corresponding_files.csv")
print("- decimated_missing_underscores.csv")
print("- decimated_missing_corresponding_files.csv")

# Print summary statistics
print("\nSummary:")
print(f"Timing files missing underscores: {timing_no_underscores_df.count().sum()}")
print(f"Timing files missing corresponding files: {timing_no_corresponding_df.count().sum()}")
print(f"Decimated files missing underscores: {decimated_no_underscores_df.count().sum()}")
print(f"Decimated files missing corresponding files: {decimated_no_corresponding_df.count().sum()}")