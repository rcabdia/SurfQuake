from PyQt5 import QtWidgets
pw = QtWidgets

class MessageDialog(pw.QMessageBox):

    def __init__(self, parent):
        super(MessageDialog, self).__init__(parent)
        self.setParent(parent)

        self.setWindowTitle("Message")
        # style
        self.setStyleSheet("QLabel#qt_msgbox_informativelabel {min-width:300px; font-size: 16px;}"
                           "QLabel#qt_msgbox_label {min-width:300px; font: bold 18px;}"
                           "QPushButton{ background-color: rgb(85, 87, 83); border-style: outset; font: 12px;"
                           "border-width: 1px; border-radius: 10px; border-color:rgb(211, 215, 207); "
                           "padding: 2px; color:white}"
                           "QPushButton:hover:pressed "
                           "{ background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, "
                           "stop: 0 #dadbde, stop: 1 #f6f7fa);} "
                           "QPushButton:hover{background-color:rgb(211, 215, 207); color: black;}")

        # self.setStandardButtons(pw.QMessageBox.Ok | pw.QMessageBox.Close) # Example with two buttons
        # self.setStandardButtons(pw.QMessageBox.NoButton) # Example with no buttons
        self.setStandardButtons(pw.QMessageBox.Close)

        self.accepted.connect(self.on_accepted)
        self.rejected.connect(self.on_reject)
        self.finished.connect(self.on_finished)

        self.show()

    def on_accepted(self):
        pass

    def on_reject(self):
        pass

    def on_finished(self):
        pass

    def __set_message(self, header: str, msg: str, msg_type, detailed_message=None):
        self.setIcon(msg_type)
        self.setText(header)
        self.setInformativeText(msg)
        if detailed_message:
            self.setDetailedText(detailed_message)

    def set_info_message(self, message: str, detailed_message=None):
        """
        Set an info message to the message dialog.

        :param message: The message to be display.

        :param detailed_message: Default=None. Useful for long texts, because it adds a scroll bar.

        :return:
        """
        self.__set_message("Info", message, pw.QMessageBox.Information, detailed_message=detailed_message)

    def set_warning_message(self, message: str, detailed_message=None):
        """
        Set a warning message to the message dialog.

        :param message: The message to be display.

        :param detailed_message: Default=None. Useful for long texts, because it adds a scroll bar.

        :return:
        """
        self.__set_message("Warning", message, pw.QMessageBox.Warning, detailed_message=detailed_message)

    def set_error_message(self, message, detailed_message=None):
        """
        Set an error message to the message dialog.

        :param message: The message to be display.

        :param detailed_message: Default=None. Useful for long texts, because it adds a scroll bar.

        :return:
        """
        self.__set_message("Error", message, pw.QMessageBox.Critical, detailed_message=detailed_message)