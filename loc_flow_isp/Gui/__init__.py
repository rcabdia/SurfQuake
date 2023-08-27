import os
import sys
import PyQt5 as PyQt
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from loc_flow_isp import app_logger
from loc_flow_isp.Gui.controllers.window_controller import Controller


pyqt = PyQt
pqg = QtGui
pw = QtWidgets
pyc = QtCore
# qt = Qt
# file to save ui fields
user_preferences = pyc.QSettings(pyc.QSettings.NativeFormat, pyc.QSettings.UserScope, "isp", "user_pref")
#print(user_preferences.fileName())

def controller():

    return Controller()

def get_settings_file():
    return user_preferences.fileName()


def start_locflow():
    from loc_flow_isp.Gui.StyleLib import set_isp_mpl_style_file

    app = QtWidgets.QApplication(sys.argv)

    controller().open_locflow()
    set_isp_mpl_style_file()

    app_logger.info("Surf Quake Gui Started")
    app_logger.info("User preferences is at: {}".format(get_settings_file()))
    sys.exit(app.exec_())


def except_hook(cls, exception, exc_traceback):
    sys.__excepthook__(cls, exception, exc_traceback)
    controller().exception_parse(cls, exception, exc_traceback)

    #print(str(exception))


if __name__ == '__main__':
    sys.excepthook = except_hook
    start_locflow()
