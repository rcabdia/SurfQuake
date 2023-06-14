import math
import os
import pickle
from multiprocessing import Pool
from enum import unique, Enum
from obspy import read_inventory
from obspy.geodetics import degrees2kilometers, gps2dist_azimuth
from obspy.io.nlloc.core import read_nlloc_hyp
from obspy.taup import TauPyModel
import pandas as pd
from obspy import Stream, read, Trace, UTCDateTime, read_events
import numpy as np
from obspy.core.event import Origin
from loc_flow_isp.Exceptions.exceptions import InvalidFile
from loc_flow_isp.Structures.structures import TracerStats
from typing import List
from loc_flow_isp.Utils.nllOrgErrors import computeOriginErrors


@unique
class Filters(Enum):

    Default = "Filter"
    BandPass = "bandpass"
    BandStop = "bandstop"
    LowPass = "lowpass"
    HighPass = "highpass"

    def __eq__(self, other):
        if type(other) is str:
            return self.value == other
        else:
            return self.value == other.value

    def __ne__(self, other):
        if type(other) is str:
            return self.value != other
        else:
            return self.value != other.value

    @classmethod
    def get_filters(cls):
        return [item.value for item in cls.__members__.values()]

class ObspyUtil:


    @staticmethod
    def get_figure_from_stream(st: Stream, **kwargs):
        if st:
            return st.plot(show=False, **kwargs)
        return None

    @staticmethod
    def get_tracer_from_file(file_path) -> Trace:
        st = read(file_path)
        return st[0]

    @staticmethod
    def get_stats(file_path):
        """
        Reads only the header for the metadata and return a :class:`TracerStats`.
        :param file_path: The full file's path for the mseed.
        :return: A TracerStats contain the metadata.
        """
        st = read(file_path, headonly=True)
        tr = st[0]
        stats = TracerStats.from_dict(tr.stats)
        return stats

    @staticmethod
    def get_stats_from_trace(tr: Trace):

        """
        Reads only the header for the metadata and return a :class:`TracerStats`.
        :param ftrace: obspy trace.
        :return: A Dictionary with TracerStats contain the metadata.
        """
        net = tr.stats.network
        station = tr.stats.station
        location = tr.stats.location
        channel = tr.stats.channel
        starttime = tr.stats.starttime
        endtime = tr.stats.endtime
        npts= tr.stats.npts
        sampling_rate=tr.stats.sampling_rate
        stats =  {'net': net, 'station': station, 'location':location, 'channel':channel, 'starttime':starttime,
                  'endtime':endtime,'npts': npts, 'sampling_rate':sampling_rate}
        return stats

    @staticmethod
    def get_stations_from_stream(st: Stream):

        stations = []

        for tr in st:
            station = tr.stats.station
            if stations.count(station):
                pass
            else:
                stations.append(station)

        return stations

    @staticmethod
    def get_trip_times(source_depth, min_dist, max_dist):

        model = TauPyModel(model="iasp91")
        distances = np.linspace(min_dist, max_dist, 50)
        arrivals_list = []

        for value in distances:

            arrival = model.get_travel_times(source_depth_in_km=source_depth, distance_in_degree= float(value))


            arrivals_list.append(arrival)

        return arrivals_list

    @staticmethod
    def convert_travel_times(arrivals, otime, dist_km = True):

        all_arrival = {}

        # Loop over arrivals objects in list
        for arrival_set in arrivals:
            # Loop over phases in list
            for arrival in arrival_set:
                phase_id = arrival.purist_name
                time = otime + arrival.time

                dist = arrival.purist_distance % 360.0
                distance = arrival.distance
                if distance < 0:
                    distance = (distance % 360)
                if abs(dist - distance) / dist > 1E-5:
                    continue

                if dist_km:
                    distance = degrees2kilometers(distance)

                if phase_id in all_arrival.keys():
                    all_arrival[phase_id]["times"].append(time.matplotlib_date)
                    all_arrival[phase_id]["distances"].append(distance)

                else:
                    all_arrival[phase_id] = {}
                    all_arrival[phase_id]["times"] = [time.matplotlib_date]
                    all_arrival[phase_id]["distances"] = [distance]

        return all_arrival

    @staticmethod
    def coords2azbazinc(station_latitude, station_longitude,station_elevation, origin_latitude,
                        origin_longitude, origin_depth):

        """
        Returns azimuth, backazimuth and incidence angle from station coordinates
        given in first trace of stream and from event location specified in origin
        dictionary.
        """

        dist, bazim, azim = gps2dist_azimuth(station_latitude, station_longitude, float(origin_latitude),
                                             float(origin_longitude))
        elev_diff = station_elevation - float(origin_depth)
        inci = math.atan2(dist, elev_diff) * 180.0 / math.pi

        return azim, bazim, inci

    @staticmethod
    def filter_trace(trace, trace_filter, f_min, f_max, **kwargs):
        """
        Filter a obspy Trace or Stream.
        :param trace: The trace or stream to be filter.
        :param trace_filter: The filter name or Filter enum, ie. Filter.BandPass or "bandpass".
        :param f_min: The lower frequency.
        :param f_max: The higher frequency.
        :keyword kwargs:
        :keyword corners: The number of poles, default = 4.
        :keyword zerophase: True for keep the phase without shift, false otherwise, Default = True.
        :return: False if bad frequency filter, True otherwise.
        """
        if trace_filter != Filters.Default:
            if not (f_max - f_min) > 0:
                print("Bad filter frequencies")
                return False

            corners = kwargs.pop("corners", 4)
            zerophase = kwargs.pop("zerophase", True)

            trace.taper(max_percentage=0.05, type="blackman")

            if trace_filter == Filters.BandPass or trace_filter == Filters.BandStop:
                trace.filter(trace_filter, freqmin=f_min, freqmax=f_max, corners=corners, zerophase=zerophase)

            elif trace_filter == Filters.HighPass:
                trace.filter(trace_filter, freq=f_min, corners=corners, zerophase=zerophase)

            elif trace_filter == Filters.LowPass:
                trace.filter(trace_filter, freq=f_max, corners=corners, zerophase=zerophase)

        return True

    @staticmethod
    def merge_files_to_stream(files_path: List[str], *args, **kwargs) \
            -> Stream:
        """
        Reads all files in the list and concatenate in a Stream.
        :param files_path: A list of valid mseed files.
        :arg args: Valid arguments of obspy.read().
        :keyword kwargs: Valid kwargs for obspy.read().
        :return: The concatenate stream.
        """
        st = Stream()
        for file in files_path:
            if MseedUtil.is_valid_mseed(file):
                st += read(file, *args, **kwargs)
            else:
                raise InvalidFile("The file {} either doesn't exist or is not a valid mseed.".format(file))
        return st

    @staticmethod
    def trim_stream(st: Stream, start_time: UTCDateTime, end_time: UTCDateTime):
        """
        This method is a safe wrapper to Stream.trim(). If start_time and end_time don't overlap the
        stream, it will be trimmed by the maximum start time and minimum end time within its tracers .
        :param st: The Stream to be trimmed.
        :param start_time: The UTCDatetime for start the trim.
        :param end_time: The UTCDatetime for end the trim.
        :return:
        """
        max_start_time = np.max([tr.stats.starttime for tr in st])
        min_end_time = np.min([tr.stats.endtime for tr in st])
        st.trim(max_start_time, min_end_time)

        overlap = start_time < min_end_time and max_start_time < end_time  # check if dates overlap.
        if overlap:
            if max_start_time - start_time < 0 < min_end_time - end_time:  # trim start and end time
                st.trim(start_time, end_time)
            elif max_start_time - start_time < 0:  # trim only start time.
                st.trim(starttime=start_time)
            elif min_end_time - end_time > 0:  # trim only end time.
                st.trim(endtime=end_time)

    @staticmethod
    def reads_hyp_to_origin(hyp_file_path: str) -> Origin:
        """
        Reads an hyp file and returns the Obspy Origin.
        :param hyp_file_path: The file path to the .hyp file
        :return: An Obspy Origin
        """

        if os.path.isfile(hyp_file_path):
            cat = read_events(hyp_file_path)
            event = cat[0]
            origin = event.origins[0]
            modified_origin_90 = computeOriginErrors(origin)
            origin.depth_errors["uncertainty"]=modified_origin_90['depth_errors'].uncertainty
            origin.origin_uncertainty.max_horizontal_uncertainty = modified_origin_90['origin_uncertainty'].max_horizontal_uncertainty
            origin.origin_uncertainty.min_horizontal_uncertainty = modified_origin_90[
                'origin_uncertainty'].min_horizontal_uncertainty
            origin.origin_uncertainty.azimuth_max_horizontal_uncertainty = modified_origin_90['origin_uncertainty'].azimuth_max_horizontal_uncertainty

        return origin

    @staticmethod
    def reads_pick_info(hyp_file_path: str):
        """
        Reads an hyp file and returns the Obspy Origin.
        :param hyp_file_path: The file path to the .hyp file
        :return: list Pick info
        """
        if os.path.isfile(hyp_file_path):
            Origin = read_nlloc_hyp(hyp_file_path)
            return Origin.events[0].picks


    @staticmethod
    def has_same_sample_rate(st: Stream, value):
        for tr in st:
            print(tr.stats.sampling_rate)
            if tr.stats.sampling_rate != value:
                return False
        return True

    @staticmethod
    def realStation(dataXml, stationfile):
        channels = ['HNZ', 'HHZ', 'BHZ', 'EHZ']

        with open(stationfile, 'w') as f:
            for network in dataXml:
                for stations in network.stations:
                    info_channel = [ch for ch in stations.channels if ch.code in channels]
                    f.write(f"{stations.longitude}\t{stations.latitude}\t{network.code}\t{stations.code}\t"
                            f"{info_channel[0].code}\t{float(stations.elevation) / 1000: .3f}\n")

            f.close()

    @staticmethod
    def nllStation(dataXml, stationfile):
        with open(stationfile, 'w') as f:
            for network in dataXml:
                for stations in network.stations:
                    f.write(f"{'GTSRCE '}{stations.code + ' '}{'LATLON '}{stations.latitude}{' '}{stations.longitude}"
                            f"{' '}{float(0.0):.1f}{' '}{float(stations.elevation) / 1000:.3f}\n")

            f.close()

    @staticmethod
    def readXml(file, real_station, nll_station):
        xml = read_inventory(file)

        ObspyUtil.realStation(xml, real_station)
        ObspyUtil.nllStation(xml, nll_station)


class MseedUtil:

    def __init__(self, robust=True, **kwargs):

        self.start = kwargs.pop('starttime', [])
        self.end = kwargs.pop('endtime', [])
        self.obsfiles = []
        self.pos_file = []
        self.robust = robust
        self.use_ind_files = False


    @classmethod
    def load_project(cls, file: str):
        project = {}
        try:
            project = pickle.load(open(file, "rb"))

        except:
            pass
        return project

    def search_indiv_files(self, list_files: list):

        self.use_ind_files = True
        self.list_files = list_files
        with Pool(processes=os.cpu_count()) as pool:
            returned_list = pool.map(self.create_dict, range(len(self.list_files)))

        project = self.convert2dict(returned_list)
        self.use_ind_files = False

        return project

    def search_files(self, rooth_path: str):

        self.search_file = []
        for top_dir, sub_dir, files in os.walk(rooth_path):
            for file in files:
                self.search_file.append(os.path.join(top_dir, file))

        with Pool(processes=os.cpu_count()) as pool:
            returned_list = pool.map(self.create_dict, range(len(self.search_file)))

        project = self.convert2dict(returned_list)

        return project

    def create_dict(self, i):
        key = None
        data_map = None

        try:
            if self.use_ind_files:
                header = read(self.list_files[i], headeronly=True)
                print(self.list_files[i])
                net = header[0].stats.network
                sta = header[0].stats.station
                chn = header[0].stats.channel
                key = net + "." + sta + "." + chn
                data_map = [self.list_files[i], header[0].stats]
            else:
                header = read(self.search_file[i], headeronly=True)
                print(self.search_file[i])
                net = header[0].stats.network
                sta = header[0].stats.station
                chn = header[0].stats.channel
                key = net + "." + sta + "." + chn
                data_map = [self.search_file[i], header[0].stats]

        except:
            pass

        return [key, data_map]

    def convert2dict(self, project):
        project_converted = {}
        for name in project:
            if name[0] in project_converted.keys() and name[0] is not None:
                project_converted[name[0]].append([name[1][0],name[1][1]])

            elif name[0] not in project_converted.keys() and name[0] is not None:
                project_converted[name[0]] = [[name[1][0],name[1][1]]]

        return project_converted

    def convert2dataframe(self, project):
        project_converted = []
        _names = project.keys()

        for name in _names:
            for i in range(len(project[name])):
                project_converted.append({
                    'id': name,
                    'fname': project[name][i][0],
                    'stats': project[name][i][1]
                })

        return pd.DataFrame.from_dict(project_converted)

    @classmethod
    def get_metadata_files(cls, file):
        from obspy import read_inventory
        try:

            inv = read_inventory(file)

            return inv

        except IOError:

           return []
