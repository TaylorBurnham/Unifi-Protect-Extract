#!/bin/bash
# This script was modified from Peter's original source in the unifi-protect-remux repository.
# https://github.com/petergeneric/unifi-protect-remux/
#
# This script will locate UBV files missing their associated indexes for ffmpeg to process
# and generate them. I wrote in lockfile support so it has parallel support.

if [ -z "$UBVINFO" ] ; then
	UBVINFO=/usr/bin/ubnt_ubvinfo
fi

function helptext() {
	echo "Usage: $0 *_0_rotating_*.ubv"
}

function generate() {
	INPUT_FILE=$1
	OUTPUT_FILE="${INPUT_FILE}.txt"
	echo "Creating indices for ${INPUT_FILE}"
	${UBVINFO} -P -f "${INPUT_FILE}" > "${OUTPUT_FILE}"
	echo "Done!"
}

BASE_NAME="$(basename "$1")"
LOCK_FILE="/tmp/${BASE_NAME}.lock"
trap "rm -f ${LOCK_FILE}" SIGINT SIGTERM
if [ -z "$1" ] ; then
	helptext
	exit 1
elif [ "$1" == "--help" ] ; then
	helptext
	exit 0
elif [ -e "${LOCK_FILE}" ] ; then
	echo "${LOCK_FILE} exists for this file."
	exit 1
else
	touch "${LOCK_FILE}"
	generate ${1}
	rm -f "${LOCK_FILE}"
	trap - SIGINT SIGTERM
fi