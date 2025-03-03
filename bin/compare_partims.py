import re
from datetime import datetime
import os

def extract_dates(filename):
    dates = set()
    try:
        with open(filename, 'r') as f:
            for line in f:
                # Changed to strip and check for J
                if line.strip().startswith('J'):
                    match = re.search(r'\s*J\d+[+-]\d+_(\d{4}-\d{2}-\d{2})-\d{2}:\d{2}:\d{2}', line)
                    if match:
                        dates.add(match.group(1))
                    else:
                        print(f"No match found for line: {line.strip()[:50]}...")  # Debug line improved
    except FileNotFoundError:
        print(f"Warning: File not found - {filename}")
        return set()
    return dates

def compare_timing_files(file1, file2, pulsar_name):
    # Extract dates from both files
    dates1 = extract_dates(file1)
    dates2 = extract_dates(file2)

    # print(f"\nDates in file1: {sorted(dates1)}")  # Debug line
    # print(f"Dates in file2: {sorted(dates2)}")  # Debug line
    
    if not dates1 and not dates2:
        print(f"\nSkipping {pulsar_name} - neither timing file exists")
        return
    
    # Find unique dates in each file
    unique_to_file1 = dates1 - dates2
    unique_to_file2 = dates2 - dates1
    
    if not unique_to_file1 and not unique_to_file2:
        print(f"\n{pulsar_name}: No differences found")
        return
    
    # Output results
    print(f"\n=== Results for {pulsar_name} ===")
    print(f"Dates unique to snrbwepoch version:")
    for date in sorted(unique_to_file1):
        print(f"  {date}")
        
    print(f"\nDates unique to matt version:")
    for date in sorted(unique_to_file2):
        print(f"  {date}")

def read_pulsar_list(filename="psr_list.txt"):
    try:
        with open(filename, 'r') as f:
            # Read lines and remove whitespace, empty lines
            pulsars = [line.strip() for line in f if line.strip()]

            # pulsars = ['J2322+2057']  # Debug line
        return pulsars
    except FileNotFoundError:
        print(f"Error: {filename} not found in current directory")
        return []

def main():
    # Read pulsar list
    pulsars = read_pulsar_list()
    if not pulsars:
        return
    
    print(f"Found {len(pulsars)} pulsars to process")
    
    # Process each pulsar
    for pulsar in pulsars:
        # Define paths for both versions
        snrbw_path = f"/fred/oz002/users/mbailes/astral/timing2025/partim_snrbwepoch/{pulsar}/{pulsar}.tim"
        matt_path = f"/fred/oz002/users/mbailes/astral/timing2025/partim_matt/{pulsar}.tim"
        
        # Compare the timing files
        compare_timing_files(snrbw_path, matt_path, pulsar)

if __name__ == "__main__":
    main()