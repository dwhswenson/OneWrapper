#!/bin/bash

##### RUN THE MAIN SCRIPT
echo "Running shooting move $1" >> moves.txt

echo "Launch rep 000" >> moves.txt
echo "Launch rep 001" >> moves.txt

echo "Finishing rep 000" >> moves.txt
echo "python OneWrapper.py -N $(( $1 + 1 )) -r 000 example_retis.conf >> moves.txt " | 
batch > /dev/null
echo "Finishing rep 001" >> moves.txt
echo "python OneWrapper.py -N $(( $1 + 1 )) -r 001 example_retis.conf >> moves.txt " | 
batch > /dev/null

# NOTE: the last thing the script should do (within the qsub) is to launch
# the wrapper again


