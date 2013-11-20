# script that actually runs the program for shooting with gromacs

# run the program
# NOTE: $WORKDIR must be set in the startup or prologue
runprogram()
{
  # change to the scratch directory
  cd ${WORKDIR}

  # get filenames and generate directories for this and next tistraj
  TISTRAJSTR=`grep "^tistraj" ${BASE}/${CONF} | awk '{ print $2 }' | 
              sed 's/STEPNUM/STEP/'`
  TISTRAJ=`eval echo $TISTRAJSTR`
  mkdir -p `dirname $TISTRAJ`
  NEXT_TISTRAJ_STR=`echo $TISTRAJSTR | sed 's/\$STEP/\$NEXT/'`
  NEXT_TISTRAJ=`eval echo $NEXT_TISTRAJ_STR`
  mkdir -p `dirname $NEXT_TISTRAJ`

  echo "BASE = $BASE"
  echo "TISTRAJ = $TISTRAJ"
  echo "REPINFO = $REPINFO"

  # TODO: run the trajectory

  # TODO: make the tistraj from the trajectory
  touch $TISTRAJ 

  # TODO: check acceptance of the new trajectory based on the tistraj
  
  # TODO: copy (or symlink) most recently accepted trajectories to the right
  # location
  cp $TISTRAJ $NEXT_TISTRAJ
  
  # call OneWrapper again
  pushd $BASE
  echo "${ONEWRAPPER_PY} -N $NEXT -r $REP $CONF "
  ${ONEWRAPPER_PY} -N $NEXT -r $REP $CONF 
  popd
}

