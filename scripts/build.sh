#!/bin/bash

set -e

ROOTDIR=$(pwd)

if [[ -z $1 ]]; then
  MODE=RELEASE
elif [[ $1 != "RELEASE" && $1 != "DEBUG" ]]; then
  echo "Invalid mode '$1', set to default mode."
  MODE=RELEASE
else
  MODE=$1
fi


echo "Building with mode '$MODE' at '$ROOTDIR'"

rm -rf $ROOTDIR/build
cmake -DCMAKE_BUILD_TYPE=$MODE -B $ROOTDIR/build $ROOTDIR
cmake --build $ROOTDIR/build -j4
