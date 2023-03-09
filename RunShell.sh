#!/bin/bash

export DISPLAY=:0
export LD_LIBRARY_PATH=$PWD:$LD_LIBRARY_PATH


num=0
while :
do
  starttime=$(date +%Y-%m-%d\ %H:%M:%S)
  echo $starttime

  let num++
  pid_num=$(ps -ef | grep "python3 main_03_09"| grep -v "grep"| wc -l)
  echo "num" $num "pid_num" $pid_num
  #if [ $num -eq 10 -o $pid_num -ne 3 ];
  if [ $pid_num -ne 4 ];
  then
    echo "restart"
    pids=$(ps -ef | grep "python3 main_03_09" | grep -v "grep" | awk '{print $2}')
    echo $pids
    for pid in ${pids}
    do
        echo "kill pid" $pid
        kill -9 $pid
    done
    num=0
    python3 main_03_09.py >> text.log 2>&1 &
  fi
  sleep 50
done
