#!/bin/bash

# exit on error and don't allow the use of unset variables
set -o errexit
set -o nounset
set -o verbose

# some env variables that will be used throughout this script
SCRIPTS_DIR="`dirname $0`"
export PYTHONPATH="${PYTHONPATH:-}:${SCRIPTS_DIR}/src"

rm -f haploqa.db
#python -m haploqa.sampleannoimport haploqa.db MegaMUGA "docs/Mouse 14may2014/Sample_Map.txt"
#python -m haploqa.probeannoimport haploqa.db "docs/Mouse 14may2014/MegaMUGA Marker Annotation 11Oct2012.csv"
#python -m haploqa.finalreportimport haploqa.db "docs/Mouse 14may2014/Jax_Lab_Osborne_MEGMUGV01_20140512_FinalReport.txt"

DATA_DIR="/Volumes/redhotdog/MegaMUGA-from-melania/181_Ellison_DO/Jackson_Laboratory_Harrison_MEGMUGV01_20150210/"
python -m haploqa.sampleannoimport haploqa.db MegaMUGA "${DATA_DIR}/Sample_Map.txt"
python -m haploqa.probeannoimport haploqa.db "docs/Mouse 14may2014/MegaMUGA Marker Annotation 11Oct2012.csv"
python -m haploqa.finalreportimport haploqa.db "${DATA_DIR}/Jackson_Laboratory_Harrison_MEGMUGV01_20150210_FinalReport.txt"
