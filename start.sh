#!/bin/sh
while [ true ]
do
    ./main.py
    # update one time in 8 hours 
    sleep $(( 3600 * 8 ))
done