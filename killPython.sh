#!/bin/bash

pids=$(ps -ef | grep "python3 main_03_09" | grep -v "grep" | awk '{print $2}')
for pid in ${pids}
do
    echo "kill pid" $pid
    kill -9 $pid
done
