#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:14:55 2021

@author: robertocabieces
"""

from PyQt5 import uic
import os
from loc_flow_isp import UIS_PATH

print(UIS_PATH)
def load_ui_designers(ui_file):
    ui_path = os.path.join(UIS_PATH, ui_file)
    if not os.path.isfile(ui_path):
        raise FileNotFoundError("The file {} can't be found at the location {}".
                                format(ui_file, UIS_PATH))
    #ui_class, _ = uic.loadUiType(ui_path, from_imports=True, import_from='isp.resources')
    ui_class, _ = uic.loadUiType(ui_path)
    return ui_class