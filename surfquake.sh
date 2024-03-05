#!/bin/bash

SURF_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

# Activate environment
source $(conda info --base)/etc/profile.d/conda.sh

if [[ `uname -s` == "Darwin" ]]; then
	export OS="MacOSX"
	source activate surfquake
else
	export OS="Linux"
	conda activate surfquake
fi

pushd ${SURF_DIR} > /dev/null
python start_surfquake.py
popd > /dev/null
