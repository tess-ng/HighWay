#!/bin/bash

export DISPLAY=:0
export LD_LIBRARY_PATH=$PWD:$LD_LIBRARY_PATH


while :
do
  starttime=$(date +%Y-%m-%d\ %H:%M:%S)
  echo $starttime
  pid_num=$(ps -ef | grep "python3 main"| grep -v "grep"| wc -l)
  if [ $pid_num -ne 5 ];
  then
    echo "restart"
    pids=$(ps -ef | grep "python3 main" | grep -v "grep" | awk '{print $2}')
    echo $pids
    for pid in ${pids}
    do
        echo "kill pid" $pid
        kill -9 $pid
    done
    python3 main.py >> text.log 2>&1 &
  fi
  sleep 50
done
