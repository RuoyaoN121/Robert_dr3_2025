import os
import argparse
import shutil



def copy_par_files(base_dir):
    pulsar_list = os.path.join(base_dir, "psr_list.txt")

    with open(pulsar_list, "r") as f:
        pulsars = [line.strip() for line in f if line.strip()]

    for pulsar in pulsars:
        src = os.path.join(base_dir, "partim", pulsar, f"{pulsar}.par")
        dst = os.path.join(base_dir, "partim_robert", pulsar, f"{pulsar}.par")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f"Copied {src} to {dst}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy par files from partim to partim_robert")
    parser.add_argument("base_dir", type=str, help="Base directory containing the pulsar data")
    base_dir = "/fred/oz002/users/mbailes/astral/timing2025"

    copy_par_files(base_dir)