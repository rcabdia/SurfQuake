#!/bin/bash

# ******************************************************************************
# *   surfQuake                                          *
# *                                                                            *
# *   A Python GUI for earthquake seismology and seismic signal processing     *
# *                                                                            *
# *   Copyright (C) 2023     Roberto Cabieces                                  *
# *   Copyright (C) 2023     Thiago C. Junqueira                               *
# *   Copyright (C) 2023     Jesús Relinque                                    *
# *                                                                            *
# *   This file is part of surfQuake.                                          *
# *                                                                            *
# *   surfQuake is free software: you can redistribute it and/or modify it under the *
# *   terms of the GNU Lesser General Public License (LGPL) as published by    *
# *   the Free Software Foundation, either version 3 of the License, or (at    *
# *   your option) any later version.                                          *
# *                                                                            *
# *   surfQuake is distributed in the hope that it will be useful for any user or,   *
# *   institution, but WITHOUT ANY WARRANTY; without even the implied warranty *
# *   of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU      *
# *   Lesser General Public License (LGPL) for more details.                   *
# *                                                                            *
# *   You should have received a copy of the GNU LGPL license along with       *
# *   surfQuake. If not, see <http://www.gnu.org/licenses/>.                         *
# ******************************************************************************

# ******************************************************************************
# * SURFQUAKE INSTALLER USING CONDA ENVIRONMENT               *
# ******************************************************************************

SURF_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )/.."

# Create/update the isp conda environment from file.yml

conda env list | grep '^surfquake\s' > /dev/null
if (( $? )); then
  echo "No surfquake environment found. Creating one"

if [[ `uname -s` == "Darwin" ]]; then

export OS="MacOSX"  
conda env create -f ./mac_installer/mac_environment.yml

else
export OS="Linux"
conda env create -f ./linux_installer/linux_environment.yml
fi
else
echo "surfquake environment found"
fi


# Creat an alias
read -p "Create alias at .bashrc for surfquake?[Y/n] " -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
     echo "# surfquake Installation" >> ~/.bashrc
     echo "# surfquake Installation" >> ~/.bash_profile
     echo "# surfquake Installation" >> ~/.zshrc
     echo "# surfquake Installation" >> ~/.zprofile

     echo "alias surfq=${SURF_DIR}/surfquake.sh" >> ~/.bashrc
     echo "alias surfq=${SURF_DIR}/surfquake.sh" >> ~/.bash_profile
     echo "alias surfq=${SURF_DIR}/surfquake.sh" >> ~/.zshrc
     echo "alias surfq=${SURF_DIR}/surfquake.sh" >> ~/.zprofile

     echo "#  Installation end" >> ~/.bashrc
     echo "# surfq Installation end" >> ~/.bash_profile
     echo "# surfq Installation end" >> ~/.zshrc
     echo "# surfq Installation end" >> ~/.zprofile
     echo "Run surfquake GUI by typing surfq at terminal"
else
    echo "To run surfquake execute surfquake.sh at ${SURF_DIR}"
fi