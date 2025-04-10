#!/bin/bash

set -ex

ROOTDIR=$(pwd)

if [[ -z $1 ]]; then
  MODE=RELEASE
elif [[ $1 != "RELEASE" && $1 != "DEBUG" ]]; then
  echo "Invalid mode '$1', set to default mode."
  MODE=RELEASE
else
  MODE=$1
fi

if [[ -z $2 ]]; then
  ENABLE_TEST=ON
elif [[ $2 != "ON" && $2 != "OFF" ]]; then
  echo "Invalid mode '$2', set to default mode."
  ENABLE_TEST=ON
else
  ENABLE_TEST=$2
fi


echo "Building with mode '$MODE' at '$ROOTDIR'"

rm -rf $ROOTDIR/build
cmake -DCMAKE_BUILD_TYPE=$MODE -DENABLE_TESTING=$ENABLE_TEST -B $ROOTDIR/build $ROOTDIR
cmake --build $ROOTDIR/build -j
