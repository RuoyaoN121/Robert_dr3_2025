
# notes: for the input directorys, don't add a / at the end of the directory name
# e.g. python compare_partims2.py partim1 partim2
import os
import sys
import pandas as pd
import re

base_dir = "/fred/oz002/users/mbailes/astral/timing2025"
pulsar_list = os.path.join(base_dir, "psr_list.txt")

class compare:
    def __init__(self, dir1, dir2, pulsars):
        self.dir1 = dir1
        self.dir2 = dir2
        self.dir1_path = os.path.join(base_dir, dir1)
        self.dir2_path = os.path.join(base_dir, dir2)
        self.pulsars = pulsars

    def extract_dates(self, tim_file):
        dates = set()
        if not os.path.isfile(tim_file):
            return dates
        with open(tim_file, "r") as f:
            for line in f:
                # Adjust pattern according to your date format
                match = re.match(r"\s*J\d+[+-]\d+_(\d{4}-\d{2}-\d{2})-\d{2}:\d{2}:\d{2}", line)
                if match:
                    dates.add(match.group(1))
        return dates

    def find_sim(self):
        # Collect same
        sim = {}
        for psr in self.pulsars:
            tim1 = os.path.join(dir1_path, psr, f"{psr}.tim")  # could change code to make this more elegant, but won't make this change now
            tim2 = os.path.join(dir2_path, psr, f"{psr}.tim")

            print(f'{psr}: {tim1}') # debug
            print(f'{psr}: {tim2}') # debug

            dates1 = self.extract_dates(tim1)
            #print(f'{psr}: {len(dates1)} dates in {dir1}') # debug
            dates2 = self.extract_dates(tim2)
            #print(f'{psr}: {len(dates2)} dates in {dir2}') # debug
            same_dates = sorted(dates1 & dates2)
            #print(f'{psr}: {same_dates} same dates') # debug
            #print(f'{psr}: {len(same_dates)} same dates') # debug
            #sys.exit(1)
            if same_dates:
                sim[psr] = same_dates

        # Create DataFrame
        df_sim = pd.DataFrame(dict([(k, pd.Series(v, dtype=str)) for k, v in sim.items()]))

        # Save to CSV
        output_dir = os.path.join(base_dir, "compare_epochs")
        os.makedirs(output_dir, exist_ok=True)
        df_sim.to_csv(os.path.join(output_dir, f"{self.dir1}_vs_{self.dir2}_same.csv"), index=False)
        

    def find_diff(self):
        # Collect differences
        dir1_unique = {}
        dir2_unique = {}
        for psr in self.pulsars:
            tim1 = os.path.join(self.dir1_path, psr, f"{psr}.tim")
            tim2 = os.path.join(self.dir2_path, f"{psr}.tim") # not in subfolders for matt's data

            dates1 = self.extract_dates(tim1)
            dates2 = self.extract_dates(tim2)
            print(f'\n{psr}: {len(dates1)} dates in {dir1}, {len(dates2)} dates in {dir2}')
            # print(f'\n{psr}: {sorted(dates1)} dates in {dir1}, {sorted(dates2)} dates in {dir2}')


            diff1 = sorted(dates1 - dates2)
            diff2 = sorted(dates2 - dates1)

            if diff1:
                dir1_unique[psr] = diff1
            else:
                dir1_unique[psr] = []
            if diff2:
                dir2_unique[psr] = diff2
            else:
                dir2_unique[psr] = []

        # Create DataFrames
        df1 = pd.DataFrame(dict([(k, pd.Series(v, dtype=str)) for k, v in dir1_unique.items()]))
        df2 = pd.DataFrame(dict([(k, pd.Series(v, dtype=str)) for k, v in dir2_unique.items()]))

        # Save to CSV
        output_dir = os.path.join(base_dir, "compare_epochs")
        os.makedirs(output_dir, exist_ok=True)
        df1.to_csv(os.path.join(output_dir, fr"{dir1}_vs_{dir2}_unique.csv"), index=False)
        df2.to_csv(os.path.join(output_dir, fr"{dir2}_vs_{dir1}_unique.csv"), index=False)

        #df1.to_csv(os.path.join(output_dir, fr"test1.csv"), index=False)
        #df2.to_csv(os.path.join(output_dir, fr"test2.csv"), index=False)

if __name__ == "__main__":
    if len(sys.argv) < 4:
            print("Usage: python compare_partims2.py <dir1> <dir2> <sim/diff>")
            sys.exit(1)

    dir1, dir2 = sys.argv[1], sys.argv[2]
    dir1_path = os.path.join(base_dir, dir1)
    dir2_path = os.path.join(base_dir, dir2)
    sim_diff = sys.argv[3].lower()

    with open(pulsar_list, "r") as f:
        pulsars = [line.strip() for line in f if line.strip()]
        # pulsars = ["J1713+0747"]  # Debug line

    process = compare(dir1, dir2, pulsars)

    # Read all pulsar names

    
    if sim_diff == "diff":
        process.find_diff()
        print("running for differences")
    elif sim_diff == "sim":
        process.find_sim()
        print("running for similarities")
    else:
        print("Usage: python compare_partims2.py <dir1> <dir2> <sim/diff>")
        sys.exit(1)