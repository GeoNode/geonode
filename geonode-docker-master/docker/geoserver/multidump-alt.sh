#!/bin/sh

if [ $# -ne 3 ]; then
    echo "Usage: $0 pid interval count"
    exit 1
fi

PID=$1
INTERVAL=$2
COUNT=$3

top -bH -d $INTERVAL -n $COUNT -p $PID >> top.out 2>&1 &
for i in `seq $COUNT`; do
    kill -3 $PID
    sleep $INTERVAL
done
