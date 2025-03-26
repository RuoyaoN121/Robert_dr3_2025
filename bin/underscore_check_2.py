import os
import glob
import re
import pandas as pd
import warnings
warnings.simplefilter(action='ignore', category=pd.errors.PerformanceWarning)

# Base directory to start the search
BASE_DIR = "/fred/oz005/timing_processed/"

# Initialize dictionaries to store results by pulsar
missing_underscore_dict = {}
multiple_correct_dict = {}

# Regular expressions for pattern matching
# Pre-compile patterns for better performance
no_underscore_pattern = re.compile(r'.*_zap_chopped\.(\d+)ch(\d+)p(\d+)t\.ar')
any_underscore_pattern = re.compile(r'.*_zap_chopped\.\d+ch_\d+p_.*_\d+t\.ar')

def main():
    # Use glob to directly find all timing subdirectories - much faster directory traversal
    # This gives us all subdirectories in timing folders with a single filesystem operation
    timing_dirs = glob.glob(os.path.join(BASE_DIR, "*/20*/?/timing/*/"))
    
    # Similarly, find all decimated directories in one go
    decimated_dirs = glob.glob(os.path.join(BASE_DIR, "*/20*/?/decimated/"))
    
    print(f"Found {len(timing_dirs)} timing directories and {len(decimated_dirs)} decimated directories")
    
    # Process timing directories
    for directory in timing_dirs:
        process_directory(directory, "timing")
        
    # Process decimated directories  
    for directory in decimated_dirs:
        process_directory(directory, "decimated")
    
    # Convert dictionaries to dataframes
    missing_underscore_df = pd.DataFrame(dict([(k, pd.Series(list(v))) for k, v in missing_underscore_dict.items() if v]))
    multiple_correct_df = pd.DataFrame(dict([(k, pd.Series(list(v))) for k, v in multiple_correct_dict.items() if v]))
    
    # Save results to CSV files
    missing_underscore_df.to_csv("missing_underscores.csv")
    multiple_correct_df.to_csv("multiple_correct_files.csv")
    
    print("\nSummary:")
    print(f"Files without underscores found: {len(missing_underscore_dict)} pulsars")
    print(f"Directories with more than 3 correct files found: {len(multiple_correct_dict)} pulsars")
    print("Results saved to missing_underscores.csv and multiple_correct_files.csv")

def process_directory(directory, dir_type):
    print(f"Processing {dir_type} directory: {directory}")
    # Extract pulsar name from path
    path_parts = directory.split(os.sep)
    pulsar = None
    
    # Find the pulsar name in the path
    for part in path_parts:
        if part.startswith("J") and ("+" in part or "-" in part):
            pulsar = part
            break
    
    if not pulsar:
        return  # Skip if we couldn't find pulsar name
    
    # Initialize sets for this pulsar if needed (using sets for faster duplicate removal)
    if pulsar not in missing_underscore_dict:
        missing_underscore_dict[pulsar] = set()
    if pulsar not in multiple_correct_dict:
        multiple_correct_dict[pulsar] = set()
    
    # Get all files in the directory
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    except (FileNotFoundError, PermissionError):
        return
    
    # Quick filter for relevant files
    zap_chopped_files = [f for f in files if '_zap_chopped.' in f]
    
    # Skip if no relevant files
    if not zap_chopped_files:
        return
    
    # Lists to track files with and without underscores
    missing_underscore_files = []
    correct_underscore_files = []
    
    # Check each file
    for file in zap_chopped_files:
        # Check if file has "chopped." without underscore before extension
        if no_underscore_pattern.match(file):
            missing_underscore_files.append(file)
        # Check if file has "chopped_" with underscore before extension
        elif any_underscore_pattern.match(file):
            correct_underscore_files.append(file)
    
    # Record files without underscores
    if missing_underscore_files:
        missing_underscore_dict[pulsar].update(missing_underscore_files)
    
    # Record if multiple correct files exist
    if len(correct_underscore_files) > 3:
        multiple_correct_dict[pulsar].update(correct_underscore_files)

if __name__ == "__main__":
    main()
