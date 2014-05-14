#!/bin/bash
##############################################################################
# Finds the bin directory where node and npm are installed, or installs a
# local copy of them in a temp folder if not found. Then outputs where they
# are.
#
# Usage and install instructions:
# https://github.com/hugojosefson/find-node-or-install
##############################################################################

# Creates temp dir which stays the same every time this script executes
function setTEMP_DIR()
{
  local NEW_OS_SUGGESTED_TEMP_FILE=$(mktemp -t asdXXXXX)
  local OS_ROOT_TEMP_DIR=$(dirname ${NEW_OS_SUGGESTED_TEMP_FILE})
  rm ${NEW_OS_SUGGESTED_TEMP_FILE}
  TEMP_DIR=${OS_ROOT_TEMP_DIR}/nvm
  mkdir -p ${TEMP_DIR}
}

# Break on error
set -e

# Try to find node, but don't break if not found
NODE=$(which node || true)

if [[ -n "${NODE}" ]]; then
  # Good. We found it.
  echo $(dirname ${NODE})
else
  # Did not find node. Better install it.
  # Do it in a temp dir, which stays the same every time this script executes
  setTEMP_DIR
  cd ${TEMP_DIR}

  # Do we have nvm here?
  if [[ ! -d "nvm" ]]; then
    git clone git://github.com/creationix/nvm.git >/dev/null
  fi

  # Clear and set NVM_* env variables to our installation
  mkdir -p .nvm
  export NVM_DIR=$( (cd .nvm && pwd) )
  unset NVM_PATH
  unset NVM_BIN

  # Load nvm into current shell
  . nvm/nvm.sh >/dev/null

  # Install and use latest 0.10.* node
  nvm install 0.10 >/dev/null
  nvm alias default 0.10 >/dev/null
  nvm use default >/dev/null

  # Find and output node's bin directory
  NODE=$(which node)
  echo $(dirname ${NODE})
fi
