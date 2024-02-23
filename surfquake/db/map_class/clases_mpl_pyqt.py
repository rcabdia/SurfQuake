
from matplotlib import rcParams
from PyQt5.QtCore import QSize
from PyQt5 import QtWidgets
from matplotlib.backends.backend_qt import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as Canvas
import cartopy.crs as ccrs
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from PyQt5.QtWidgets import QVBoxLayout
rcParams["font.family"] = "Ubuntu"
rcParams["font.size"] = 8
rcParams['axes.linewidth'] = 0.4
rcParams['patch.linewidth'] = .25

class MatplotlibWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(MatplotlibWidget, self).__init__(parent)

        self.fig = Figure()
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())

        self.lat = inset_axes(self.ax, width=0.4, height="100%", loc='center left',
                              bbox_to_anchor=(-0.08, 0.0, 1, 1),
                              bbox_transform=self.ax.transAxes, borderpad=0)
        self.lon = inset_axes(self.ax, width="100.0%", height=0.4, loc='upper center',
                              bbox_to_anchor=(0.00, 0.14, 1, 1),
                              bbox_transform=self.ax.transAxes, borderpad=0)
        self.lat.set_ylim(self.ax.get_ylim())
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



