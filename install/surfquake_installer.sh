#!/bin/bash

# ******************************************************************************
# *   surfQuake                                          *
# *                                                                            *
# *   A Python GUI for earthquake seismology and seismic signal processing     *
# *                                                                            *
# *   Copyright (C) 2025     Roberto Cabieces                                  *
# *   Copyright (C) 2025     Thiago C. Junqueira                               *
# *   Copyright (C) 2025     Jesús Relinque                                    *
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

# Function to detect OS and create Conda environment
create_surfquake_env() {
  OS_TYPE=$(uname -s)
  echo "Operating System detected: $OS_TYPE"

  if [[ $OS_TYPE == "Darwin" ]]; then
    echo "MacOS detected. Checking processor type..."
    
    # Determine processor type
    CPU_INFO=$(sysctl -n machdep.cpu.brand_string)
    echo "Processor Info: $CPU_INFO"

    if [[ $CPU_INFO == *"Apple"* ]]; then
      echo "Apple Silicon (M1/M2) detected."
      export OS="MacOSX-ARM"
      ENV_FILE="./mac_installer/mac_environment_arm.yml"
    else
      echo "Intel processor detected."
      export OS="MacOSX-Intel"
      ENV_FILE="./mac_installer/mac_environment.yml"
    fi
  elif [[ $OS_TYPE == "Linux" ]]; then
    echo "Linux detected."
    export OS="Linux"
    ENV_FILE="./linux_installer/linux_environment.yml"
  else
    echo "Unsupported operating system: $OS_TYPE"
    exit 1
  fi

  echo "Using Conda environment file: $ENV_FILE"
  conda env create -f "$ENV_FILE"
}


SURF_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )/.."

# Create/update the surfquake conda environment from file.yml
#echo "Updating Conda to the latest version..."
#conda update -n base -c defaults conda -y

# Check if the surfquake environment exists
if conda env list | grep -q '^surfquake\s'; then
  echo "'surfquake' environment already exists."
  read -p "Do you want to remove the existing environment and reinstall surfquake? (Y/N): " CHOICE
  case "$CHOICE" in
    [Yy]* )
      echo "Removing existing 'surfquake' environment..."
      conda remove --name surfquake --all -y
      echo "Reinstalling surfquake environment..."
      create_surfquake_env
      ;;
    * ) 
      echo "Skipping environment reinstallation. Proceeding with the existing setup."
      ;;
  esac
else
  echo "No 'surfquake' environment found. Proceeding to create one."
  create_surfquake_env
fi

echo "surfquake environment process finished"

# Compile packages
pushd ${SURF_DIR} > /dev/null
popd > /dev/null

# Creat an alias
# Create an alias for surfquake in multiple shell configurations
read -p "Create alias for surfquake in your shell configuration? [Y/n] " ALIAS_CHOICE
echo    # Move to a new line

if [[ $ALIAS_CHOICE =~ ^[Yy]$ ]]; then
    CONFIG_FILES=(~/.bashrc ~/.bash_profile ~/.zshrc ~/.zprofile ~/.profile ~/.kshrc ~/.tcshrc ~/.cshrc ~/.config/fish/config.fish)

    for PROFILE in "${CONFIG_FILES[@]}"; do
        if [[ -f "$PROFILE" ]]; then
            # Remove existing alias if present
            # Detect OS to choose correct sed syntax
            if [[ "$OSTYPE" == "darwin"* ]]; then
              SED_CMD="sed -i ''"
            else
              SED_CMD="sed -i"
            fi

            $SED_CMD '/# surfquake Installation/,/# surfquake Installation end/d' "$PROFILE"

            # Add new alias
            echo "# surfquake Installation" >> "$PROFILE"
            if [[ "$PROFILE" == *fish* ]]; then
                echo "alias surfq '${SURF_DIR}/surfquake.sh'" >> "$PROFILE"
            elif [[ "$PROFILE" == *tcshrc* || "$PROFILE" == *cshrc* ]]; then
                echo "alias surfq '${SURF_DIR}/surfquake.sh'" >> "$PROFILE"
            else
                echo "alias surfq='${SURF_DIR}/surfquake.sh'" >> "$PROFILE"
            fi
            echo "# surfquake Installation end" >> "$PROFILE"

            echo "Updated alias in $PROFILE"
        fi
    done

    echo "Aliases have been updated in your shell configuration files."
    echo "Run surfquake by typing 'surfq' in the terminal or execute ./SurfQuake/surfquake.sh "
else
    echo "To run surfquake, execute surfquake.sh at ${SURF_DIR}"
fi
