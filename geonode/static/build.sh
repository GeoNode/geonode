#!/bin/bash
set -e

do_npx=0
do_update=0
do_npm_install=0
do_yarn_install=1
do_lint=0
while getopts "xuny" opt
do
    case $opt in
    (x) do_npx=1 ;;
    (u) do_update=1 ;;
    (n) do_yarn_install=0 ; do_npm_install=1 ;;
    (y) do_yarn_install=1 ; do_npm_install=0 ;;
    (*) printf "Illegal option '-%s'\n" "$opt" && printf "Example usage: ./build.sh -un\n  Options:\n\t(x) Cleans node_modules\n\t(u) Runs npn update\n\t(n) Uses npm install instead of yarn\n\t(y) Uses yarn install instead of npm\n" && exit 1 ;;
    esac
done

(( do_npx )) && printf " - Cleaning node_modules...\n" && npx rimraf package-lock.json npm-shrinkwrap.json node_modules
(( do_update )) && printf " - Executing npm update...\n" && npm update
(( do_npm_install )) && printf " - Executing npm install...\n" && npm install
(( do_yarn_install )) && printf " - Executing yarn update...\n" && yarn install
printf " - Executing grunt...\n" && grunt development && grunt production
