#!/bin/bash

# exit on error and don't allow the use of unset variables
set -o errexit
set -o nounset
set -o verbose

# some env variables that will be used throughout this script
SCRIPTS_DIR="`dirname $0`"
export PYTHONPATH="${PYTHONPATH:-}:${SCRIPTS_DIR}/src"

py.test -v "${SCRIPTS_DIR}/src/tests/"
