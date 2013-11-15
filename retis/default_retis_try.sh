#!/bin/bash

STEP=$1
DELTA=$2
REPA=$3
REPB=$4
CONF=$5
MYCONF=$6

# NOTE: all things handled by the semiparse function must have the card at
# the start of the line, and the part that gets returned must have no spaces
function semiparse
{
    grep "^$1" $2 | sed 's/\#.*//' | awk '{ print $2 }'
}

function maxlambda
{
    gawk -v col=4 'BEGIN {max="-inf"} 
                    { if (max<$(col)) { max=$(col) } } 
                    END { print max }' < $1
}

# Load up info about the two interfaces
STEPSTYLE=`semiparse "stepstyle" $CONF`
STEPNUM=`printf "$STEPSTYLE" $STEP`
NEXT=$(( $STEP + $DELTA ))
NEXTSTEP=`printf "$STEPSTYLE" $NEXT`
# we assume that REPA and REPB are correctly formatted
BASE=`semiparse "base" $CONF`
TISTRAJ=`semiparse "tistraj" $CONF`
REPINFO=`semiparse "repinfo" $CONF`
repaline=`awk -v rep=$REPA '$1 ~ rep { print $0 }' $REPINFO`
repbline=`awk -v rep=$REPB '$1 ~ rep { print $0 }' $REPINFO`
tistrajAstr=`echo $TISTRAJ | sed 's/REP/REPA/'`
tistrajBstr=`echo $TISTRAJ | sed 's/REP/REPB/'`
tistrajA=`eval echo $tistrajAstr`
tistrajB=`eval echo $tistrajBstr`


setA=`echo $repaline | awk '{ print $2 }'`
setB=`echo $repbline | awk '{ print $2 }'`
lambdaA=`echo $repaline | awk ' { print $3 }'`
lambdaB=`echo $repbline | awk ' { print $3 }'`
scriptA=`echo $repaline | awk ' { print $4 }'`
scriptB=`echo $repbline | awk ' { print $4 }'`

# read these variables names as, e.g., "maximum lambda for the trajectory in
# replica A, based on the order parameter used for replica set A"
maxlambdaA_setA=`maxlambda $tistrajA`
maxlambdaB_setB=`maxlambda $tistrajB`

#echo "A : $setA $lambdaA $scriptA $maxlambdaA_setA $tistrajA"
#echo "B : $setB $lambdaB $scriptB $maxlambdaB_setB $tistrajB"

# Check whether we're looking at the same interface set for both
if [ "$setA" = "$setB" ]
then
    maxlambdaA_setB=$maxlambdaA_setA
    maxlambdaB_setA=$maxlambdaB_setB
else
    echo "TODO: have to recalculate lambdas if replica sets are different"
fi

# Test whether we cross each other
swaptest=`echo $maxlambdaA_setB $lambdaB $maxlambdaB_setA $lambdaA |
    awk '{ if (($1 > $2) && ($3 > $4)) { print 1 } else { print 0 } }'`
echo $swaptest
