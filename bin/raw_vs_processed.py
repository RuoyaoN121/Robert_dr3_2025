import os
import pandas as pd

# Define base directory
base_dir = "/fred/oz002/users/mbailes/astral/timing2025"

# Define the two directories to compare
dir1 = r"/fred/oz005/timing/"
dir2 = r"/fred/oz005/timing_processed/"

# Function to list subdirectories
def list_subdirectories(directory):
    return [d for d in os.listdir(directory) if os.path.isdir(os.path.join(directory, d))]

# Get all subdirectories from both directories
try:
    subdirs1 = set(list_subdirectories(dir1))
    subdirs2 = set(list_subdirectories(dir2))
except FileNotFoundError as e:
    print(f"Error accessing directories: {e}")
    exit(1)

print(f"Total subdirectories in {dir1}: {len(subdirs1)}")
print(f"Total subdirectories in {dir2}: {len(subdirs2)}")

# Find common subdirectories between the two main directories
common_subdirs = subdirs1.intersection(subdirs2)
print(f"Number of common subdirectories: {len(common_subdirs)}")
print(f"Common subdirectories: {len(sorted(common_subdirs))}")

differences = {}
i = 0
# Compare contents of each common subdirectory
for subdir in sorted(common_subdirs):
    i+=1
    psr_dir1 = os.path.join(dir1, subdir)
    psr_dir2 = os.path.join(dir2, subdir)
    
    subdirs_level1 = set(list_subdirectories(psr_dir1))
    subdirs_level2 = set(list_subdirectories(psr_dir2))
    #print(f"length of subdirs in {subdir} (raw): {len(subdirs_level1)}")
    #print(f"length of subdirs in {subdir} (processed): {len(subdirs_level2)}")

    only_in_dir1 = subdirs_level1 - subdirs_level2
    
    if only_in_dir1:
        #print(f"Differences found for directory {subdir}:")
        #print(f"  Only in {psr_dir1}: {sorted(only_in_dir1)}")
        differences[subdir] = tuple(sorted(only_in_dir1))

print(f"Processed {i} common subdirectories")

# Write differences to a CSV file
if differences:
    # Ensure all values in the dictionary have the same length
    max_length = max(len(v) for v in differences.values())
    for k, v in differences.items():
        differences[k] = list(v) + [''] * (max_length - len(v))

    df = pd.DataFrame.from_dict(differences, orient='index').transpose()
    csv_file = os.path.join(base_dir, "differences_2.csv")
    df.to_csv(csv_file)
    print(f"Differences written to {csv_file}")
else:
    print("No differences found.")

