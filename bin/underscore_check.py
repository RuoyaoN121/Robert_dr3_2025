import os
import glob
import re
import pandas as pd
import warnings
import sys
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# Base directory
base_dir = "/fred/oz005/timing_processed"

# Get all pulsar directories
pulsar_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

# Initialize dictionaries for individual files
timing_missing_underscores = {pulsar: [] for pulsar in pulsar_dirs}
timing_missing_corresponding = {pulsar: [] for pulsar in pulsar_dirs}
decimated_missing_underscores = {pulsar: [] for pulsar in pulsar_dirs}
decimated_missing_corresponding = {pulsar: [] for pulsar in pulsar_dirs}

# Initialize dictionaries for directories
# Directories with non-underscored files with at least one file that has underscores
timing_dirs_with_underscores = {pulsar: [] for pulsar in pulsar_dirs}
# Directories with non-underscored files but no files with underscores
timing_dirs_only_nonunderscored = {pulsar: [] for pulsar in pulsar_dirs}
# Same for decimated directories
decimated_dirs_with_underscores = {pulsar: [] for pulsar in pulsar_dirs}
decimated_dirs_only_nonunderscored = {pulsar: [] for pulsar in pulsar_dirs}

# Regular expressions to match file patterns
# Pattern for files without proper underscores - e.g. .16ch1p14t.ar.tim
no_underscore_pattern = re.compile(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar')
# Pattern for corresponding files with underscores - e.g. .16ch_1p_max_14t.ar.tim
with_underscore_pattern = re.compile(r'.*_zap_chopped\.(\d+)ch_(\d+)p_(\w+)_(\d+)t\.ar')
# More general pattern to detect any file with underscores between ch, p, and t
any_underscore_pattern = re.compile(r'.*_zap_chopped\.\d+ch_\d+p_.*_\d+t\.ar')

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
                dir_path_relative = os.path.relpath(full_sub_path, base_dir)
                
                # Get all .tim files
                tim_files = glob.glob(os.path.join(full_sub_path, "*.tim"))
                
                # Skip if no files found
                if not tim_files:
                    continue
                
                # Track what we find in this directory
                has_nonunderscored_files = False
                has_underscored_files = False
                nonunderscored_files_info = []  # Store (filename, ch, p, t) for each nonunderscored file
                
                # First pass - check if directory has non-underscored files and underscored files
                for tim_file in tim_files:
                    filename = os.path.basename(tim_file)
                    
                    # Skip if not a zap_chopped file
                    if '_zap_chopped.' not in filename:
                        continue
                    
                    # Check for non-underscored files
                    no_underscore_match = no_underscore_pattern.match(filename)
                    if no_underscore_match:
                        has_nonunderscored_files = True
                        ch, p, t = no_underscore_match.groups()
                        nonunderscored_files_info.append((filename, ch, p, t))
                        
                        # Store the date from the filename
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                        if date_match:
                            date = date_match.group(1)
                            timing_missing_underscores[pulsar].append(date)
                    
                    # Check for files with underscores
                    if any_underscore_pattern.match(filename):
                        has_underscored_files = True
                
                # Only process directories with non-underscored files
                if has_nonunderscored_files:
                    # Check if directory also has files with underscores
                    if has_underscored_files:
                        timing_dirs_with_underscores[pulsar].append(dir_path_relative)
                    else:
                        timing_dirs_only_nonunderscored[pulsar].append(dir_path_relative)
                    
                    # Check for corresponding files
                    for filename, ch, p, t in nonunderscored_files_info:
                        has_matching = False
                        
                        # Look for corresponding files with underscores
                        for modifier in ["max", "mode", "all"]:
                            corresponding_pattern = f"*{ch}ch_{p}p_{modifier}_{t}t.ar.tim"
                            matching_files = glob.glob(os.path.join(full_sub_path, corresponding_pattern))
                            
                            if matching_files:
                                has_matching = True
                                break
                        
                        # If this file has no matching underscored version
                        if not has_matching:
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                            if date_match:
                                date = date_match.group(1)
                                timing_missing_corresponding[pulsar].append(date)
    
    # === DECIMATED DIRECTORIES ===
    # First check decimated directories inside timing dirs
    for timing_dir in timing_dirs:
        decimated_dir = os.path.join(timing_dir, "decimated")
        
        if os.path.isdir(decimated_dir):
            dir_path_relative = os.path.relpath(decimated_dir, base_dir)
            
            # Get all .ar files
            ar_files = glob.glob(os.path.join(decimated_dir, "*.ar"))
            
            # Skip if no files
            if not ar_files:
                continue
            
            # Track what we find in this directory
            has_nonunderscored_files = False
            has_underscored_files = False
            nonunderscored_files_info = []  # Store (filename, ch, p, t) for each nonunderscored file
            
            # First pass - check if directory has non-underscored files and underscored files
            for ar_file in ar_files:
                filename = os.path.basename(ar_file)
                
                # Skip if not a zap_chopped file
                if '_zap_chopped.' not in filename:
                    continue
                
                # Check for non-underscored files
                no_underscore_match = re.search(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar$', filename)
                if no_underscore_match:
                    has_nonunderscored_files = True
                    ch, p, t = no_underscore_match.groups()
                    nonunderscored_files_info.append((filename, ch, p, t))
                    
                    # Store the date from the filename
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                    if date_match:
                        date = date_match.group(1)
                        decimated_missing_underscores[pulsar].append(date)
                
                # Check for files with underscores
                if any_underscore_pattern.match(filename):
                    has_underscored_files = True
            
            # Only process directories with non-underscored files
            if has_nonunderscored_files:
                # Check if directory also has files with underscores
                if has_underscored_files:
                    decimated_dirs_with_underscores[pulsar].append(dir_path_relative)
                else:
                    decimated_dirs_only_nonunderscored[pulsar].append(dir_path_relative)
                
                # Check for corresponding files
                for filename, ch, p, t in nonunderscored_files_info:
                    has_matching = False
                    
                    # Look for corresponding files with underscores
                    for modifier in ["max", "mode", "all"]:
                        corresponding_pattern = f"*{ch}ch_{p}p_{modifier}_{t}t.ar"
                        matching_files = glob.glob(os.path.join(decimated_dir, corresponding_pattern))
                        
                        if matching_files:
                            has_matching = True
                            break
                    
                    # If this file has no matching underscored version
                    if not has_matching:
                        date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                        if date_match:
                            date = date_match.group(1)
                            decimated_missing_corresponding[pulsar].append(date)
    
    # Check the main decimated directory at pulsar level
    decimated_dir = os.path.join(pulsar_dir, "decimated")
    
    if os.path.isdir(decimated_dir):
        dir_path_relative = os.path.relpath(decimated_dir, base_dir)
        
        # Get all .ar files
        ar_files = glob.glob(os.path.join(decimated_dir, "*.ar"))
        
        # Skip if no files
        if not ar_files:
            continue
        
        # Track what we find in this directory
        has_nonunderscored_files = False
        has_underscored_files = False
        nonunderscored_files_info = []  # Store (filename, ch, p, t) for each nonunderscored file
        
        # First pass - check if directory has non-underscored files and underscored files
        for ar_file in ar_files:
            filename = os.path.basename(ar_file)
            
            # Skip if not a zap_chopped file
            if '_zap_chopped.' not in filename:
                continue
            
            # Check for non-underscored files
            no_underscore_match = re.search(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar$', filename)
            if no_underscore_match:
                has_nonunderscored_files = True
                ch, p, t = no_underscore_match.groups()
                nonunderscored_files_info.append((filename, ch, p, t))
                
                # Store the date from the filename
                date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                if date_match:
                    date = date_match.group(1)
                    decimated_missing_underscores[pulsar].append(date)
            
            # Check for files with underscores
            if any_underscore_pattern.match(filename):
                has_underscored_files = True
        
        # Only process directories with non-underscored files
        if has_nonunderscored_files:
            # Check if directory also has files with underscores
            if has_underscored_files:
                decimated_dirs_with_underscores[pulsar].append(dir_path_relative)
            else:
                decimated_dirs_only_nonunderscored[pulsar].append(dir_path_relative)
            
            # Check for corresponding files
            for filename, ch, p, t in nonunderscored_files_info:
                has_matching = False
                
                # Look for corresponding files with underscores
                for modifier in ["max", "mode", "all"]:
                    corresponding_pattern = f"*{ch}ch_{p}p_{modifier}_{t}t.ar"
                    matching_files = glob.glob(os.path.join(decimated_dir, corresponding_pattern))
                    
                    if matching_files:
                        has_matching = True
                        break
                
                # If this file has no matching underscored version
                if not has_matching:
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}-\d{2}:\d{2}:\d{2})', filename)
                    if date_match:
                        date = date_match.group(1)
                        decimated_missing_corresponding[pulsar].append(date)

# Remove duplicates in all lists
for pulsar in pulsar_dirs:
    timing_missing_underscores[pulsar] = list(set(timing_missing_underscores[pulsar]))
    timing_missing_corresponding[pulsar] = list(set(timing_missing_corresponding[pulsar]))
    decimated_missing_underscores[pulsar] = list(set(decimated_missing_underscores[pulsar]))
    decimated_missing_corresponding[pulsar] = list(set(decimated_missing_corresponding[pulsar]))
    
    timing_dirs_with_underscores[pulsar] = list(set(timing_dirs_with_underscores[pulsar]))
    timing_dirs_only_nonunderscored[pulsar] = list(set(timing_dirs_only_nonunderscored[pulsar]))
    
    decimated_dirs_with_underscores[pulsar] = list(set(decimated_dirs_with_underscores[pulsar]))
    decimated_dirs_only_nonunderscored[pulsar] = list(set(decimated_dirs_only_nonunderscored[pulsar]))

# Create DataFrames for individual files
timing_no_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_missing_underscores.items()]))
timing_no_corresponding_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_missing_corresponding.items()]))
decimated_no_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_missing_underscores.items()]))
decimated_no_corresponding_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_missing_corresponding.items()]))

# Create DataFrames for directories
timing_dirs_with_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_dirs_with_underscores.items()]))
timing_dirs_only_nonunderscored_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in timing_dirs_only_nonunderscored.items()]))
decimated_dirs_with_underscores_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_dirs_with_underscores.items()]))
decimated_dirs_only_nonunderscored_df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in decimated_dirs_only_nonunderscored.items()]))

# Save original files CSVs
timing_no_underscores_df.to_csv("timing_missing_underscores.csv", index=False)
timing_no_corresponding_df.to_csv("timing_missing_corresponding_files.csv", index=False)
decimated_no_underscores_df.to_csv("decimated_missing_underscores.csv", index=False)
decimated_no_corresponding_df.to_csv("decimated_missing_corresponding_files.csv", index=False)

# Save directory CSVs
timing_dirs_with_underscores_df.to_csv("timing_dirs_with_underscores.csv", index=False)
timing_dirs_only_nonunderscored_df.to_csv("timing_dirs_only_nonunderscored.csv", index=False)
decimated_dirs_with_underscores_df.to_csv("decimated_dirs_with_underscores.csv", index=False)
decimated_dirs_only_nonunderscored_df.to_csv("decimated_dirs_only_nonunderscored.csv", index=False)

# Count totals for summary
nonunderscored_file_count_timing = sum(len(v) for v in timing_missing_underscores.values())
nonunderscored_file_count_decimated = sum(len(v) for v in decimated_missing_underscores.values())
corresponding_missing_timing = sum(len(v) for v in timing_missing_corresponding.values())
corresponding_missing_decimated = sum(len(v) for v in decimated_missing_corresponding.values())

# Print information about saved files
print("Results saved to:")
print("File-level CSVs:")
print("- timing_missing_underscores.csv")
print("- timing_missing_corresponding_files.csv")
print("- decimated_missing_underscores.csv")
print("- decimated_missing_corresponding_files.csv")

print("\nDirectory-level CSVs:")
print("- timing_dirs_with_underscores.csv (dirs with non-underscored files that also have underscored files)")
print("- timing_dirs_only_nonunderscored.csv (dirs with non-underscored files but no underscored files)")
print("- decimated_dirs_with_underscores.csv (dirs with non-underscored files that also have underscored files)")
print("- decimated_dirs_only_nonunderscored.csv (dirs with non-underscored files but no underscored files)")

# Print summary statistics
print("\nSummary Statistics:")
print("\nFile Counts:")
print(f"Timing files missing underscores: {timing_no_underscores_df.count().sum()} (from {nonunderscored_file_count_timing} dates)")
print(f"Timing files missing corresponding files: {timing_no_corresponding_df.count().sum()} (from {corresponding_missing_timing} dates)")
print(f"Decimated files missing underscores: {decimated_no_underscores_df.count().sum()} (from {nonunderscored_file_count_decimated} dates)")
print(f"Decimated files missing corresponding files: {decimated_no_corresponding_df.count().sum()} (from {corresponding_missing_decimated} dates)")

print("\nDirectory Counts:")
print(f"Timing directories with non-underscored files: {timing_dirs_with_underscores_df.count().sum() + timing_dirs_only_nonunderscored_df.count().sum()}")
print(f"   - Of which, also have underscored files: {timing_dirs_with_underscores_df.count().sum()}")
print(f"   - Of which, have only non-underscored files: {timing_dirs_only_nonunderscored_df.count().sum()}")

print(f"Decimated directories with non-underscored files: {decimated_dirs_with_underscores_df.count().sum() + decimated_dirs_only_nonunderscored_df.count().sum()}")
print(f"   - Of which, also have underscored files: {decimated_dirs_with_underscores_df.count().sum()}")
print(f"   - Of which, have only non-underscored files: {decimated_dirs_only_nonunderscored_df.count().sum()}")