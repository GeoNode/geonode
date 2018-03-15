#!/bin/bash 

# This is the script directory
# pushd $(dirname $0)

# This is the current directory
pushd $PWD

find . -name "*.pyc" -exec rm -f {} \;
