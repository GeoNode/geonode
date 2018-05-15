#!/bin/bash

# This is the script directory
# pushd $(dirname $0)

# This is the current directory
pushd $PWD

git fetch --all --prune
OUTPUT=`git branch -r | awk '{print $1}' | egrep -v -f /dev/fd/0 <(git branch -vv) | awk '{print $1}' | xargs git branch -D 2>&1`

`echo $OUTPUT | grep 'branch name required' &> /dev/null`
if [ $? == 0 ]; then
   echo "All remote branches are aligned!"
   BRANCH=`git branch 2>&1`
   echo "You are currently on branch: $BRANCH"
fi
