#!/bin/bash

rm -rf docs/api/; ringo-doc --file-urls -s lib/ -d docs/api/ -p package.json -n "Stick API"
