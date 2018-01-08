#!/usr/bin/env bash

set -x

case $1 in
	"before_install")
		echo "Before install scripts"
		sudo apt-get -qq -y update
		sudo apt-get install build-essential chrpath libssl-dev libxft-dev libfreetype6-dev libfreetype6 libfontconfig1-dev libfontconfig1 -y
		sudo wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
		sudo tar xvjf phantomjs-2.1.1-linux-x86_64.tar.bz2 -C /usr/local/share/
		# sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/
		;;
	"before_script")
		echo "Setting up PyTest suite"
		pip install pytest==2.9.0 pytest-bdd==2.5.0 pytest-splinter pytest-django
		;;
esac
