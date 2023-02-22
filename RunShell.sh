#!/bin/bash

export DISPLAY=:0
export LD_LIBRARY_PATH=$PWD:$LD_LIBRARY_PATH

while :
do
  PID=$(ps -ef|grep "python3 main"|grep -v grep|awk '{print $2}')
  echo $PID
  if [ -z $PID ]; then
    echo "process provider not exist"s
  else
    echo "process id: $PID"
    kill -9 ${PID}
    echo "process provider killed"
  fi
  python3 main.py >> text.log 2>&1 &
  sleep 60
done

