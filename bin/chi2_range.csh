#!/bin/csh

# Usage: ./script_name.csh <start_index> <end_index>
if ( $#argv < 2 ) then
  echo "Usage: $0 <start_index> <end_index>"
  exit 1
endif

set start = $argv[1]
set end = $argv[2]

echo "Code to calculate reduced chi^2 for observations in range $start to $end"
echo "Working in the $TIMING/partim_obs_2 directory"
echo "Fitting for DM as well"

cd $TIMING/partim_obs_2

# Get a sorted list of pulsars that match "J"
set pulsars = (`ls | grep ^J | sort`)
set total = $#pulsars

echo "Total number of pulsars found: $total"

set index = 1

foreach pulsar ($pulsars)
  if ( $index >= $start && $index <= $end ) then
    echo "Processing pulsar $pulsar (index $index)"
    
    cd $pulsar
    
    foreach obs (`cat ${pulsar}.tim | awk -F_ '{ print $2}' | sort | uniq`)
      echo "Working on pulsar $pulsar observation $obs"
      
      set nlines = `cat $obs.tim | wc -l`
      
      if ( $nlines > 2 ) then
        tempo2 -npsr 1 -ntoa 1000 -nofit -fit DM -outpar ${obs}.auto.par -f ${pulsar}.par ${obs}.tim > /dev/null
      endif
    end
    
    echo "UTC,CHI2R,NPOINTS" > ${pulsar}.auto.CHI2R.csv
    grep CHI2R 2*.auto.par | sed -e "s/.auto.par:CHI2R//" | awk '{ print $1","$2","$3}' >> ${pulsar}.auto.CHI2R.csv
    
    cd ..
    
  endif
  @ index++
end

echo "Finished processing pulsars $start to $end"
