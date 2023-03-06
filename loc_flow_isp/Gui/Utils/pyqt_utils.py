import os
from PyQt5 import uic
from loc_flow_isp.Gui.package.interface_tools import UIS_PATH
from PyQt5 import QtCore, QtGui, QtWidgets

pyc = QtCore
pqg = QtGui
pyc = QtCore
pw = QtWidgets


def load_ui_designers(ui_file):
    ui_path = os.path.join(UIS_PATH, ui_file)
    if not os.path.isfile(ui_path):
        raise FileNotFoundError("The file {} can't be found at the location {}".
                                format(ui_file, UIS_PATH))
    ui_class, _ = uic.loadUiType(ui_path, from_imports=True, import_from='isp.resources')
    return ui_class


class BindPyqtObject(pyc.QObject):
    """
    Bind a pyqt object to this class
    """

    def __init__(self, pyqt_obj, callback=None):
        """
        Create an instance that has value property bind to the pyqt object value.

        :param pyqt_obj: The pyqt object to bind to, i.e: QLineEdit, QSpinBox, etc..

        :param callback: A callback function that is called when the pyqt object change value.
        """
        super().__init__()

        if isinstance(pyqt_obj, pw.QLineEdit):
            value = pyqt_obj.text()
            pyqt_obj.textChanged.connect(self.__valueChanged)
            self.__set_value = lambda v: pyqt_obj.setText(v)

        elif isinstance(pyqt_obj, pw.QSpinBox) or isinstance(pyqt_obj, pw.QDoubleSpinBox):
            value = pyqt_obj.value()
            pyqt_obj.valueChanged.connect(self.__valueChanged)
            self.__set_value = lambda v: pyqt_obj.setValue(v)

        elif isinstance(pyqt_obj, pw.QComboBox):
            value = pyqt_obj.currentText()
            pyqt_obj.currentTextChanged.connect(self.__valueChanged)
            self.__set_value = lambda v: pyqt_obj.setCurrentText(v)

        else:
            raise AttributeError("The object {} don't have a valid type".format(pyqt_obj))

        self.__value = value
        self.__callback_val_changed = callback
        self.set_valueChanged_callback(callback)
        self.pyqt_obj = pyqt_obj

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        if self.__value != value:
            self.__set_value(value)

    @pyc.pyqtSlot(float)
    @pyc.pyqtSlot(int)
    @pyc.pyqtSlot(str)
    def __valueChanged(self, value):
        self.__value = value
        if self.__callback_val_changed:
            self.__callback_val_changed(value)

    def set_valueChanged_callback(self, func):
        if func is not None:
            self.__callback_val_changed = lambda v: func(v)

    def unblind_valueChanged(self):
        self.__callback_val_changed = None

    @staticmethod
    def __validate_event(event: pqg.QDropEvent):
        data = event.mimeData()
        urls = data.urls()
        accept = True
        for url in urls:
            if not url.isLocalFile():
                accept = False

        if accept:
            event.acceptProposedAction()

    def __drop_event(self, event: pqg.QDropEvent, func):
        if func:
            func(event, self)

    def accept_dragFile(self, drop_event_callback=None):
        """
        Makes this object accept drops.

        :param drop_event_callback: A callback function that is called when the object is drop. The callback must
            have the parameters event and a BindPyqtObject object.

        :return:
        """
        if hasattr(self.pyqt_obj, "setDragEnabled"):
            self.pyqt_obj.setDragEnabled(True)
            self.pyqt_obj.dragEnterEvent = self.__validate_event
            self.pyqt_obj.dragMoveEvent = self.__validate_event
            self.pyqt_obj.dropEvent = lambda event: self.__drop_event(event, drop_event_callback)
        else:
            raise AttributeError("The object {} doesn't have the method setDragEnabled".
                                 format(self.pyqt_obj.objectName()))

    def set_visible(self, is_visible: bool):
        """
        Set visibility of the pyqt object.

        :param is_visible: Either it should be visible or not.
        :return:
        """
        self.pyqt_obj.setVisible(is_visible)