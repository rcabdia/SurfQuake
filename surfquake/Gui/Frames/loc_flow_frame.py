import os
import pickle
import pandas as pd
from obspy.geodetics import gps2dist_azimuth, kilometers2degrees
from surfquake import ROOT_DIR, model_dir, p_dir, station, ttime, nllinput, realout, magnitudes_config, magnitudes
from surfquake.DataProcessing.metadata_manager import MetadataManager
from surfquake.Exceptions.exceptions import parse_excepts
from surfquake.Gui.Frames import BaseFrame
from surfquake.Gui.Frames.qt_components import MessageDialog
from surfquake.Gui.Frames.uis_frames import UiLoc_Flow
from PyQt5 import QtWidgets, QtGui, QtCore, Qt
from surfquake.Gui.Utils.pyqt_utils import BindPyqtObject, add_save_load
from sys import platform
from concurrent.futures.thread import ThreadPoolExecutor
from surfquake.Utils import obspy_utils
from surfquake.Utils.obspy_utils import MseedUtil
from surfquake.loc_flow_tools.internal.real_manager import RealManager
from surfquake.loc_flow_tools.location_output.run_nll import NllManager
from surfquake.loc_flow_tools.phasenet.phasenet_handler import PhasenetUtils as Util
from surfquake.loc_flow_tools.phasenet.phasenet_handler import PhasenetISP
from surfquake.Gui.Frames.event_location_frame import EventLocationFrame
from surfquake.Gui.Frames.parameters import ParametersSettings
from obspy.core.inventory.inventory import Inventory
from surfquake.loc_flow_tools.tt_db.taup_tt import create_tt_db
import numpy as np
from surfquake.loc_flow_tools.utils import ConversionUtils
from surfquake.Utils.time_utils import AsycTime
from surfquake.magnitude_tools.autoag import Automag
from surfquake.maps.plot_map import plot_real_map
from surfquake.sq_isola_tools.sq_bayesian_isola import bayesian_isola_db

pw = QtWidgets
pqg = QtGui
pyc = QtCore
@add_save_load()
class LocFlow(BaseFrame, UiLoc_Flow):

    def __init__(self):
        super(LocFlow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('SurfQuake')
        self.__pick_output_path = nllinput
        self.__dataless_dir = None
        self.__nll_manager = None
        self.db_frame = None
        self.latitude_center = None
        self.longitude_center = None
        self.h_range = None
        self.inventory = None
        self.project = None
        self.parameters = ParametersSettings()
        ####### Metadata ##########
        self.metadata_path_bind = BindPyqtObject(self.datalessPathForm, self.onChange_metadata_path)
        self.loadMetaBtn.clicked.connect(lambda: self.on_click_select_file(self.metadata_path_bind))

        ####### Project ###########

        self.progressbar = pw.QProgressDialog(self)
        self.progressbar.setLabelText("Computing Project ")
        self.progressbar.setWindowIcon(pqg.QIcon(':\icons\map-icon.png'))
        self.progressbar.close()
        self.root_path_bind = BindPyqtObject(self.rootPathForm, self.onChange_root_path)
        self.pathFilesBtn.clicked.connect(lambda: self.on_click_select_directory(self.root_path_bind))
        self.loadProjectBtn.clicked.connect(lambda: self.load_project())
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
        #self.stationsBtn.clicked.connect(lambda: self.on_click_select_metadata_file())
        self.actionData_Base.triggered.connect(lambda: self.open_data_base())

        # Magnitude

        self.mag_runBtn.clicked.connect(lambda: self.run_automag())

        # MTI
        self.mti_path_bind = BindPyqtObject(self.mti_working_path, self.onChange_root_path)
        self.earth_model_bind = BindPyqtObject(self.earth_model_path, self.onChange_root_path)
        self.workingDirectoryMTIBtn.clicked.connect(lambda: self.on_click_select_directory(self.mti_path_bind))
        self.earthModelMTIBtn.clicked.connect(lambda: self.on_click_select_file(self.earth_model_bind))
        self.mti_output_path_bind = BindPyqtObject(self.MTI_output_path, self.onChange_root_path)
        self.outputDirectoryMTIBtn.clicked.connect(lambda: self.on_click_select_directory(self.mti_output_path_bind))
        self.macroMITBtn.clicked.connect(lambda: self.open_parameters_settings())
        self.runInversionMTIBtn.clicked.connect(lambda: self.run_mti())
        # Dialog

        self.progress_dialog = pw.QProgressDialog(self)
        self.progress_dialog.setRange(0, 0)
        self.progress_dialog.setWindowTitle('Processing.....')
        self.progress_dialog.setLabelText('Please Wait')
        self.progress_dialog.setWindowIcon(self.windowIcon())
        self.progress_dialog.setWindowTitle(self.windowTitle())
        self.progress_dialog.close()

    # @pyc.Slot()
    # def _increase_progress(self):
    #      self.progressbar.setValue(self.progressbar.value() + 1)
    def open_parameters_settings(self):
        self.parameters.show()

    def open_data_base(self):
        if self.db_frame is None:
            self.db_frame = EventLocationFrame()
        self.db_frame.show()

    def info_message(self, msg, detailed_message=None):
        md = MessageDialog(self)
        md.set_info_message(msg, detailed_message)

    def on_click_select_file(self, bind: BindPyqtObject):
        selected = pw.QFileDialog.getOpenFileName(self, "Select metadata file")
        if isinstance(selected[0], str) and os.path.isfile(selected[0]):
            bind.value = selected[0]

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

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg))
    def onChange_metadata_path(self, value):

        try:
            self.__metadata_manager = MetadataManager(value)
            self.inventory: Inventory = self.__metadata_manager.get_inventory()
            print(self.inventory)
        except:
            raise FileNotFoundError("The metadata is not valid")

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

            file_to_store = open(os.path.join(path, self.nameForm.text()), "wb")
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

    @AsycTime.run_async()
    def send_phasenet(self):
        print("Starting Picking")

        phISP = PhasenetISP(self.project, modelpath=model_dir, amplitude=True)
        picks = phISP.phasenet()

        """ PHASENET OUTPUT TO REAL INPUT"""

        picks_ = Util.split_picks(picks)
        Util.save_original_picks(picks_)
        Util.convert2real(picks_)
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)

    def run_phasenet(self):

        if self.project is None:
            md = MessageDialog(self)
            md.set_error_message("Metadata run Picking, Please load a project first")
        else:
            self.send_phasenet()
            self.progress_dialog.exec()
            md = MessageDialog(self)
            md.set_info_message("Picking Done")


    def plot_real_grid(self):
        print("Work in progress")
        lon_min = self.lon_refMin.value()
        lon_max = self.lon_refMaxSB.value()
        lat_max = self.lat_refMaxSB.value()
        lat_min = self.lat_refMinSB.value()
        x = [lon_min, lon_max, lon_max, lon_min, lon_min]
        y = [lat_max, lat_max, lat_min, lat_min, lat_max]
        area = x + y
        network = obspy_utils.ObspyUtil.stationsCoodsFromMeta(self.inventory)
        plot_real_map(network, area=area)

    def plot_previewCatalog(self):
        print("plotting Preview")
        lon_min = self.lon_refMin.value()
        lon_max = self.lon_refMaxSB.value()
        lat_max = self.lat_refMaxSB.value()
        lat_min = self.lat_refMinSB.value()
        x = [lon_min, lon_max, lon_max, lon_min, lon_min]
        y = [lat_max, lat_max, lat_min, lat_min, lat_max]
        area = x + y
        network = obspy_utils.ObspyUtil.stationsCoodsFromMeta(self.inventory)
        plot_real_map(network, earthquakes=True, area=area)


    def get_real_grid(self):

        lon_min = self.lon_refMin.value()
        lon_max = self.lon_refMaxSB.value()
        lat_max = self.lat_refMaxSB.value()
        lat_min = self.lat_refMinSB.value()
        self.latitude_center = (lat_min + lat_max) / 2
        self.longitude_center = (lon_min + lon_max) / 2
        distance, az1, az2 = gps2dist_azimuth(self.latitude_center, self.longitude_center, lat_max, lon_max)
        self.h_range = kilometers2degrees(distance*0.001)
        # TODO A MAP with All available stations and the Grid
        #self.gridSearchParamHorizontalRangeBtn.setValue(self.h_range)

    def __get_lat_mean(self):

        lat_max = self.lat_refMaxSB.value()
        lat_min = self.lat_refMinSB.value()
        latitude_center = (lat_min + lat_max) / 2
        return latitude_center

    @AsycTime.run_async()
    def send_real(self):

        obspy_utils.ObspyUtil.realStation(self.inventory, station)
        # create travel times
        tt_db = create_tt_db()
        self.get_real_grid()
        tt_db.run_tt_db(dist=self.h_range, depth=self.depthSB.value(), ddist=0.01, ddep=1)
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
                                   gridSearchParamHorizontalRange=gridSearchParamHorizontalRange,
                                   HorizontalGridSize=HorizontalGridSize,
                                   DepthSearchParamHorizontalRange=DepthSearchParamHorizontalRange,
                                   DepthGridSize=DepthGridSize,
                                   EventTimeW=EventTimeW, TTHorizontalRange=TTHorizontalRange,
                                   TTHorizontalGridSize=TTHorizontalGridSize,
                                   TTDepthGridSize=TTDepthGridSize, TTDepthRange=TTDepthRange,
                                   ThresholdPwave=ThresholdPwave,
                                   ThresholdSwave=ThresholdSwave, number_stations_picks=number_stations_picks)

        real_handler.latitude_center = self.__get_lat_mean()
        print(real_handler.stations)

        ### Real Parameters ####

        for events_info in real_handler:
            print(events_info)
            print(events_info.events_date)

        real_handler.save()
        real_handler.compute_t_dist()
        ConversionUtils.real2nll(realout, nllinput)
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)

    def run_real(self):

        """ REAL """

        # create stations file
        #if isinstance(self.inventory, Inventory):
        if self.inventory is None:
            md = MessageDialog(self)
            md.set_error_message("Metadata couldn't be loaded")
        else:

            self.send_real()
            self.progress_dialog.exec()
            md = MessageDialog(self)
            md.set_info_message("Association Done")

    # def on_click_select_metadata_file(self):
    #     selected = pw.QFileDialog.getOpenFileName(self, "Select metadata/stations coordinates file")
    #     if isinstance(selected[0], str) and os.path.isfile(selected[0]):
    #         self.stationsPath.setText(selected[0])
    #         self.set_dataless_dir(self.stationsPath.text())

    #def set_dataless_dir(self, dir_path):
    #    self.__dataless_dir = dir_path
    #    self.nll_manager.set_dataless_dir(dir_path)

    @property
    def nll_manager(self):
        if not self.__nll_manager:
            self.__nll_manager = NllManager(self.__pick_output_path, self.__dataless_dir)
        return self.__nll_manager

    def set_dataless_dir(self):
        self.nll_manager.set_dataless(self.metadata_path_bind.value)
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


    ####### Automag ########

    def __modify_pred_config(self):

        self.config_automag["max_epi_dist"] = self.mag_max_distDB.value()

        if self.mag_max_distDB.value() < 700:
            self.config_automag["scale"] = "Regional"
        else:
            self.config_automag["scale"] = "Teleseism"

        self.config_automag["mag_vpweight"] = self.mag_vpweightDB.value()
        self.config_automag["rho"] = self.automag_density_DB.value()
        self.config_automag["automag_rpp"] = self.automag_rppDB.value()
        self.config_automag["automag_rps"] = self.automag_rpsDB.value()

        if self.r_power_nRB.isChecked():
            self.config_automag["geom_spread_model"] = "r_power_n"
        else:
            self.config_automag["geom_spread_model"] = "boatwright"
        self.config_automag["geom_spread_n_exponent"] = self.geom_spread_n_exponentDB.value()
        self.config_automag["geom_spread_cutoff_distance"] = self.geom_spread_cutoff_distanceDB.value()
        self.config_automag["a_local_magnitude"] = self.mag_aDB.value()
        self.config_automag["b_local_magnitude"] = self.mag_bDB.value()
        self.config_automag["c_local_magnitude"] = self.mag_cDB.value()
        self.config_automag["win_length"] = self.win_lengthDB.value()

    def __load_config_automag(self):
        try:
            self.config_automag = pd.read_pickle(magnitudes_config)
            self.__modify_pred_config()
        except:
            md = MessageDialog(self)
            md.set_error_message("Coundn't open magnitude config file")

    def mag_runBtn(self):
        self.__load_config_automag(magnitudes_config)

    def run_automag(self):
        self.automagnitudesText.clear()
        self.Date_Id = []
        self.lats = []
        self.longs = []
        self.depths = []
        self.Mw = []
        self.Mw_std = []
        self.ML = []
        self.ML_std = []
        self.__load_config_automag()
        mg = Automag(self.project, self.inventory)
        magnitude_mw_statistics_list, magnitude_ml_statistics_list, focal_parameters_list = (
            mg.estimate_magnitudes(self.config_automag))
        for magnitude_mw_statistics, magnitude_ml_statistics, focal_parameters in zip(magnitude_mw_statistics_list,
                                                            magnitude_ml_statistics_list, focal_parameters_list):
            self.print_automag_results(magnitude_mw_statistics, magnitude_ml_statistics, focal_parameters)

        self.save_magnitudes()
    def print_automag_results(self, magnitude_mw_statistics, magnitude_ml_statistics, focal_parameters):
        self.automagnitudesText.appendPlainText("#####################################################")
        self.automagnitudesText.appendPlainText(focal_parameters[0].strftime(format="%m/%d/%Y, %H:%M:%S")+ "    "+str(focal_parameters[1])+
            "º    "+ str(focal_parameters[2])+"º    "+ str(focal_parameters[3])+" km")

        #self.Date_Id.append(focal_parameters[0].strftime(format="%Y%m%d%H%M%S"))
        self.Date_Id.append(focal_parameters[0].strftime('%m/%d/%Y, %H:%M:%S.%f'))
        self.lats.append(focal_parameters[1])
        self.longs.append(focal_parameters[2])
        self.depths.append(focal_parameters[3])

        if magnitude_mw_statistics != None:
            Mw = magnitude_mw_statistics.summary_spectral_parameters.Mw.weighted_mean.value
            Mw_std = magnitude_mw_statistics.summary_spectral_parameters.Mw.weighted_mean.uncertainty

            Mo = magnitude_mw_statistics.summary_spectral_parameters.Mo.mean.value
            Mo_units = magnitude_mw_statistics.summary_spectral_parameters.Mo.units

            fc = magnitude_mw_statistics.summary_spectral_parameters.fc.weighted_mean.value
            fc_units = "Hz"

            t_star = magnitude_mw_statistics.summary_spectral_parameters.t_star.weighted_mean.value
            t_star_std = magnitude_mw_statistics.summary_spectral_parameters.t_star.weighted_mean.uncertainty
            t_star_units = magnitude_mw_statistics.summary_spectral_parameters.t_star.units

            source_radius = magnitude_mw_statistics.summary_spectral_parameters.radius.mean.value
            radius_units = magnitude_mw_statistics.summary_spectral_parameters.radius.units

            bsd = magnitude_mw_statistics.summary_spectral_parameters.bsd.mean.value
            bsd_units = magnitude_mw_statistics.summary_spectral_parameters.bsd.units

            Qo =  magnitude_mw_statistics.summary_spectral_parameters.Qo.mean.value
            Qo_std = magnitude_mw_statistics.summary_spectral_parameters.Qo.mean.uncertainty
            Qo_units = magnitude_mw_statistics.summary_spectral_parameters.Qo.units

            Er = magnitude_mw_statistics.summary_spectral_parameters.Er.mean.value
            Er_units = "jul"

            self.Mw.append("{:.2f}".format(Mw))
            self.Mw_std.append("{:.2f}".format(Mw_std))

            self.automagnitudesText.appendPlainText("Moment Magnitude: " " Mw {Mw:.3f} "
                                                    " std {std:.3f} ".format(Mw=Mw, std=Mw_std))

            self.automagnitudesText.appendPlainText("Seismic Moment and Source radius: " " Mo {Mo:e} Nm"
                                                    ", R {std:.3f} km".format(Mo=Mo, std=source_radius / 1000))

            self.automagnitudesText.appendPlainText("Brune stress Drop: " "{bsd:.3f} MPa".format(bsd=bsd))

            self.automagnitudesText.appendPlainText(
                "Quality factor: " " Qo {Qo:.3f} " " Q_std {Qo_std:.3f} ".format(Qo=Qo, Qo_std=Qo_std))

            self.automagnitudesText.appendPlainText(
                "t_star: " "{t_star:.3f} s" " t_star_std {t_star_std:.3f} ".format(t_star=t_star,
                                                                                   t_star_std=t_star_std))

        else:
            self.automagnitudesText.appendPlainText("Mw cannot be estimated")
            self.Mw.append("None")
            self.Mw_std.append("None")

        if magnitude_ml_statistics != None:
            ML = magnitude_ml_statistics[0]
            ML_std = magnitude_ml_statistics[1]
            self.ML.append("{:.2f}".format(ML))
            self.ML_std.append("{:.2f}".format(ML_std))
            self.automagnitudesText.appendPlainText("Local Magnitude: " " ML {ML:.3f} "
                                                    " ML_std {std:.3f} ".format(ML=ML, std=ML_std))

        else:
            self.automagnitudesText.appendPlainText("ML cannot be estimated")
            self.ML.append("None")
            self.ML_std.append("None")

    def save_magnitudes(self):
        magnitudes_dict = {'date_id': self.Date_Id, 'lats': self.lats, 'longs': self.longs, 'depths': self.depths,
        'Mw': self.Mw, 'Mw_error': self.Mw_std,'ML': self.ML, 'ML_error': self.ML_std}
        df_magnitudes = pd.DataFrame.from_dict(magnitudes_dict)
        df_magnitudes.to_csv(magnitudes, sep=";", index=False)

    ########## Moment Tensor Inversion #######################

    def get_db(self):
        db = self.db_frame.get_entities()
        return db

    def get_model(self):
        # returns the database
        model = self.db_frame.get_model()
        return model

    def get_inversion_parameters(self):

        parameters = {'working_directory': self.mti_working_path.text(), 'output_directory': self.MTI_output_path.text(),
                      'earth_model': self.earth_model_path.text(), 'location_unc': self.HorizontalLocUncertainityMTIDB.value(),
                      'time_unc': self.timeUncertainityMTIDB.value(), 'depth_unc': self.depthUncertainityMTIDB.value(),
                      'deviatoric': self.deviatoricCB.isChecked(), 'covariance': self.covarianceCB.isChecked(),
                      'plot_save': self.savePlotsCB.isChecked(), 'rupture_velocity': self.ruptureVelMTIDB.value(),
                      'source_type': self.sourceTypeCB.currentText(), 'min_dist': self.minDistMTIDB.value(),
                      'max_dist': self.maxDistMTIDB.value(), 'fmin': self.freq_minMTI.value(),
                      'fmax': self.freq_maxMTI.value(), 'rms_thresh': self.rms_threshMTI.value(),
                      'max_num_stationsMTI0': self.max_num_stationsMTI.value()}

        return parameters

    def run_mti(self):
        macroMTI = self.parameters.getParameters()
        parametersGUI = self.get_inversion_parameters()
        sq_bayesian = bayesian_isola_db(model=self.get_model(), entities=self.get_db(), metadata=self.inventory,
                                        project=self.project, parameters=parametersGUI, macro=macroMTI)
        sq_bayesian.run_inversion()