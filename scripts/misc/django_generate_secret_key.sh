#!/bin/bash

# This is the script directory
# pushd $(dirname $0)

# This is the current directory
pushd $PWD

OUTPUT=`python -c "import random,string;print(''.join([random.SystemRandom().choice(\"{}{}{}\".format(string.ascii_letters, string.digits, \"---\")) for i in range(63)]).replace('\\'','\\'\"\\'\"\\''))"; 2>&1`

echo $OUTPUT
