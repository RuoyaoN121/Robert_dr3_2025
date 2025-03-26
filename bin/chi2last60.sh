#!/bin/bash

echo "Code to calculate reduced chi^2 for every observation"
echo "in the $TIMING/partim_obs_2 directory"
echo "Fit for DM as well"

# export TEMPO2_CLOCK_DIR=/fred/oz002/users/mbailes/astral/tempo2/clock/

# Go to source of truth and list pulsar directories
cd "$TIMING/partim_obs_2" || exit
pulsars=($(ls | grep J))
npsr=${#pulsars[@]}

# Function to process a given range of pulsars in reverse order
process_pulsars() {
  start=$1
  end=$2
  subset=($(printf "%s\n" "${pulsars[@]: -$start:$((start - end + 1))}" | tac))
  
  for pulsar in "${subset[@]}"; do
    cd "$pulsar" || continue
    for obs in $(awk -F_ '{ print $2 }' "${pulsar}.tim" | sort -u); do
      echo "Working on pulsar $pulsar observation $obs"
      nlines=$(wc -l < "$obs.tim")
      if [ "$nlines" -gt 2 ]; then
        tempo2 -npsr 1 -ntoa 1000 -nofit -fit DM -outpar "${obs}.auto.par" -f "${pulsar}.par" "${obs}.tim" > /dev/null
      fi
    done
    echo "UTC,CHI2R,NPOINTS" > "${pulsar}.auto.CHI2R.csv"
    grep CHI2R 2*.auto.par | sed -e "s/.auto.par:CHI2R//" | awk '{ print $1","$2","$3 }' >> "${pulsar}.auto.CHI2R.csv"
    cd ..
  done
}

# Process different ranges of pulsars in reverse order
process_pulsars 60 51