#!/bin/bash

ONEWRAP="/home/dwhs/OneWrapper"

STEPNUM=$1
DELTA=$2
CONF=$3
MYCONF=$4

echo "shooting.sh $STEPNUM $REPNUM $DELTA $CONF $MYCONF"

# NOTE: all things handled by the semiparse function must have the card at
# the start of the line, and the part that gets returned must have no spaces
function semiparse
{
    grep "^$1" $2 | sed 's/\#.*//' | awk '{ print $2 }'
}

REPS=`grep "replicas" $MYCONF | sed 's/replicas\ *\(.*\)\#.*/\1/'`

echo $REPS


# extract the base directory name from the RETIS conf file
BASE=`semiparse "base" $CONF`
STEPSTYLE=`semiparse "stepstyle" $CONF`
STEP=`printf "$STEPSTYLE" $STEPNUM`
REPSTYLE=`semiparse "repstyle" $CONF`
REPINFO=`semiparse "repinfo" $CONF`

# and extract some stuff we want from the shooting conf file
PYTMPL=`semiparse "pytmpl" $MYCONF`
LAUNCHPARSE=`semiparse "launchjob" $MYCONF`

##### RUN THE MAIN SCRIPT FOR EACH REPLICA 

for REPNUM in $REPS
do
    REP=`printf "$REPSTYLE" $REPNUM`
    #echo "LAUNCHPARSE = $LAUNCHPARSE"
    LAUNCHJOB=`eval echo $LAUNCHPARSE`
    echo "Running shooting move $STEP for replica $REP"
    echo "Job script in $LAUNCHJOB"
    # Prepare the shooting move
    # 1. Modify conditions so that you can run the dynamics needed (at first,
    #    we're doing this in the job template)

    # 2. Generate the job script from the job template
    ${ONEWRAP}/gen_move.py -N $STEPNUM -d $DELTA -r $REP --base $BASE \
        --conf $CONF --repfile $REPINFO $PYTMPL > $LAUNCHJOB


    # 3. Launch the job (i.e., add to qsubdir)
    ${ONEWRAP}/qsubdir ${LAUNCHJOB}
done


