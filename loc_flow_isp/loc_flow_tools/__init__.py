import os
import platform

root_dir = os.path.dirname(__file__)
_parent_dir = os.path.dirname(root_dir)

_os = platform.system()

if _os.lower() == 'linux':
    bin_dir = os.path.join(_parent_dir, "binaries", "linux")
    real_bin = os.path.join(bin_dir, "REAL")
elif _os.lower() == 'windows':
    bin_dir = os.path.join(_parent_dir, "binaries", "win")
    real_bin = os.path.join(bin_dir, "REAL.exe")
elif _os.lower() == 'mac' or _os.lower() == 'darwin':
    bin_dir = os.path.join(_parent_dir, "binaries", "mac")
    real_bin = os.path.join(bin_dir, "REAL")  # TODO Roberto please add binaries for mac
else:
    raise AttributeError(f"The OS {_os} is not valid.")

__all__ = [
    'root_dir',
    'bin_dir',
    'real_bin',
]
