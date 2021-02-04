#!/bin/bash
# This script will process UBV files and call on remux to
# extract video footage using ffmpeg. Once completed it will
# sort the files by camera into separate directories.

INPUT_FILE="${1}"
OUTPUT_PATH="${2}"
echo "Extracting Footage from ${INPUT_FILE} to ${OUTPUT_PATH}"

# Remove -with-audio if you don't want that, but I do.
REMUX_PARAMS="-output-folder=\"${OUTPUT_PATH}\" -with-audio=true"
remux ${INPUT_FILE} ${REMUX_PARAMS}