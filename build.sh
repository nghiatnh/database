#!/bin/bash

set -eux

clear
rm -rf build
cmake -B build .
cmake --build build -j4
