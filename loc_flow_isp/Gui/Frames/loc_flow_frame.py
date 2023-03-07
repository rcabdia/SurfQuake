import os
import pickle
from loc_flow_isp import ROOT_DIR, model_dir, p_dir, station, ttime
from loc_flow_isp.Gui.Frames.qt_components import MessageDialog
from loc_flow_isp.Gui.Frames.uis_frames import UiLoc_Flow
from PyQt5 import QtWidgets, QtGui, QtCore
from loc_flow_isp.Gui.Utils.pyqt_utils import BindPyqtObject
from sys import platform
from concurrent.futures.thread import ThreadPoolExecutor
from loc_flow_isp.Utils.obspy_utils import MseedUtil
from loc_flow_isp.loc_flow_tools.internal.real_manager import RealManager
from loc_flow_isp.loc_flow_tools.phasenet.phasenet_handler import Util
from loc_flow_isp.loc_flow_tools.phasenet.phasenet_handler import PhasenetISP

#from PyQt5.QtCore import pyqtSlot

pw = QtWidgets
pqg = QtGui
pyc = QtCore

class LocFlow(pw.QMainWindow, UiLoc_Flow):

    def __init__(self):
        super(LocFlow, self).__init__()
        self.setupUi(self)

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

    # @pyc.Slot()
    # def _increase_progress(self):
    #      self.progressbar.setValue(self.progressbar.value() + 1)

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

    def run_real(self):
        """ REAL """
        # TODO BUILD TTDB
        real_handler = RealManager(pick_dir=p_dir, station_file=station, time_travel_table_file=ttime)
        # real_handler.latitude_center = 36.19#36.1 #42.75

        # print(real_handler.stations)

        # for events_info in real_handler:
        #    print(events_info)
        #    print(events_info.events_date)

        # real_handler.save()
        # real_handler.compute_t_dist()

        #convert.real2nll(realout, nllinput)

