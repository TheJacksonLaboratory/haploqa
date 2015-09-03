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

#DATA_DIR="/Volumes/redhotdog/MegaMUGA-from-melania/181_Ellison_DO/Jackson_Laboratory_Harrison_MEGMUGV01_20150210/"
#python -m haploqa.sampleannoimport haploqa.db MegaMUGA "${DATA_DIR}/Sample_Map.txt"
#python -m haploqa.probeannoimport haploqa.db "data/Mouse 14may2014/MegaMUGA Marker Annotation 11Oct2012.csv"
#python -m haploqa.finalreportimport haploqa.db "${DATA_DIR}/Jackson_Laboratory_Harrison_MEGMUGV01_20150210_FinalReport.txt"

#DATA_DIR="/Users/kss/projects/muga-haploqa/data/UNC_Villena_GIGMUGV01_20141012/"
#python -m haploqa.sampleannoimport haploqa.db GIGAMuga "${DATA_DIR}/Sample_Map.txt"
#python -m haploqa.snpmapimport haploqa.db GIGAMuga "${DATA_DIR}/SNP_Map.txt"
#python -m haploqa.finalreportimport haploqa.db "${DATA_DIR}/UNC_Villena_GIGMUGV01_20141012_FinalReport.txt"

OSBORNE_DATA_DIR="/Users/kss/projects/muga-haploqa/data/Jax_Lab_Osborne_GIGMUGV01_20150705/"
python -m haploqa.snpmapimport GigaMUGA "${OSBORNE_DATA_DIR}/SNP_Map.txt"
python -m haploqa.finalreportimport GigaMUGA "${OSBORNE_DATA_DIR}/Jax_Lab_Osborne_GIGMUGV01_20150705_FinalReport.txt"
UNC_DATA_DIR="/Users/kss/projects/muga-haploqa/data/UNC_Villena_GIGMUGV01_20141012/"
python -m haploqa.finalreportimport GigaMUGA "${UNC_DATA_DIR}/UNC_Villena_GIGMUGV01_20141012_FinalReport.txt"
