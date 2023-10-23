import os
from obspy import UTCDateTime, Stream
from surfquake.DataProcessing import SeismogramDataAdvanced
from surfquake.Gui.Frames.qt_components import MessageDialog
from surfquake.Utils.obspy_utils import MseedUtil
from surfquake.seismogramInspector.signal_processing_advanced import duration
from surfquake.sq_isola_tools import BayesISOLA
from surfquake.sq_isola_tools.mti_utilities import MTIManager


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
        self.cpuCount = os.cpu_count() - 1

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

        pick_times = []
        stations_list = []
        for phase in phase_info:
            if phase.time_weight >= 0.9 and abs(phase.time_residual) <= 3.5:
                stations_list.append(phase.station_code)
                pick_times.append(phase.time)
        station_filter = '|'.join(stations_list)
        max_time = max(pick_times)
        return station_filter, max_time

    def run_inversion(self):
        for (i, entity) in enumerate(self.entities):

            event_info = self.model.find_by(latitude=entity[0].latitude, longitude=entity[0].longitude,
                        depth=entity[0].depth, origin_time=entity[0].origin_time)
            phase_info = event_info.phase_info
            origin_time = event_info.origin_time
            print(event_info)
            #print(phase_info)
            station_filter, max_time = self.get_stations_list(phase_info)
            files_path = self.get_now_files(origin_time, max_time, station_filter)

            # TODO: TAKE CARE WITH TYPE OF MAGNITUDE
            try:
                self.process_data(files_path, origin_time, entity[0].transformation, str(i), pick_time=max_time,
                                  magnitude=event_info.mw, save_stream_plot=True)
            except:
                self.process_data(files_path, origin_time, entity[0].transformation, str(i))

            self.invert(event_info, i)

    def filter_error_message(self, msg):
        md = MessageDialog(self)
        md.set_info_message(msg)

    def process_data(self, files_path, date, transform, ID_folder,  **kwargs):

        all_traces = []
        date = UTCDateTime(date)
        pick_time = kwargs.pop('pick_time', None)
        magnitude = kwargs.pop('magnitude', None)
        save_stream_plot = kwargs.pop('save_stream_plot', True)

        if pick_time is not None:
            pick_time = UTCDateTime(pick_time)
            delta_min = pick_time - date
            if delta_min <= 240:
                start_time = date - (240/3)
                end_time = pick_time + 240
            else:
                if pick_time != None and magnitude != None:
                    D = duration(self.parameters["max_dist"], magnitude)
                    delta_time = (self.parameters["max_dist"] / 3.5) + D
                    start_time = date - (delta_time/3)
                    end_time = pick_time + delta_time
        else:
            if transform == "SIMPLE":
                delta_time = 8*60
                start_time = date - (delta_time / 3)
                end_time = pick_time + delta_time
            else:
                delta_time = 1300
                start_time = date - (delta_time / 3)
                end_time = pick_time + delta_time

        for file in files_path:
            sd = SeismogramDataAdvanced(file)
            tr = sd.get_waveform_advanced(self.macro, self.metadata, start_time=start_time, end_time=end_time)
            if len(tr.data) > 0:
                all_traces.append(tr)

        self.st = Stream(traces=all_traces)
        self.st.merge()

        if save_stream_plot:
            outputdir = os.path.join(self.parameters['output_directory'], ID_folder, "stream_raw.png")
            self.st.plot(outfile=outputdir, size=(800, 600))

    def invert(self, event_info,num):

        mt = MTIManager(self.st, self.metadata, event_info.latitude, event_info.longitude,
            event_info.depth, UTCDateTime(event_info.origin_time), self.parameters["min_dist"]*1000,
                        self.parameters["max_dist"]*1000, self.parameters['working_directory'])

        #mt.prepare_working_directory()
        [st, deltas, stations_isola_path] = mt.get_stations_index()
        ID_folder = event_info.origin_time.strftime("%m/%d/%Y")+"_"+str(num)
        outputdir = os.path.join(self.parameters['output_directory'], ID_folder)
        inputs = BayesISOLA.load_data(outdir=outputdir)

        inputs.set_event_info(lat=event_info.latitude, lon=event_info.longitude, depth=(event_info.depth/1000),
        mag=event_info.mw, t=UTCDateTime(event_info.origin_time))

        # Sets the source time function for calculating elementary seismograms inside green folder type, working_directory, t0=0, t1=0
        inputs.set_source_time_function('triangle', self.parameters['working_directory'], t0=2.0, t1=0.5)

        # Create data structure self.stations
        inputs.read_network_coordinates(stations_isola_path)  # stn['useN'] = stn['useE'] = stn['useZ'] = False

        # edit self.stations_index
        inputs.read_network_coordinates(os.path.join(self.parameters['working_directory'], "stations.txt"))

        stations = inputs.stations
        stations_index = inputs.stations_index

        # NEW FILTER STATIONS PARTICIPATION BY RMS THRESHOLD
        mt.get_traces_participation(None, 60, 5, magnitude=None, distance=None)
        inputs.stations, inputs.stations_index = mt.filter_mti_inputTraces(stations, stations_index)

        # read crustal file and writes in green folder
        inputs.read_crust(self.parameters['earth_model'], output=os.path.join(self.parameters['working_directory'],
                            "crustal.dat"))  # read_crust(source, output='green/crustal.dat')

        # writes station.dat in working folder from self.stations
        inputs.write_stations(self.parameters['working_directory'])

        inputs.data_raw = st
        inputs.create_station_index()
        inputs.data_deltas = deltas

        grid = BayesISOLA.grid(inputs, self.parameters['working_directory'], location_unc=3000, depth_unc=3000,
                time_unc=1, step_x=200, step_z=200, max_points=500, circle_shape=True, rupture_velocity=1000)


        data = BayesISOLA.process_data(inputs, self.parameters['working_directory'], grid, threads=self.cpuCount,
                use_precalculated_Green=False, fmax=self.parameters["fmax"], fmin=self.parameters["fmin"],
                                       correct_data=False)

        cova = BayesISOLA.covariance_matrix(data)
        cova.covariance_matrix_noise(crosscovariance=True, save_non_inverted=True)
        #
        solution = BayesISOLA.resolve_MT(data, cova, self.parameters['working_directory'], deviatoric=False,
                                         from_axistra=True)

        # deviatoric=True: force isotropic component to be zero
        #
        plot = BayesISOLA.plot(solution, self.parameters['working_directory'], from_axistra=True)
        plot.html_log(h1='Example_Test')
