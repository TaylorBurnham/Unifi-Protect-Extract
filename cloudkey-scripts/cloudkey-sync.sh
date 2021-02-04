#!/bin/bash
# Destination Settings
RSYNC_USER="cloudkey-sync"
RSYNC_HOST="nas.local"
RSYNC_PATH="/path/to/sync/dest"

# Set our paths
SRC_PATH="/srv/unifi-protect/video/"
DST_PATH="${RSYNC_USER}@${RSYNC_HOST}:${RSYNC_PATH}"

# Lockfile Settings
BASE_NAME="$(basename "$0")"
LOCK_FILE="/tmp/${BASE_NAME}.lock"
trap "rm -f ${LOCK_FILE}" SIGINT SIGTERM
if [ -e "${LOCK_FILE}" ]
then
    echo "${BASE_NAME} is already running."
    exit
else
    # Touch the lockfile
    touch "${LOCK_FILE}"
    # Now rsync
    echo "Synchronizing Files from ${SRC_PATH} to ${DST_PATH}"
    rsync -avP --inplace \
     -e "ssh -i /root/.ssh/id_rsa -p 22" \
     --include="*_0_rotating_*.ubv" \
     --exclude="*_2_*" \
     --exclude="*_0_timelapse*" \
     --exclude="pool" \
     "${SRC_PATH}" "${DST_PATH}"
    echo "Done!"
    rm -f "${LOCK_FILE}"
    trap - SIGINT SIGTERM
fi