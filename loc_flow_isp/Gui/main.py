#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 23 10:26:51 2021

@author: robertocabieces
"""
#from interface import designer_uis
from PyQt5 import QtWidgets
import sys

# Gesitona la aplicación y el bucle de eventos
from package.interface import designFrame

app = QtWidgets.QApplication(sys.argv)

w = designFrame()
w.show()

# Deja bloqueado el bucle de eventos hasta que no salgamos de la aplicación
sys.exit(app.exec_())