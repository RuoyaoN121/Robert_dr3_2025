import os
import re

class TimFileProcessor:
    def __init__(self, apply_epoch_cut=True, apply_snr_cut=True, apply_bw_cut=False, 
                 apply_length_cut=False, epochs=None, snr_cutoff=10, bw_cutoff=20, 
                 length_cutoff=128):
        self.apply_epoch_cut = apply_epoch_cut
        self.apply_snr_cut = apply_snr_cut
        self.apply_bw_cut = apply_bw_cut
        self.apply_length_cut = apply_length_cut
        self.epochs = epochs or []
        self.epoch_pattern = re.compile("|".join(map(re.escape, self.epochs))) if self.epochs else None
        self.snr_cutoff = snr_cutoff
        self.bw_cutoff = bw_cutoff
        self.length_cutoff = length_cutoff

    def line_passes_filters(self, line):
        # Epoch filter
        if self.apply_epoch_cut and self.epoch_pattern and self.epoch_pattern.search(line):
            return False

        # SNR filter
        if self.apply_snr_cut and "-snr" in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "-snr" and i + 1 < len(parts):
                    try:
                        if float(parts[i+1]) < self.snr_cutoff:
                            return False
                    except ValueError:
                        pass

        # BW filter
        if self.apply_bw_cut and "-bw" in line:
            parts = line.split()
            for i, part in enumerate (parts):
                if part == "-bw" and i + 1 < len(parts):
                    try:
                        if float(parts[i+1]) < self.bw_cutoff:
                            return False
                    except ValueError:
                        pass
                        
        # Length filter
        if self.apply_length_cut and "-tobs" in line:
            parts = line.split()
            for i, part in enumerate (parts):
                if part == "-length" and i + 1 < len(parts):
                    try:
                        if float(parts[i+1]) < self.length_cutoff:
                            return False
                    except ValueError:
                        pass

        return True

    def process_tim_file(self, tim_path, psr_dest_dir, psr_dest_dir_deleted):
        if not os.path.exists(tim_path):
            print(f"Warning: {tim_path} not found")
            return

        with open(tim_path, 'r') as f_in:
            lines = f_in.readlines()

        filtered = [ln for ln in lines if self.line_passes_filters(ln)]
        deleted = [ln for ln in lines if not self.line_passes_filters(ln)]

        os.makedirs(psr_dest_dir, exist_ok=True)
        os.makedirs(psr_dest_dir_deleted, exist_ok=True)

        tim_out = os.path.join(psr_dest_dir, f"{psrname}.tim")
        tim_out_deleted = os.path.join(psr_dest_dir_deleted, f"{psrname}.tim")

        with open(tim_out, 'w+') as f_out1:
            # Add the EMAX 10 line at the beginning of the file
            f_out1.write("EMAX 10\n")
            f_out1.writelines(filtered)
            print(f"Processed: {tim_path}")

        with open(tim_out_deleted, 'w+') as f_out2:
            f_out2.writelines(deleted)
            print(f"Processed (deleted): {tim_path}")

# Main execution
if __name__ == "__main__":
    base_dir = "/fred/oz002/users/mbailes/astral/timing2025"
    pulsar_file = os.path.join(base_dir, "psr_list.txt")
    partim_dir = os.path.join(base_dir, "partim_v3")
    out_dir_filtered = os.path.join(base_dir, "partim_obs")
    out_dir_deleted = os.path.join(base_dir, "partim_deleted")
    epochs_to_remove = ["2021-06-13", "2021-06-21", "2020-01-21", "2021-06-22"]

    os.makedirs(out_dir_filtered, exist_ok=True)
    os.makedirs(out_dir_deleted, exist_ok=True)

    processor = TimFileProcessor(
        apply_epoch_cut=True,
        apply_snr_cut=True,
        apply_bw_cut=True,  # Set to True if needed
        apply_length_cut=True,  # Enable the length filter
        epochs=epochs_to_remove,
        snr_cutoff=10,
        bw_cutoff=20,
        length_cutoff=128  # Set the minimum length value
    )

    with open(pulsar_file, "r") as f:
        pulsars = [line.strip() for line in f if line.strip()]

    for psrname in pulsars:
        tim_file_path = os.path.join(partim_dir, psrname, f"{psrname}.tim")
        psr_dest_dir = os.path.join(out_dir_filtered, psrname)
        psr_dest_dir_deleted = os.path.join(out_dir_deleted, psrname)
        processor.process_tim_file(tim_file_path, psr_dest_dir, psr_dest_dir_deleted)

    print("Processing complete!")