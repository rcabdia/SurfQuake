<img src="loc_flow_isp/resources/logo/surfQuake.png" width="600">

# SurfQuake

Earthquake source parameters from P- or S-wave displacement spectra

[![changelog-badge]][changelog-link]
[![license-badge]][license-link]
[![docs-badge]][docs-link]

## Description

SurfQuake is an opensource software designed to run an automatic flow of tasks in seismic studies. From pick seismic phases to Moment Tensor Inversion

See [Cabieces et al., (2023)] work in progress


## Installation

surfQuake to have anaconda installed. All the required dependencies will be
downloaded and installed during the insttallation process.

### Using Anaconda

The following command will automatically create an [Anaconda] environment
named `surfquake`. Go to the folder ./SurfQuake/install and type:

    conda env create -f ./mac_installer/mac_environment.yml
    conda env create -f ./linux_installer/linux_environment.yml

*The environment is exactly the same as Integrated Seismic Program*

Activate the environment with:

    conda activate surfquake

from within your environment.

    python start_locflow.py
