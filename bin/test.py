from enterprise.pulsar import Pulsar
import matplotlib.pyplot as plt
import sys
import glob
import os
import matplotlib

matplotlib.use('TkAgg')


# Find par and tim files
parfile = r'/fred/oz002/users/mbailes/astral/timing2025/GWB_search_2/J1101-6424.new.par'
timfile = r'/fred/oz002/users/mbailes/astral/timing2025/GWB_search_2/J1101-6424.tim'

# Ensure output directory exists
output_dir = "../Optstat/pngs/psr"

ephemeris = 'DE440'

pulsar = Pulsar(parfile, timfile, ephem=ephemeris)
print(f"Loaded {pulsar.name}")


toas_mjd = pulsar.toas / 86400.0
residuals = pulsar.residuals
errors = pulsar.toaerrs

plt.figure(figsize=(10, 6))
plt.errorbar(toas_mjd, residuals, yerr=errors, fmt='x', color='blue', label=pulsar.name)
plt.xlabel("MJD")
plt.ylabel("Residual (s)")
plt.title(f"TOA Residuals vs. MJD for {pulsar.name}")
plt.grid(True)
plt.legend()

filename = f"{output_dir}/{pulsar.name}.png"
plt.savefig(filename, dpi=300, bbox_inches='tight')
plt.show()
plt.close()
#print(f"Saved {pulsar.name}.png")
