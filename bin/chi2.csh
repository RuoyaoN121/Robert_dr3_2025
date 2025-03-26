#!/bin/csh

echo code to calculate reduced chi^2 for every observation
echo in the $TIMING/partim_obs_2 directory
echo fit for DM as well

# setenv TEMPO2_CLOCK_DIR /fred/oz002/users/mbailes/astral/tempo2/clock/

# go to source of truth and copy all of the files pulsar by pulsar


cd $TIMING/partim_obs_2
set npsr = `ls | grep J | wc -l`

foreach pulsar (`ls | grep J`)
  cd $pulsar
  foreach obs (`cat ${pulsar}.tim | awk -F_ '{ print $2}' | sort | uniq`)
    echo working on pulsar $pulsar observation $obs
    set nlines = `cat $obs.tim | wc -l`
    if ( $nlines > 2 ) then
      tempo2 -npsr 1 -ntoa 1000 -nofit -fit DM -outpar ${obs}.auto.par -f ${pulsar}.par ${obs}.tim > /dev/null
    endif
  end
  echo "UTC,CHI2R,NPOINTS" > ${pulsar}.auto.CHI2R.csv 
  grep CHI2R 2*.auto.par | sed -e "s/.auto.par:CHI2R//" | awk '{ print $1","$2","$3}'>> ${pulsar}.auto.CHI2R.csv
  cd ..
end