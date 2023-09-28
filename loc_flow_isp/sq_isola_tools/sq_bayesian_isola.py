from obspy import UTCDateTime, Stream
from loc_flow_isp.DataProcessing import SeismogramDataAdvanced
from loc_flow_isp.Utils.obspy_utils import MseedUtil


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
        start = date-1300 #half and hour before
        end = pick_time+2*3600 #end 2 hours after
        files_path = MseedUtil.filter_time(list_files=self.files_path, starttime=start, endtime=end)
        return files_path

    def get_stations_list(self, phase_info):
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
            print(phase_info)
            station_filter, max_time = self.get_stations_list(phase_info)
            files_path = self.get_now_files(origin_time, max_time, station_filter)
             # A list with phase picking info
            # TODO NEEDS TO FILTER PROJECT BASED minimum and maximum distance
            # TODO NEEDS TO PROCESS Data


    def process_data(self, files_path):
        all_traces = []
        for file in files_path:
            sd = SeismogramDataAdvanced(file)
            tr = sd.get_waveform_advanced(self.macro, self.inventory, filter_error_callback=self.filter_error_message)
            all_traces.append(tr)

        self.st = Stream(traces=all_traces)
