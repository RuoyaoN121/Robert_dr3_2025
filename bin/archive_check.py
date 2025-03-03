import os
import pandas as pd
import glob

# Base directory
base_dir = "/fred/oz005/timing_processed"

# Get all pulsar directories
pulsar_dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]

# Initialize a dictionary to store results
results = {pulsar: [] for pulsar in pulsar_dirs}

# For each pulsar directory
for pulsar in pulsar_dirs:
    # Find all timing directories (matching the pattern ?/ where ? is an integer)
    print(f"Checking {pulsar}...")
    timing_dirs_pattern = os.path.join(base_dir, pulsar, "*/[0-9]/")
    timing_dirs = glob.glob(timing_dirs_pattern)
    
    # Check each timing directory for the expected file
    for timing_dir in timing_dirs:
        # Extract the timing value from the path
        path_parts = timing_dir.rstrip('/').split('/')
        time = path_parts[-2]
        
        # Check if the expected file exists
        expected_file = f"{pulsar}_{time}_zap.ar"
        expected_file_path = os.path.join(timing_dir, expected_file)
        
        if not os.path.exists(expected_file_path):
            # If file doesn't exist, add the timing directory to results
            # Store just the relevant part of the path
            dir_info = f"{time}/{path_parts[-1]}"
            results[pulsar].append(dir_info)

# Create DataFrame
df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in results.items()]))

print(df)

# Save to CSV
csv_file = "missing_zap_files.csv"
df.to_csv(csv_file, index=False)
print(f"Results saved to {csv_file}")