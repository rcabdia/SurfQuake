from matplotlib import rcParams
from PyQt5.QtCore import QSize
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
from PyQt5.QtWidgets import QVBoxLayout
rcParams["font.family"] = "Ubuntu"
rcParams["font.size"] = 8
rcParams['axes.linewidth'] = 0.4
rcParams['patch.linewidth'] = .25

class MatplotlibWidgetStatistics(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidgetStatistics, self).__init__(parent)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.canvas = Canvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(self.toolbar)  # Add the toolbar after the canvas to place it at the bottom
        self.setLayout(self.vbl)

    def sizeHint(self):
        return self.canvas.sizeHint()
    #
    def minimumSizeHint(self):
         return QSize(10, 10)