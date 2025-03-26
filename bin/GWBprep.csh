#!/bin/csh

echo final filter on auto.tim files to create .gwb.tim files

cd $TIMING/partim_obs_2

echo removing all tim files with CHI2R \> 3.6 and npts \<= 7
echo also remove points with nbands \< 5
echo leaves behind a file JNAME.gwb.tim

set ncopied = 0


foreach pulsar (`ls -1 | grep J`)
  echo working on pulsar $pulsar
  cd $pulsar
  foreach obs (`cat $pulsar.auto.CHI2R.csv | grep -v CHI | awk -F, '{print $1}'`)
    set chi2r = `cat $pulsar.auto.CHI2R.csv | grep -v CHI | \grep $obs| awk -F, '{print $2 }'`
    set npts = `cat $pulsar.auto.CHI2R.csv | grep -v CHI |\grep $obs| awk -F, '{print $3 }'`
    set chi2rtest = `echo $chi2r | awk '{ if ($1 ~ /^[0-9]+(\.[0-9]+)?$/ && $1 < 3.6) print 1; else print 0}'`
    if ( ( $chi2rtest == 1 ) && ( $npts > 7 ) ) then
      cp ${obs}.tim ${obs}.gwb.tim
      @ ncopied++
    endif
  end
  cat 2*.gwb.tim > ${pulsar}.gwb.tim
  echo now copied $ncopied observations
  cd .. 
end


exit