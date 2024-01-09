import os
from surfquakecore.earthquake_location.structures import NLLConfig, GridConfiguration, TravelTimesConfiguration, \
    LocationParameters
from surfquakecore.magnitudes.source_tools import ReadSource
from surfquakecore.moment_tensor.sq_isola_tools import BayesianIsolaCore
from surfquakecore.real.real_core import RealCore
from surfquakecore.real.structures import RealConfig, GeographicFrame, GridSearch, TravelTimeGridSearch, ThresholdPicks
from surfquake import ROOT_DIR, p_dir, nllinput, \
    real_working_dir, real_output_data, source_config
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
from surfquake.Gui.Frames.event_location_frame import EventLocationFrame
from surfquake.Gui.Frames.parameters import ParametersSettings
from obspy.core.inventory.inventory import Inventory
from surfquake.Utils.time_utils import AsycTime
from surfquake.maps.plot_map import plot_real_map
from surfquake.sq_isola_tools.sq_bayesian_isola_core import BayesianIsolaGUICore
from surfquakecore.project.surf_project import SurfProject
from surfquakecore.phasenet.phasenet_handler import PhasenetUtils
from surfquakecore.phasenet.phasenet_handler import PhasenetISP
from surfquakecore.utils.obspy_utils import MseedUtil
from surfquakecore.earthquake_location.run_nll import Nllcatalog, NllManager
from surfquakecore.magnitudes.run_magnitudes import Automag

pw = QtWidgets
pqg = QtGui
pyc = QtCore


@add_save_load()
class LocFlow(BaseFrame, UiLoc_Flow):

    def __init__(self):
        super(LocFlow, self).__init__()
        self.setupUi(self)
        self.setWindowTitle('surfQuake')
        self.__pick_output_path = nllinput
        self.__dataless_dir = None
        self.__nll_manager = None
        self.db_frame = None
        self.latitude_center = None
        self.longitude_center = None
        self.h_range = None
        self.inventory = None
        self.project = None
        self.config_automag = {}
        self.parameters = ParametersSettings()

        ####### Metadata ##########
        self.metadata_path_bind = BindPyqtObject(self.datalessPathForm)
        self.setMetaBtn.clicked.connect(lambda: self.on_click_select_file(self.metadata_path_bind))
        self.loadMetaBtn.clicked.connect(lambda: self.onChange_metadata_path(self.metadata_path_bind.value))

        ####### Project ###########

        self.progressbar = pw.QProgressDialog(self)
        self.progressbar.setLabelText("Computing Project ")
        self.progressbar.setWindowIcon(pqg.QIcon(':/icons/icon.png'))
        self.progressbar.close()
        self.root_path_bind = BindPyqtObject(self.rootPathForm, self.onChange_root_path)
        self.pathFilesBtn.clicked.connect(lambda: self.on_click_select_directory(self.root_path_bind))
        self.loadProjectBtn.clicked.connect(lambda: self.load_project())
        self.openProjectBtn.clicked.connect(lambda: self.openProject())
        self.saveBtn.clicked.connect(lambda: self.saveProject())
        self.regularBtn.clicked.connect(lambda: self.load_files())
        self.phasenetBtn.clicked.connect(self.run_phasenet)
        self.realBtn.clicked.connect(self.run_real)
        self.plot_grid_stationsBtn.clicked.connect(self.plot_real_grid)

        ############# Phasent -Picking ##############
        self.picking_bind = BindPyqtObject(self.picking_LE, self.onChange_root_path)
        self.output_path_pickBtn.clicked.connect(lambda: self.on_click_select_directory(self.picking_bind))

        ############ REAL ###########################
        self.real_bind = BindPyqtObject(self.real_inputLE, self.onChange_root_path)
        self.real_picking_inputBtn.clicked.connect(lambda: self.on_click_select_directory(self.real_bind))
        self.real_output_bind = BindPyqtObject(self.output_realLE, self.onChange_root_path)
        self.output_realBtn.clicked.connect(lambda: self.on_click_select_directory(self.real_output_bind))

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
        self.loc_work_bind = BindPyqtObject(self.loc_workLE)
        self.loc_work_dirBtn.clicked.connect(lambda: self.on_click_select_directory(self.loc_work_bind))
        self.model_path_bind = BindPyqtObject(self.modelLE, self.onChange_root_path)
        self.modelPathBtn.clicked.connect(lambda: self.on_click_select_directory(self.model_path_bind))
        self.picks_path_bind = BindPyqtObject(self.picksLE, self.onChange_root_path)
        self.picksBtn.clicked.connect(lambda: self.on_click_select_file(self.picks_path_bind))
        self.genvelBtn.clicked.connect(lambda: self.on_click_run_vel_to_grid())
        self.grdtimeBtn.clicked.connect(lambda: self.on_click_run_grid_to_time())
        self.runlocBtn.clicked.connect(lambda: self.on_click_run_loc())
        # self.plotmapBtn.clicked.connect(lambda: self.on_click_plot_map())
        # self.stationsBtn.clicked.connect(lambda: self.on_click_select_metadata_file())
        self.actionData_Base.triggered.connect(lambda: self.open_data_base())

        # Magnitude
        self.source_locs_bind = BindPyqtObject(self.source_locsLE)
        self.setLocFolderBtn.clicked.connect(lambda: self.on_click_select_directory(self.source_locs_bind))

        self.source_out_bind = BindPyqtObject(self.source_outLE)
        self.setSourceOutBtn.clicked.connect(lambda: self.on_click_select_directory(self.source_out_bind))
        self.mag_runBtn.clicked.connect(lambda: self.run_automag())
        self.printSourceResultsBtn.clicked.connect(lambda: self.print_source_results())

        # MTI
        self.mti_path_bind = BindPyqtObject(self.mti_working_path, self.onChange_root_path)
        self.earth_model_bind = BindPyqtObject(self.earth_model_path, self.onChange_root_path)
        self.workingDirectoryMTIBtn.clicked.connect(lambda: self.on_click_select_directory(self.mti_path_bind))
        self.earthModelMTIBtn.clicked.connect(lambda: self.on_click_select_file(self.earth_model_bind))
        self.mti_output_path_bind = BindPyqtObject(self.MTI_output_path, self.onChange_root_path)
        self.outputDirectoryMTIBtn.clicked.connect(lambda: self.on_click_select_directory(self.mti_output_path_bind))
        #self.macroMITBtn.clicked.connect(lambda: self.open_parameters_settings())
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
        selected = pw.QFileDialog.getOpenFileName(self, "Select file")
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

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg,
                                                              False))  # When launch, metadata path need show messsage to False.
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
                self.sp = SurfProject.load_project(self.current_project_file)
                self.project = self.sp.project
                md.set_info_message("Project {} loaded  ".format(self.current_project_file))
            except:
                md.set_error_message("Project couldn't be loaded ")
        else:
            md.set_error_message("Project couldn't be loaded ")

    def load_files(self):

        if self.rootPathForm_inv.text() == "":
            filter = "All files (*.*)"
        else:

            filter = self.rootPathForm_inv.text()

        selected_files, _ = pw.QFileDialog.getOpenFileNames(self, "Select Project", ROOT_DIR, filter=filter)

        md = MessageDialog(self)
        md.hide()

        try:
            self.sp = SurfProject(selected_files)
            self.progressbar.reset()
            self.progressbar.setLabelText("Bulding Project")
            self.progressbar.setRange(0, 0)

            def callback():
                self.sp.search_files(verbose=True)
                r = self.sp.project
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


    def _select_directory(self, bind: BindPyqtObject):

        if "darwin" == platform:
            dir_path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', bind.value)
        else:
            dir_path = pw.QFileDialog.getExistingDirectory(self, 'Select Directory', bind.value,
                                                           pw.QFileDialog.DontUseNativeDialog)
        return dir_path

    def on_click_select_directory(self, bind: BindPyqtObject):
        dir_path = self._select_directory(bind)
        if dir_path:
            bind.value = dir_path

    def openProject(self):

        md = MessageDialog(self)
        md.hide()
        try:
            self.sp = SurfProject(self.root_path_bind.value)
            self.progressbar.reset()
            self.progressbar.setLabelText("Bulding Project")
            self.progressbar.setRange(0, 0)

            def callback():
                self.sp.search_files(verbose=True)
                r = self.sp.project
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
            dir_path = self._select_directory(self.root_path_bind)
            if not dir_path:
                return
            dir_path = os.path.join(dir_path, self.nameForm.text())
            if self.sp.save_project(dir_path) == True:
                MessageDialog(self).set_info_message("Succesfully saved project")
            else:
                MessageDialog(self).set_error_message("Error saving project")
        except:
            MessageDialog(self).set_error_message("No data to save in Project")

    @AsycTime.run_async()
    def send_phasenet(self):
        print("Starting Picking")

        phISP = PhasenetISP(self.sp.project, amplitude=True, min_p_prob=self.p_wave_picking_thresholdDB.value(),
                            min_s_prob=self.s_wave_picking_thresholdDB.value())

        picks = phISP.phasenet()
        picks_ = PhasenetUtils.split_picks(picks)

        PhasenetUtils.convert2real(picks_, self.picking_bind.value)
        PhasenetUtils.save_original_picks(picks_, self.picking_bind.value)

        """ PHASENET OUTPUT TO REAL INPUT"""
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)

    def run_phasenet(self):

        if self.sp.project is None:
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

    def run_real(self):

        """ REAL """
        if self.inventory is None:
            md = MessageDialog(self)
            md.set_error_message("Metadata couldn't be loaded")
        else:
            self.send_real()
            self.progress_dialog.exec()
            md = MessageDialog(self)
            md.set_info_message("Association Done")

    @AsycTime.run_async()
    def send_real(self):

        real_config = RealConfig(
            geographic_frame=GeographicFrame(
                lat_ref_max=self.lat_refMaxSB.value(),
                lon_ref_max=self.lon_refMaxSB.value(),
                lat_ref_min=self.lat_refMinSB.value(),
                lon_ref_min=self.lon_refMin.value(),
                depth=self.depthSB.value()
            ),
            grid_search_parameters=GridSearch(
                horizontal_search_range=self.gridSearchParamHorizontalRangeBtn.value(),
                depth_search_range=self.DepthSearchParamHorizontalRangeBtn.value(),
                event_time_window=self.EventTimeWindow.value(),
                horizontal_search_grid_size=self.HorizontalGridSizeBtn.value(),
                depth_search_grid_size=self.DepthGridSizeBtn.value()),
            travel_time_grid_search=TravelTimeGridSearch(
                horizontal_range=self.TTHorizontalRangeBtn.value(),
                depth_range=self.TTDepthRangeBtn.value(),
                depth_grid_resolution_size=self.TTDepthGridSizeBtn.value(),
                horizontal_grid_resolution_size=self.TTHorizontalGridSizeBtn.value()),
            threshold_picks=ThresholdPicks(
                min_num_p_wave_picks=self.ThresholdPwaveSB.value(),
                min_num_s_wave_picks=self.ThresholdSwaveSB.value(),
                num_stations_recorded=self.number_stations_picksSB.value())
        )

        rc = RealCore(self.metadata_path_bind.value, real_config, self.real_bind.value, real_working_dir,
                      self.real_output_bind.value)
        rc.run_real()
        print("End of Events AssociationProcess, please see for results: ", real_output_data)
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)

    def get_nll_config(self):

        if self.loc_wavetypeCB.currentText() == "P & S":
            p_wave_type = True
            s_wave_type = True
        else:
            p_wave_type = True
            s_wave_type = True

        if self.loc_modelCB.currentText() == "1D":
            path_model1D = self.model_path_bind.value
            path_model3D = "NONE"
        else:
            path_model1D = "NONE"
            path_model3D = self.picks_path_bind.value

        nllconfig = NLLConfig(
            grid_configuration=GridConfiguration(
                latitude=self.grid_latitude_bind.value,
                longitude=self.grid_longitude_bind.value,
                depth=self.grid_depth_bind.value,
                x=self.grid_xnode_bind.value,
                y=self.grid_ynode_bind.value,
                z=self.grid_znode_bind.value,
                dx=self.grid_dxsize_bind.value,
                dy=self.grid_dysize_bind.value,
                dz=self.grid_dzsize_bind.value,
                geo_transformation=self.transCB.currentText(),
                grid_type=self.gridtype.currentText(),
                path_to_1d_model=path_model1D,
                path_to_3d_model=path_model3D,
                path_to_picks=self.picks_path_bind.value,
                p_wave_type=p_wave_type,
                s_wave_type=s_wave_type,
                model=self.loc_modelCB.currentText()),
            travel_times_configuration=TravelTimesConfiguration(
                distance_limit=self.distanceSB.value(),
                grid=self.grid_typeCB.currentText()[4:6]),
            location_parameters=LocationParameters(
                search=self.loc_searchCB.currentText(),
                method=self.loc_methodCB.currentText()))

        return nllconfig

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg))
    def on_click_run_vel_to_grid(self):
        nllconfig = self.get_nll_config()
        if isinstance(nllconfig, NLLConfig):
            nll_manager = NllManager(nllconfig, self.metadata_path_bind.value, self.loc_work_bind.value)
            nll_manager.vel_to_grid()

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg))
    def on_click_run_grid_to_time(self):
        nllconfig = self.get_nll_config()
        if isinstance(nllconfig, NLLConfig):
            nll_manager = NllManager(nllconfig, self.metadata_path_bind.value, self.loc_work_bind.value)
            nll_manager.grid_to_time()

    @parse_excepts(lambda self, msg: self.subprocess_feedback(msg, set_default_complete=False))
    def on_click_run_loc(self):
        nllconfig = self.get_nll_config()
        if isinstance(nllconfig, NLLConfig):
            nll_manager = NllManager(nllconfig, self.metadata_path_bind.value, self.loc_work_bind.value)
            nll_manager.run_nlloc()
            nll_catalog = Nllcatalog(self.loc_work_bind.value)
            nll_catalog.run_catalog(self.loc_work_bind.value)

    ####### Source Parameters ########

    def run_automag(self):
        self.__send_run_automag()
        self.progress_dialog.exec()
        md = MessageDialog(self)
        md.set_info_message("Source Parameters estimation finished, Please see output directory and press "
                            "print results")

    @AsycTime.run_async()
    def __send_run_automag(self):

        self.__load_config_automag()
        # Running stage
        mg = Automag(self.sp, self.source_locs_bind.value, self.metadata_path_bind.value, source_config,
                     self.source_out_bind.value, scale="regional", gui_mod=self.config_automag)
        print("Estimating Source Parameters")
        mg.estimate_source_parameters()

        # write a txt summarizing the results
        rs = ReadSource(self.source_out_bind.value)
        summary = rs.generate_source_summary()
        summary_path = os.path.join(self.source_out_bind.value, "source_summary.txt")
        rs.write_summary(summary, summary_path)
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)


    def __load_config_automag(self):
        self.config_automag['epi_dist_ranges'] = [0, self.mag_max_distDB.value()]
        self.config_automag['p_arrival_tolerance'] = self.p_tolDB.value()
        self.config_automag['s_arrival_tolerance'] = self.s_tolDB.value()
        self.config_automag['noise_pre_time'] = self.noise_windowDB.value()
        self.config_automag['win_length'] = self.signal_windowDB.value()
        self.config_automag['spectral_win_length'] = self.spec_windowSB.value()
        self.config_automag['rho_source'] = self.automag_density_DB.value()
        self.config_automag['rpp'] = self.automag_rppDB.value()
        self.config_automag['rps'] = self.automag_rpsDB.value()

        if self.r_power_nRB.isChecked():
            self.config_automag['geom_spread_model'] = "r_power_n"
        else:
            self.config_automag['geom_spread_model'] = "boatwright"

        self.config_automag['geom_spread_n_exponent'] = self.geom_spread_n_exponentDB.value()
        self.config_automag['geom_spread_cutoff_distance'] = self.geom_spread_cutoff_distanceDB.value()

        self.config_automag['a'] = self.mag_aDB.value()
        self.config_automag['b'] = self.mag_bDB.value()
        self.config_automag['c'] = self.mag_cDB.value()
        print("Loaded Source Config from GUI")


    def print_source_results(self):
        import pandas as pd
        import math
        summary_path = os.path.join(self.source_out_bind.value, "source_summary.txt")
        df = pd.read_csv(summary_path, sep=";", na_values='missing')

        for index, row in df.iterrows():
            self.automagnitudesText.appendPlainText("#####################################################")
            date = row['date_id']
            lat = str(row['lats'])
            lon = str(row['longs'])
            depth = str(row['depths'])
            if not math.isnan(row['Mw']):
                Mw = str("{: .2f}".format(row['Mw']))
            else:
                Mw = row['Mw']

            if not math.isnan(row['Mw_error']):
                Mw_std = str("{: .2f}".format(row['Mw_error']))
            else:
                Mw_std = row['Mw_error']

            if not math.isnan(row['Mo']):
                Mo = str("{: .2e}".format(row['Mo']))
            else:
                Mo = row['Mo']

            if not math.isnan(row['radius']):
                source_radius = str("{: .2f}".format(row['radius']))
            else:
                source_radius = row['radius']

            if not math.isnan(row['ML']):
                ML = str("{: .2f}".format(row['ML']))
            else:
                ML = row['ML']

            if not math.isnan(row['ML_error']):
                ML_std = str("{: .2f}".format(row['ML_error']))
            else:
                ML_std = row['ML_error']

            if not math.isnan(row['bsd']):
                bsd = str("{: .2f}".format(row['bsd']))
            else:
                bsd = row['bsd']

            if not math.isnan(row['Er']):
                Er = str("{: .2e}".format(row['Er']))
            else:
                Er = row['Er']

            if not math.isnan(row['Er_std']):
                Er_std = str("{: .2e}".format(row['Er_std']))
            else:
                Er_std = row['Er']

            if not math.isnan(row['fc']):
                fc = str("{: .2f}".format(row['fc']))
            else:
                fc = row['fc']

            if not math.isnan(row['fc_std']):
                fc_std = str("{: .2f}".format(row['fc_std']))
            else:
                fc_std = row['fc']

            if not math.isnan(row['Qo']):
                Qo = str("{: .2f}".format(row['Qo']))
            else:
                Qo = row['Qo']

            if not math.isnan(row['Qo_std']):
                Qo_std = str("{: .2f}".format(row['Qo_std']))
            else:
                Qo_std = row['Qo_std']

            if not math.isnan(row['t_star']):
                t_star = str("{: .2f}".format(row['t_star']))
            else:
                t_star = row['t_star']

            if not math.isnan(row['t_star_std']):
                t_star_std = str("{: .2f}".format(row['t_star_std']))
            else:
                t_star_std = row['t_star_std']


            self.automagnitudesText.appendPlainText(date + "    " + lat +"º    "+ lon+"º    "+ depth+" km")
            self.automagnitudesText.appendPlainText("Moment Magnitude: " " Mw {Mw} "
                                                             " std {std} ".format(Mw=Mw, std=Mw_std))

            self.automagnitudesText.appendPlainText("Seismic Moment and Source radius: " " Mo {Mo:} Nm"
                                                              ", R {std} km".format(Mo=Mo, std=source_radius))

            self.automagnitudesText.appendPlainText("Local Magnitude: " " ML {ML} "
                                                    " std {std} ".format(ML=ML, std=ML_std))

            self.automagnitudesText.appendPlainText("Brune stress Drop: " "{bsd} MPa".format(bsd=bsd))

            self.automagnitudesText.appendPlainText(
                 "Seismic Energy: " " Er {Er} juls" " Er_std {Er_std} ".format(Er=Er, Er_std=Er_std))

            self.automagnitudesText.appendPlainText(
                 "Corner Frequency: " " fc {fc} Hz" " fc_std {fc_std} ".format(fc=fc, fc_std=fc_std))

            self.automagnitudesText.appendPlainText(
                          "Quality factor: " " Qo {Qo} " " Q_std {Qo_std} ".format(Qo=Qo, Qo_std=Qo_std))

            self.automagnitudesText.appendPlainText(
                          "t_star: " "{t_star} s" " t_star_std {t_star_std} ".format(t_star=t_star,
                                                                                             t_star_std=t_star_std))


    ########## Moment Tensor Inversion #######################

    def get_db(self):
        db = self.db_frame.get_entities()
        return db

    def get_model(self):
        # returns the database
        model = self.db_frame.get_model()
        return model

    def get_inversion_parameters(self):

        parameters = {'working_directory': self.mti_working_path.text(),
                      'output_directory': self.MTI_output_path.text(),
                      'earth_model': self.earth_model_path.text(),
                      'location_unc': self.HorizontalLocUncertainityMTIDB.value(),
                      'time_unc': self.timeUncertainityMTIDB.value(), 'depth_unc': self.depthUncertainityMTIDB.value(),
                      'deviatoric': self.deviatoricCB.isChecked(), 'covariance': self.covarianceCB.isChecked(),
                      'plot_save': self.savePlotsCB.isChecked(), 'rupture_velocity': self.ruptureVelMTIDB.value(),
                      'source_type': self.sourceTypeCB.currentText(), 'min_dist': self.minDistMTIDB.value(),
                      'max_dist': self.maxDistMTIDB.value(), 'fmin': self.freq_minMTI.value(),
                      'fmax': self.freq_maxMTI.value(), 'rms_thresh': self.rms_threshMTI.value(),
                      'max_num_stationsMTI0': self.max_num_stationsMTI.value(),
                      'source_duration': self.sourceTypeLenthgMTIDB.value()}

        return parameters

    def run_mti(self):
        self.__send_run_mti()
        self.progress_dialog.exec()
        md = MessageDialog(self)
        md.set_info_message("Moment Tensor Inversion finished, Please see output directory and press "
                            "print results")

    @AsycTime.run_async()
    def __send_run_mti(self):
        # macroMTI = self.parameters.getParameters()
        #parameters = self.get_inversion_parameters()
        # sq_bayesian = bayesian_isola_db(model=self.get_model(), entities=self.get_db(), metadata=self.inventory,
        #                                 project=self.project, parameters=parametersGUI, macro=macroMTI)
        #sq_bayesian.run_inversion()

        ### from surfquakecore ###
        parameters =self.get_inversion_parameters()
        bic = BayesianIsolaCore(project=self.project, inventory_file=self.metadata_path_bind.value,
                                output_directory=self.MTI_output_path.text(),
                                save_plots=parameters['plot_save'])
        bic.working_directory = self.mti_working_path.text()
        bi = BayesianIsolaGUICore(bic, model=self.get_model(), entities=self.get_db(),
                                  parameters=parameters)
        bi.run_inversion()
        pyc.QMetaObject.invokeMethod(self.progress_dialog, 'accept', Qt.Qt.QueuedConnection)
        #########################
