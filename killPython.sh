#!/bin/bash

pids=$(ps -ef | grep "python 03_31_main" | grep -v "grep" | awk '{print $2}')
for pid in ${pids}
do
    echo "kill pid" $pid
    kill -9 $pid
done
