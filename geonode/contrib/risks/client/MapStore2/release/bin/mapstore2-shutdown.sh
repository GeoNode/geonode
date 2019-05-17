#!/bin/sh
# -----------------------------------------------------------------------------
# Start Script for MapStore2
#
# $Id$
# -----------------------------------------------------------------------------

# Make sure catalina scripts are executable
chmod +x bin/*.sh

PRGDIR=`pwd`
EXECUTABLE=shutdown.sh
CATALINA_HOME="$PRGDIR"

if [ ! -x "$CATALINA_HOME"/bin/"$EXECUTABLE" ]; then
  echo "Cannot find $PRGDIR/$EXECUTABLE"
  echo "The file is absent or does not have execute permission"
  echo "This file is needed to run this program"
  exit 1
fi

sh "$CATALINA_HOME"/bin/"$EXECUTABLE" stop "$@"

echo "Waiting for services to stop..."
sleep 4
echo "Thank you for using MapStore2!"
