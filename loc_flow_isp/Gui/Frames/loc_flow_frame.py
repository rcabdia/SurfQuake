import os
import pickle
from obspy.geodetics import gps2dist_azimuth, kilometers2degrees
from loc_flow_isp import ROOT_DIR, model_dir, p_dir, station, ttime, nllinput
from loc_flow_isp.Exceptions.exceptions import parse_excepts
from loc_flow_isp.Gui.Frames.qt_components import MessageDialog
from loc_flow_isp.Gui.Frames.uis_frames import UiLoc_Flow
from PyQt5 import QtWidgets, QtGui, QtCore
from loc_flow_isp.Gui.Utils.pyqt_utils import BindPyqtObject, add_save_load
from sys import platform
from concurrent.futures.thread import ThreadPoolExecutor
from loc_flow_isp.Utils.obspy_utils import MseedUtil
from loc_flow_isp.loc_flow_tools.internal.real_manager import RealManager
from loc_flow_isp.loc_flow_tools.location_output.run_nll import NllManager
from loc_flow_isp.loc_flow_tools.phasenet.phasenet_handler import Util
from loc_flow_isp.loc_flow_tools.phasenet.phasenet_handler import PhasenetISP
from loc_flow_isp.loc_flow_tools.tt_db.taup_tt import create_tt_db
import numpy as np

#from PyQt5.QtCore import pyqtSlot

pw = QtWidgets
pqg = QtGui
pyc = QtCore
@add_save_load()
class LocFlow(pw.QMainWindow, UiLoc_Flow):

    def __init__(self):
        super(LocFlow, self).__init__()
        self.setupUi(self)
        self.__pick_output_path = nllinput
        self.__dataless_dir = None
        self.__nll_manager = None
        ####### Project ###########
        self.progressbar = pw.QProgressDialog(self)
        self.progressbar.setLabelText("Computing Project ")
        self.progressbar.setWindowIcon(pqg.QIcon(':\icons\map-icon.png'))
        self.progressbar.close()
        self.root_path_bind = BindPyqtObject(self.rootPathForm, self.onChange_root_path)
        self.pathFilesBtn.clicked.connect(lambda: self.on_click_select_directory(self.root_path_bind))
        self.openProjectBtn.clicked.connect(lambda: self.openProject())
        self.saveBtn.clicked.connect(lambda: self.saveProject())
        self.regularBtn.clicked.connect(lambda: self.load_files_done())
        self.phasenetBtn.clicked.connect(self.run_phasenet)
        self.realBtn.clicked.connect(self.run_real)
        self.plot_grid_stationsBtn.clicked.connect(self.plot_real_grid)

        # NonLinLoc
        self.grid_latitude_bind = BindPyqtObject(self.gridlatSB)
        self.grid_longitude_bind = BindPyqtObject(self.gridlonSB)
        self.grid_depth_bind = BindPyqtObject(self.griddepthSB)
        self.grid_xnode_bind = BindPyqtObject(self.xnodeSB)
        self.grid_ynode_bind = BindPyqtObject(self.ynodeSB)
        self.grid_znode_bind = BindPyqtObject(self.znodeSB)
        self.grid_dxsize_bind = BindPyqtObject(self.dxsizeSB)
        self.grid_dysize_bind = BindPyqtObject(self.dysizeSB)
        self.grid_dzsize_bind = BindPyqtObject(self.dzsizeSB)
        self.genvelBtn.clicked.connect(lambda: self.on_click_run_vel_to_grid())
        self.grdtimeBtn.clicked.connect(lambda: self.on_click_run_grid_to_time())
        self.runlocBtn.clicked.connect(lambda: self.on_click_run_loc())
        #self.plotmapBtn.clicked.connect(lambda: self.on_click_plot_map())
        self.stationsBtn.clicked.connect(lambda: self.on_click_select_metadata_file())

    # @pyc.Slot()
    # def _increase_progress(self):
    #      self.progressbar.setValue(self.progressbar.value() + 1)
    @property
    def nll_manager(self):
        if not self.__nll_manager:
            self.__nll_manager = NllManager(self.__pick_output_path, self.__dataless_dir)
        return self.__nll_manager

    def info_message(self, msg, detailed_message=None):
        md = MessageDialog(self)
        md.set_info_message(msg, detailed_message)

    def subprocess_feedback(self, err_msg: str, set_default_complete=True):
        """
        This method is used as a subprocess feedback. It runs when a raise expect is detected.

        :param err_msg: The error message from the except.
        :param set_default_complete: If True it will set a completed successfully message. Otherwise nothing will
            be displayed.
        :return:
        """
        if err_msg:
            md = MessageDialog(self)
            if "Error code" in err_msg:
                md.set_error_message("Click in show details detail for more info.", err_msg)
            else:
                md.set_warning_message("Click in show details for more info.", err_msg)
        else:
            if set_default_complete:
                md = MessageDialog(self)
                md.set_info_message("Completed Successfully.")

    def set_pick_output_path(self, file_path):
        self.__pick_output_path = file_path
        self.nll_manager.set_observation_file(file_path)
    def onChange_root_path(self, value):
        """
        Fired every time the root_path is changed

        :param value: The path of the new directory.

        :return:
        """
        pass

    def load_files_done(self):

        if self.rootPathForm_inv.text() == "":
            filter = "All files (*.*)"
        else:

            filter = self.rootPathForm_inv.text()
        print(filter)

        selected_files, _ = pw.QFileDialog.getOpenFileNames(self, "Select Project", ROOT_DIR, filter=filter)

        md = MessageDialog(self)
        md.hide()

        try:
            ms = MseedUtil()
            self.progressbar.reset()
            self.progressbar.setLabelText("Bulding Project")
            self.progressbar.setRange(0, 0)

            def callback():
                r = ms.search_indiv_files(selected_files)
                pyc.QMetaObject.invokeMethod(self.progressbar, "accept")
                return r

            with ThreadPoolExecutor(1) as executor:
                f = executor.submit(callback)
                self.progressbar.exec()
                self.project = f.result()
                f.cancel()

            md.set_info_message("Created Project")

        except:

            md.set_error_message("Something went wrong. Please check that your data files are correct mseed files")

        md.show()



    def on_click_select_directory(self, bind: BindPyqtObject):

        if "darwin" == platform:
            dir_path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', bind.value)
        else:
            dir_path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', bind.value,
                                                           pw.QFileDialog.DontUseNativeDialog)

        if dir_path:
            bind.value = dir_path


    def openProject(self):

        md = MessageDialog(self)
        md.hide()
        try:
            ms = MseedUtil()
            self.progressbar.reset()
            self.progressbar.setLabelText("Bulding Project")
            self.progressbar.setRange(0, 0)
            def callback():
                r = ms.search_files(self.root_path_bind.value)
                pyc.QMetaObject.invokeMethod(self.progressbar, "accept")
                return r
            with ThreadPoolExecutor(1) as executor:
                f = executor.submit(callback)
                self.progressbar.exec()
                self.project = f.result()
                f.cancel()

            md.set_info_message("Created Project")

        except:

            md.set_error_message("Something went wrong. Please check that your data files are correct mseed files")

        md.show()



    def saveProject(self):

        try:
            if "darwin" == platform:
                path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', self.root_path_bind.value)
            else:
                path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', self.root_path_bind.value,
                                                           pw.QFileDialog.DontUseNativeDialog)
            if not path:
                return

            file_to_store = open(os.path.join(path,self.nameForm.text()), "wb")
            pickle.dump(self.project, file_to_store)

            md = MessageDialog(self)
            md.set_info_message("Project saved successfully")

        except:

            md = MessageDialog(self)
            md.set_info_message("No data to save in Project")


###################  RunPicker   ############


    def load_project(self):
        self.loaded_project = True
        selected = pw.QFileDialog.getOpenFileName(self, "Select Project", ROOT_DIR)

        md = MessageDialog(self)

        if isinstance(selected[0], str) and os.path.isfile(selected[0]):
            try:
                self.current_project_file = selected[0]
                self.project = MseedUtil.load_project(file = selected[0])
                project_name = os.path.basename(selected[0])
                md.set_info_message("Project {} loaded  ".format(project_name))
            except:
                md.set_error_message("Project couldn't be loaded ")
        else:
            md.set_error_message("Project couldn't be loaded ")

    ######################

    def run_phasenet(self):
        self.project = None
        print("Starting Picking")
        self.load_project()
        phISP = PhasenetISP(self.project, modelpath=model_dir, amplitude=True)
        picks = phISP.phasenet()

        """ PHASENET OUTPUT TO REAL INPUT"""
        picks_ = Util.split_picks(picks)
        Util.convert2real(picks_)

    def plot_real_grid(self):

        lon_min = self.lon_refMin.value()
        lon_max = self.lon_refMaxSB.value()
        lat_max = self.lat_refMaxSB.value()
        lat_min = self.lat_refMinSB.value()
        self.latitude_center = (lat_min + lat_max) / 2
        self.longitude_center = (lon_min + lon_max) / 2
        self.h_range = kilometers2degrees(gps2dist_azimuth(self.latitude_center, self.longitude_center, lat_max, lon_max) * 0.001)
        self.gridSearchParamHorizontalRangeBtn.set_value(self.h_range)

    def run_real(self):
        """ REAL """
        #tt_db = create_tt_db()
        #tt_db.run_tt_db(dist=self.h_range, depth=self.depthSB.value(), ddist=0.01, ddep=1)

        ### grid ###
        gridSearchParamHorizontalRange = self.gridSearchParamHorizontalRangeBtn.value()
        HorizontalGridSize = self.HorizontalGridSizeBtn.value()
        DepthSearchParamHorizontalRange = self.DepthSearchParamHorizontalRangeBtn.value()
        DepthGridSize = self.DepthGridSizeBtn.value()
        EventTimeW = self.EventTimeWindow.value()

        ### travel_time ###
        TTHorizontalRange = self.TTHorizontalRangeBtn.value()
        TTHorizontalGridSize = self.TTHorizontalGridSizeBtn.value()
        TTDepthGridSize = self.TTDepthGridSizeBtn.value()
        TTDepthRange = self.TTDepthRangeBtn.value()

        # Picks Thresholds

        ThresholdPwave = self.ThresholdPwaveSB.value()
        ThresholdSwave = self.ThresholdSwaveSB.value()
        number_stations_picks = self.number_stations_picksSB.value()

        real_handler = RealManager(pick_dir=p_dir, station_file=station, time_travel_table_file=ttime,
            gridSearchParamHorizontalRange=gridSearchParamHorizontalRange, HorizontalGridSize=HorizontalGridSize,
            DepthSearchParamHorizontalRange = DepthSearchParamHorizontalRange, DepthGridSize=DepthGridSize,
            EventTimeW = EventTimeW, TTHorizontalRange=TTHorizontalRange, TTHorizontalGridSize=TTHorizontalGridSize,
            TTDepthGridSize=TTDepthGridSize, TTDepthRange=TTDepthRange, ThresholdPwave=ThresholdPwave,
                                   ThresholdSwave=ThresholdSwave, number_stations_picks=number_stations_picks)

        self.latitude_center = 42.5
        real_handler.latitude_center = self.latitude_center
        print(real_handler.stations)

        ### Real Parameters ####

        for events_info in real_handler:
             print(events_info)
             print(events_info.events_date)

        real_handler.save()
        real_handler.compute_t_dist()
        #convert.real2nll(realout, nllinput)

    def on_click_select_metadata_file(self):
        selected = pw.QFileDialog.getOpenFileName(self, "Select metadata/stations coordinates file")
        if isinstance(selected[0], str) and os.path.isfile(selected[0]):
            self.stationsPath.setText(selected[0])
            self.set_dataless_dir(self.stationsPath.text())

    def set_dataless_dir(self, dir_path):
        self.__dataless_dir = dir_path
        self.nll_manager.set_dataless_dir(dir_path)
    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg))
    def on_click_run_vel_to_grid(self):
        self.nll_manager.vel_to_grid(self.grid_latitude_bind.value, self.grid_longitude_bind.value,
                                     self.grid_depth_bind.value, self.grid_xnode_bind.value,
                                     self.grid_ynode_bind.value, self.grid_znode_bind.value,
                                     self.grid_dxsize_bind.value, self.grid_dysize_bind.value,
                                     self.grid_dzsize_bind.value, self.comboBox_gridtype.currentText(),
                                     self.comboBox_wavetype.currentText(), self.modelCB.currentText())


    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg))
    def on_click_run_grid_to_time(self):


        if self.distanceSB.value()>0:
            limit = self.distanceSB.value()
        else:
            limit = np.sqrt((self.grid_xnode_bind.value * self.grid_dxsize_bind.value) ** 2 +
                            (self.grid_xnode_bind.value * self.grid_dxsize_bind.value) ** 2)

        self.nll_manager.grid_to_time(self.grid_latitude_bind.value, self.grid_longitude_bind.value,
                                      self.grid_depth_bind.value, self.comboBox_grid.currentText(),
                                      self.comboBox_angles.currentText(), self.comboBox_ttwave.currentText(), limit)

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg, set_default_complete=False))
    def on_click_run_loc(self):
        transform = self.transCB.currentText()
        std_out = self.nll_manager.run_nlloc(self.grid_latitude_bind.value, self.grid_longitude_bind.value,
                                             self.grid_depth_bind.value, transform)
        self.info_message("Location complete. Check details.", std_out)

