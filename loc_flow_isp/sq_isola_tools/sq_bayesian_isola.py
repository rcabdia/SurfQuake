from obspy import UTCDateTime, Stream
from loc_flow_isp.DataProcessing import SeismogramDataAdvanced
from loc_flow_isp.Gui.Frames.qt_components import MessageDialog
from loc_flow_isp.Utils.obspy_utils import MseedUtil
from loc_flow_isp.sq_isola_tools.mti_utilities import MTIManager


class bayesian_isola_db:
    def __init__(self, model, entities, metadata: dict, project: dict, parameters: dict, macro: dict):

        """
        ----------
        Parameters
        ----------
        metadata dict: information of stations
        project dict: information of seismogram data files available
        parameters: dictionary containing database entities and all GUI parameters
        """
        self.model = model
        self.entities = entities
        self.metadata = metadata
        self.project = project
        self.parameters = parameters
        self.macro = macro

    def get_now_files(self, date, pick_time, stations_list):
        date = UTCDateTime(date)
        pick_time = UTCDateTime(pick_time)
        selection = [".", stations_list, "."]

        _, self.files_path = MseedUtil.filter_project_keys(self.project, net=selection[0], station=selection[1],
                                                       channel=selection[2])
        start = date - 1300 #half and hour before
        end = pick_time + 2*3600 #end 2 hours after
        files_path = MseedUtil.filter_time(list_files=self.files_path, starttime=start, endtime=end)
        return files_path

    def get_stations_list(self, phase_info):
        # TODO NEEDS TO FILTER PROJECT BASED minimum and maximum distance
        #  #needs distances in phase data_base
        pick_times = []
        stations_list = []
        for phase in phase_info:
            stations_list.append(phase.station_code)
            pick_times.append(phase.time)
        station_filter = '|'.join(stations_list)
        max_time = max(pick_times)
        return station_filter, max_time
    def get_info(self):
        for j in self.entities:
            event_info = self.model.find_by(id=j[0].id, get_first=True)
            phase_info = event_info.phase_info
            origin_time = event_info.origin_time
            print(event_info)
            #print(phase_info)
            station_filter, max_time = self.get_stations_list(phase_info)
            files_path = self.get_now_files(origin_time, max_time, station_filter)
            #self.process_data(files_path, origin_time, max_time)
            #self.invert()
    def filter_error_message(self, msg):
        md = MessageDialog(self)
        md.set_info_message(msg)

    def process_data(self, files_path, date, pick_time):
        date = UTCDateTime(date) - 60
        pick_time = UTCDateTime(pick_time) + 2*60
        all_traces = []
        for file in files_path:
            sd = SeismogramDataAdvanced(file)
            tr = sd.get_waveform_advanced(self.macro, self.metadata, start_time=date, end_time=pick_time,
                                          filter_error_callback=self.filter_error_message)
            all_traces.append(tr)

        self.st = Stream(traces=all_traces)
        #self.st.plot()

    def invert(self, event_info):
        mt = MTIManager(self.st, self.metadata, event_info.latitude, event_info.longitude, 0.0, 0.0)
        [st, deltas, stations_isola_path] = mt.get_stations_index()
        # inputs = BayesISOLA.load_data(outdir=self.parameters['output_directory'])
        # inputs.set_event_info(lat=event_info.latitude, lon=event_info.longitude, depth=(event_info.depth/1000),
        # mag=event_info.mw, t=UTCDateTime(event_info.origin_time))
        # inputs.set_source_time_function('triangle', 2.0)
        # inputs.read_network_coordinates(
        #     stations_isola_path)  # changed stn['useN'] = stn['useE'] = stn['useZ'] = False to True
        # inputs.read_crust(crust_model_path)
        # inputs.write_stations()
        # # inputs.load_files(paz_path, separator='', pz_dir=pz_dir, pz_separator='', pz_suffix='.pz')
        # inputs.data_raw = st
        # inputs.create_station_index()
        # inputs.data_deltas = deltas
        # print("end")
        # grid = BayesISOLA.grid(
        #     inputs,
        #     location_unc=3000,  # m
        #     depth_unc=3000,  # m
        #     time_unc=1,  # s
        #     step_x=200,  # m
        #     step_z=200,  # m
        #     max_points=500,
        #     circle_shape=True,
        #     rupture_velocity=1000  # m/s
        # )
        # data = BayesISOLA.process_data(
        #     inputs,
        #     grid,
        #     threads=8,
        #     use_precalculated_Green="auto",
        #     fmax=0.04,
        #     fmin=0.08,
        #     correct_data=False
        # )
        #
        # cova = BayesISOLA.covariance_matrix(data)
        # cova.covariance_matrix_noise(crosscovariance=True, save_non_inverted=True)
        #
        # solution = BayesISOLA.resolve_MT(data, cova, deviatoric=False)
        # # deviatoric=True: force isotropic component to be zero
        #
        # plot = BayesISOLA.plot(solution)
        # plot.html_log(h1='Example_Test')
