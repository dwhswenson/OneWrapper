#!/bin/bash

###### STANDARD INFORMATION FROM INPUT ################

STEP=$1
DELTA=$2
REPA=$3
REPB=$4
CONF=$5
MYCONF=$6

function semiparse
{
    grep "^$1" $2 | sed 's/\#.*//' | awk '{ print $2 }'
}

# Load up info about the two interfaces
STEPSTYLE=`semiparse "stepstyle" $CONF`
STEPNUM=`printf "$STEPSTYLE" $STEP`
NEXT=$(( $STEP + $DELTA ))
NEXTSTEP=`printf "$STEPSTYLE" $NEXT`
# we assume that REPA and REPB are correctly formatted
BASE=`semiparse "base" $CONF`



####### THINGS SPECIFIC TO THIS SCRIPT

echo "Accepting trajectory at $STEP | $REPA <=> $REPB"

swapfiles=`sed -n 's/^swapfile\ *//p' < $MYCONF`
for file in $swapfiles
do
    fileAstr=`echo $file | sed 's/REP/REPA/g'`
    fileBstr=`echo $file | sed 's/REP/REPB/g'`
    newfileAstr=`echo $fileAstr | sed 's/STEPNUM/NEXTSTEP/g'`
    newfileBstr=`echo $fileBstr | sed 's/STEPNUM/NEXTSTEP/g'`
    fileA=`eval echo $fileAstr`
    fileB=`eval echo $fileBstr`
    newfileA=`eval echo $newfileAstr`
    newfileB=`eval echo $newfileBstr`
    cp $fileA ${fileA}_tmp
    cp $fileB $newfileA
    mv ${fileA}_tmp $newfileB
done
