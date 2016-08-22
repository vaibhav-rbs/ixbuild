#!/usr/local/bin/bash

# Where is the pcbsd-build program installed
PROGDIR="`realpath | sed 's|/scripts$||g'`" ; export PROGDIR

# Source our functions
. ${PROGDIR}/scripts/functions.sh
. ${PROGDIR}/scripts/functions-tests.sh
. ${PROGDIR}/scripts/functions-vm.sh

# Source our resty / jsawk functions
. ${PROGDIR}/../utils/resty -W "http://${ip}:80/api/v1.0" -H "Accept: application/json" -H "Content-Type: application/json" -u ${fuser}:${fpass}

# Make sure we have all the required packages installed
${PROGDIR}/scripts/checkprogs.sh

if [ ! -d "${PROGDIR}/tmp" ] ; then
  mkdir ${PROGDIR}/tmp
fi


# Set the default FreeNAS testing IP address
if [ -z "${FNASTESTIP}" ] ; then
  FNASTESTIP="192.168.56.100"
  export FNASTESTIP
fi

# Set local location of FreeNAS build
if [ -n "$BUILDTAG" ] ; then
  FNASBDIR="/$BUILDTAG"
else
  FNASBDIR="/freenas"
fi
export FNASBDIR

# Figure out the ISO name
echo "Finding ISO file..."
if [ -d "${FNASBDIR}/objs" ] ; then
  ISOFILE=`find ${FNASBDIR}/objs | grep '\.iso$' | head -n 1`
elif [ -d "${FNASBDIR}/_BE/release" ] ; then
  ISOFILE=`find ${FNASBDIR}/_BE/release | grep '\.iso$' | head -n 1`
else
  if [ -n "$1" ] ; then
    ISOFILE=`find ${1} | grep '\.iso$' | head -n 1`
  else
    ISOFILE=`find ${PROGDIR}/../objs | grep '\.iso$' | head -n 1`
  fi
fi

# If no ISO found
if [ -z "$ISOFILE" ] ; then
  exit_err "Failed locating ISO file, did 'make release' work?"
fi

# Is this TrueNAS or FreeNAS?
echo $ISOFILE | grep -q "TrueNAS"
if [ $? -eq 0 ] ; then
   export FLAVOR="TRUENAS"
else
   export FLAVOR="FREENAS"
fi

echo "Using ISO: $ISOFILE"

# Create the automatic ISO installer
cd ${PROGDIR}/tmp
${PROGDIR}/scripts/create-auto-install.sh ${ISOFILE}
if [ $? -ne 0 ] ; then
  exit_err "Failed creating auto-install ISO!"
fi

# Determine which VM backend to use
if [ -n "$USE_BHYVE" ] ; then
  start_bhyve
else
  start_vbox
fi

# Give a minute to boot, should be ready for REST calls now
sleep 120

# Run the REST tests now
cd ${PROGDIR}/scripts

if [ -n "$FREENASLEGACY" ] ; then
  clean_xml_results
  ./9.10-create-tests.sh 2>&1 | tee >/tmp/fnas-tests-create.log
  ./9.10-update-tests.sh 2>&1 | tee >/tmp/fnas-tests-update.log
  ./9.10-delete-tests.sh 2>&1 | tee >/tmp/fnas-tests-delete.log
  res=$?
else
  clean_xml_results
  ./10-create-tests.sh 2>&1 | tee >/tmp/fnas-tests-create.log
  ./10-update-tests.sh 2>&1 | tee >/tmp/fnas-tests-update.log
  ./10-delete-tests.sh 2>&1 | tee >/tmp/fnas-tests-delete.log
  res=$?
fi

# Shutdown that VM
VBoxManage controlvm vminstall poweroff >/dev/null 2>/dev/null
sync

# Delete the VM
VBoxManage unregistervm $VM --delete

echo ""
echo "Output from console during runtime tests:"
echo "-----------------------------------------"
cat /tmp/vboxpipe

echo ""
echo "Output from REST API calls:"
echo "-----------------------------------------"
cat /tmp/fnas-tests-create.log
cat /tmp/fnas-tests-update.log
cat /tmp/fnas-tests-delete.log

exit $res
