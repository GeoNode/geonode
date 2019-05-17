#!/usr/bin/env bash

set -x

case $1 in
	"install")
		echo "Before install scripts"
        ;;
	"before_script")
		echo "Setting up PyTest suite"
		pip install pytest==4.3.1 pytest-bdd==3.1.0 pytest-splinter==2.0.1 pytest-django==3.4.8
		;;
esac
