import os
import numpy as np
from datetime import datetime
from obspy import read, read_events, UTCDateTime, Stream
from surfquake import all_locations
from surfquake.magnitude_tools.automag_processing_tools import ssp_inversion
from surfquake.magnitude_tools.automag_statistics import compute_summary_statistics, SourceSpecOutput
from surfquake.magnitude_tools.automag_tools import preprocess_tools
from surfquake.magnitude_tools.radiated_energy import Energy
from surfquake.Utils.obspy_utils import MseedUtil
from surfquake.Utils import read_nll_performance

class Automag:

    def __init__(self, project, inventory):
        self.project = project
        self.inventory = inventory
        self.all_traces = []
        self.st = None
        self.ML = []

    def make_stream(self):

         for file in self.files_path:
             try:
                 st = read(file)
                 st = self.fill_gaps(st, 60)
                 tr = self.ensure_24(st[0])
                 self.all_traces.append(tr)
             except:
                 pass
    #
         self.st = Stream(traces=self.all_traces)
    #     return st

    def check_gaps(self, gaps, tol):
        time_gaps = []
        for i in gaps:
            time_gaps.append(i[6])

        sum_total = sum(time_gaps)

        if sum_total > tol:
            check = True
        else:
            check = False

        return check

    def fill_gaps(self, st, tol):
        gaps = st.get_gaps()

        if len(gaps) > 0 and self.check_gaps(gaps, tol):
            st.print_gaps()
            st = []

        elif len(gaps) > 0 and self.check_gaps(gaps, tol) == False:
            st.print_gaps()
            st.merge(fill_value="interpolate", interpolation_samples=-1)

        elif len(gaps) == 0 and self.check_gaps(gaps, tol) == False:
            pass
        return st

    def ensure_24(self, tr):
        # Ensure that this trace is set to have 24h points padding with zeros the starttime and endtime
        # take random numbers to ensure the day
        random_list = np.random.choice(len(tr), 100)
        times_posix = tr.times(type="timestamp")
        days_prob = times_posix[random_list.tolist()]
        days_prob_max = days_prob.tolist()
        max_prob = max(set(days_prob_max), key=days_prob_max.count)
        year = int(datetime.utcfromtimestamp(max_prob).strftime('%Y'))
        month = int(datetime.utcfromtimestamp(max_prob).strftime('%m'))
        day = int(datetime.utcfromtimestamp(max_prob).strftime('%d'))

        check_starttime = UTCDateTime(year=year, month=month, day=day, hour=00, minute=00, microsecond=00)
        check_endtime = check_starttime + 24 * 3600
        tr.detrend(type="simple")
        tr.trim(starttime=check_starttime, endtime=check_endtime, pad=True, nearest_sample=True, fill_value=0)
        return tr

    def preprocess_stream(self, st, pick_info, regional=True):

        #TODO CHECK IS VALID THE WAVEFORM
        if regional:
            st.trim(starttime=pick_info[0][1]-60, endtime=pick_info[0][1]+3*60)
        else:
            #Teleseism time window
            st.trim(starttime=pick_info[0][1] - 1300, endtime=pick_info[0][1] + 3600)

        st.detrend(type="simple")
        st.taper(type="blackman", max_percentage=0.05)
        f1 = 0.05
        f2 = 0.08
        f3 = 0.35 * st[0].stats.sampling_rate
        f4 = 0.40 * st[0].stats.sampling_rate
        pre_filt = (f1, f2, f3, f4)

        st_deconv = []
        st_wood = []
        paz_wa = {'sensitivity': 2800, 'zeros': [0j], 'gain': 1,
                  'poles': [-6.2832 - 4.7124j, -6.2832 + 4.7124j]}

        for tr in st:

            tr_deconv = tr.copy()
            tr_wood = tr.copy()

            try:
                print("Removing Instrument")
                tr_deconv.remove_response(inventory=self.inventory, pre_filt=pre_filt, output="DISP", water_level=90)
                print(tr_deconv)
                # tr_deconv.plot()
                st_deconv.append(tr_deconv)
            except:
                print("Coudn't deconvolve", tr.stats)
                tr.data = np.array([])

            print("Simulating Wood Anderson Seismograph")

            try:
                resp = self.inventory.get_response(tr.id, tr.stats.starttime)
                resp = resp.response_stages[0]
                paz_mine = {'sensitivity': resp.stage_gain * resp.normalization_factor, 'zeros': resp.zeros,
                            'gain': resp.stage_gain, 'poles': resp.poles}
                tr_wood.simulate(paz_remove=paz_mine, paz_simulate=paz_wa, water_level=90)
                # tr_wood.plot()
                st_wood.append(tr_wood)
            except:
                print("Coudn't deconvolve", tr.stats)
                tr.data = np.array([])

        print("Finished Deconvolution")
        st_deconv = Stream(traces=st_deconv)
        st_wood = Stream(traces=st_wood)
        st_deconv.plot()
        st_wood.plot()
        return st_deconv, st_wood

    def ML_statistics(self):
        MLs = np.array(self.ML)
        MLs = MLs[MLs != None]
        MLs = self.reject_outliers(MLs)
        #ML_mean = MLs.mean()
        ML_median = np.median(MLs)
        ML_deviation = MLs.std()
        #print("Local Magnitude", str(self.ML_mean)+str(self.ML_deviation))
        return ML_median, ML_deviation

    def reject_outliers(self, data, m=2.):
        d = np.abs(data - np.median(data))
        mdev = np.median(d)
        s = d / mdev if mdev else np.zeros(len(d))
        return data[s < m]
    def get_arrival(self, arrivals, sta_name):
        arrival_return = []
        for arrival in arrivals:
            if arrival.station == sta_name:
                arrival_return.append(arrival)
        return arrival_return

    def get_now_files(self, date):

        selection = [".", ".", "."]

        _, self.files_path = MseedUtil.filter_project_keys(self.project, net=selection[0], station=selection[1],
                                                       channel=selection[2])
        start = date.split(".")
        start = UTCDateTime(year=int(start[1]), julday=int(start[0]), hour=00, minute=00, second=00)+1
        end = start+(24*3600-2)
        self.files_path = MseedUtil.filter_time(list_files=self.files_path, starttime=start, endtime=end)
        print(self.files_path)

    def filter_station(self, station):

        filtered_list = []

        for file in self.files_path:
            header = read(file, headlonly=True)
            sta = header[0].stats.station
            if station == sta:
                filtered_list.append(file)

        return filtered_list

    def scan_folder(self):
        obsfiles1 = []
        dates = {}
        for top_dir, _, files in os.walk(all_locations):

            for file in files:
                try:
                    file_hyp = os.path.join(top_dir, file)
                    cat = read_events(file_hyp, format="NLLOC_HYP")
                    ev = cat[0]
                    date = ev.origins[0]["time"]
                    date = str(date.julday) + "." + str(date.year)

                    obsfiles1.append(file_hyp)
                    if date not in dates:
                        dates[date] = [file_hyp]
                    else:
                        dates[date].append(file_hyp)
                except:
                    pass

        self.dates=dates

    def scan_from_origin(self, origin):

        self.date = origin["time"]

    def _get_stations(self, arrivals):
        stations = []
        for pick in arrivals:
            if pick.station not in stations:
                stations.append(pick.station)

        return stations

    def _get_info_in_arrivals(self, station, arrivals, min_residual_threshold):
        data = {}
        geodetics = {}
        for arrival in arrivals:
            if station == arrival.station:
                geodetics["distance_km"] = arrival.distance_km
                geodetics["distance_degrees"] = arrival.distance_degrees
                geodetics["azimuth"] = arrival.azimuth
                geodetics["takeoff_angle"] = arrival.takeoff_angle
                if arrival.phase[0] == "P":
                    geodetics["travel_time"] = float(arrival.travel_time)
                if arrival.phase in data.keys():
                    data[arrival.phase]["time_weight"].append(arrival.time_weight)
                    data[arrival.phase]["date"].append(arrival.date)
                else:
                    data[arrival.phase] = {}
                    data[arrival.phase]["time_weight"] = []
                    data[arrival.phase]["date"] = []
                    data[arrival.phase]["time_weight"].append(arrival.time_weight)
                    data[arrival.phase]["date"].append(arrival.date)

        output = {}
        output[station] = []
        for key, value in data.items():

             residual_min = list(map(abs, data[key]["time_weight"]))
             residual_min = max(residual_min)
             residual_min_index = data[key]["time_weight"].index(residual_min)
             if data[key]["date"][residual_min_index] >= min_residual_threshold:
                output[station].append([key, data[key]["date"][residual_min_index]])

        return output, geodetics


    def estimate_magnitudes(self, config):
        magnitude_mw_statistics_list = []
        magnitude_ml_statistics_list = []
        focal_parameters_list = []
        # extract info from config:
        magnitude_mw_statistics = {}
        magnitude_ml_statistics = {}
        # extract info from config:
        gap_max = config['gap_max']
        overlap_max = config['overlap_max']
        rmsmin = config['rmsmin']
        clipping_sensitivity = config['clipping_sensitivity']
        geom_spread_model = config['geom_spread_model']
        geom_spread_n_exponent = config['geom_spread_n_exponent']
        geom_spread_cutoff_distance = config['geom_spread_cutoff_distance']
        rho = config['rho']
        spectral_smooth_width_decades = config['spectral_smooth_width_decades']
        spectral_sn_min = config['spectral_sn_min']
        spectral_sn_freq_range = config['spectral_sn_freq_range']
        t_star_0_variability = config["t_star_0_variability"]
        invert_t_star_0 = config["invert_t_star_0"]
        t_star_0 = config["t_star_0"]
        inv_algorithm = config["inv_algorithm"]
        pi_misfit_max = config["pi_misfit_max"]
        pi_t_star_min_max = config["pi_t_star_min_max"]
        pi_fc_min_max = config["pi_fc_min_max"]
        pi_bsd_min_max = config["pi_bsd_min_max"]
        max_freq_Er = config["max_freq_Er"]
        min_residual_threshold = config["min_residual_threshold"]
        scale = config["scale"]
        max_win_duration = config["win_length"]
        a = config["a_local_magnitude"]
        b = config["b_local_magnitude"]
        c = config["c_local_magnitude"]
        bound_config = {"Qo_min_max": config["Qo_min_max"], "t_star_min_max": config["t_star_min_max"],
                        "wave_type": config["wave_type"], "fc_min_max": config["fc_min_max"]}
        statistics_config = config.maps[7]
        self.scan_folder()
        for date in self.dates:
            events = self.dates[date]
            #events = list(set(events))
            self.get_now_files(date)
            self.make_stream()
            for event in events:
                self.ML = []
                sspec_output = SourceSpecOutput()
                cat = read_nll_performance.read_nlloc_hyp_ISP(event)
                focal_parameters = [cat[0].origins[0]["time"], cat[0].origins[0]["latitude"],
                                    cat[0].origins[0]["longitude"],
                                    cat[0].origins[0]["depth"] * 1E-3]
                sspec_output.event_info.event_id = "Id_Local"
                sspec_output.event_info.longitude = cat[0].origins[0]["longitude"]
                sspec_output.event_info.latitude = cat[0].origins[0]["latitude"]
                sspec_output.event_info.depth_in_km = cat[0].origins[0]["depth"] * 1E-3
                sspec_output.event_info.origin_time = cat[0].origins[0]["time"]
                event = cat[0]
                arrivals = event["origins"][0]["arrivals"]
                stations = self._get_stations(arrivals)

                for station in stations:
                    try:
                        events_picks, geodetics = self._get_info_in_arrivals(station, arrivals, min_residual_threshold)
                        pick_info = events_picks[station]
                        st2 = self.st.select(station=station)
                        st2.merge()
                        if st2.count() > 0:
                            inv_selected = self.inventory.select(station=station)
                            pt = preprocess_tools(st2, pick_info, focal_parameters, geodetics, inv_selected, scale)
                            pt.deconv_waveform(gap_max, overlap_max, rmsmin, clipping_sensitivity, max_win_duration)
                            self.ML.append(pt.magnitude_local(a, b, c))
                            pt.st_deconv = pt.st_deconv.select(component="Z")
                            if pt.st_deconv.count() > 0:

                                spectrum_dict = pt.compute_spectrum(geom_spread_model, geom_spread_n_exponent,
                                                geom_spread_cutoff_distance, rho, spectral_smooth_width_decades,
                                                spectral_sn_min, spectral_sn_freq_range)

                                if spectrum_dict is not None:
                                    ssp = ssp_inversion(spectrum_dict, t_star_0_variability, invert_t_star_0, t_star_0,
                                        focal_parameters, geodetics, inv_selected, bound_config, inv_algorithm, pi_misfit_max,
                                                        pi_t_star_min_max, pi_fc_min_max, pi_bsd_min_max)

                                    magnitudes = ssp.run_estimate_all_traces()
                                    for chn in magnitudes:
                                        sspec_output.station_parameters[chn._id] = chn
                                        # for now just for vertical component
                                        for keyId, trace_dict in spectrum_dict.items():
                                            spec = trace_dict["amp_signal_moment"]
                                            specnoise = trace_dict["amp_signal_moment"]
                                            freq_signal = trace_dict["freq_signal"]
                                            freq_noise = trace_dict["freq_noise"]
                                            full_period_signal = trace_dict["full_period_signal"]
                                            full_period_noise = trace_dict["full_period_noise"]
                                            vs = trace_dict["vs"]
                                        # compute and implement energy
                                        sspec_output.station_parameters[chn._id] = Energy.radiated_energy(chn._id, spec,
                                            specnoise, freq_signal, freq_noise, full_period_signal, full_period_noise,
                                            chn.fc.value, vs, max_freq_Er, rho, chn.t_star.value, chn)
                    except:
                        print("Coudn't estimate magnitude for station ", station)

                try:
                    magnitude_mw_statistics = compute_summary_statistics(statistics_config, sspec_output)
                except:
                    magnitude_mw_statistics = None
                magnitude_mw_statistics_list.append(magnitude_mw_statistics)
                try:
                    ML_mean, ML_std = self.ML_statistics()
                    #magnitude_ml_statistics["ML_mean"] = ML_mean
                    #magnitude_ml_statistics["ML_std"] = ML_std
                except:
                    magnitude_ml_statistics = None
                magnitude_ml_statistics_list.append([ML_mean, ML_std])
                focal_parameters_list.append(focal_parameters)

        return magnitude_mw_statistics_list, magnitude_ml_statistics_list, focal_parameters_list

#if __name__ == "__main__":
    # time_window_params = {"channels": ["HHE, HHN, HHZ"], "max_epi_dist": 300, "vp_tt": None, "vs_tt": None,
    #                       "p_arrival_tolerance": 4.0,
    #                       "s_arrival_tolerance": 4.0, "noise_pre_time": 15.0, "signal_pre_time": 1.0,
    #                       "win_length": 10.0}
    #
    # spectrum_params = {"wave_type": "P", "time_domain_int": False, "ignore_vertical": False, "taper_halfwidth": 0.05,
    #                    "spectral_win_length": 20.0, "spectral_smooth_width_decades": 0.2, "residuals_filepath": None,
    #                    "bp_freqmin_acc": 1.0,
    #                    "bp_freqmax_acc": 50.0, "bp_freqmin_shortp": 1.0, "bp_freqmax_shortp": 40.0,
    #                    "bp_freqmin_broadb": 0.4,
    #                    "bp_freqmax_broadb": 40.0, "freq1_acc": 1, "freq2_acc": 30.0, "freq1_shortp": 1.0,
    #                    "freq2_shortp": 30.0,
    #                    "freq1_broadb": 0.5, "freq2_broadb": 10.0}
    #
    # signal_noise_ratio_params = {"rmsmin": 0.0, "sn_min": 1.0, "clip_max_percent": 5.0, "gap_max": None,
    #                              "overlap_max": None,
    #                              "spectral_sn_min": 0.0, "spectral_sn_freq_range": (0.1, 2.0), "clipping_sensitivity": 3}
    #
    # source_model_parameters = {"vp_source": 6.0, "vs_source": 3.5, "vp_stations": None, "vs_stations": None,
    #                            "rho": 2500.0,
    #                            "rpp": 0.52, "rps": 0.62, "rp_from_focal_mechanism": False,
    #                            "geom_spread_model": "r_power_n",
    #                            "geom_spread_n_exponent": 1.0, "geom_spread_cutoff_distance": 100.0}
    #
    # spectral_model_params = {"weighting": "noise", "f_weight": 7.0, "weight": 10.0, "t_star_0": 0.045,
    #                          "invert_t_star_0": False,
    #                          "t_star_0_variability": 0.1, "Mw_0_variability": 0.1, "inv_algorithm": "TNC",
    #                          "t_star_min_max": (0.0, 0.1), "fc_min_max" : (1.0, 50.0), "Qo_min_max": None}
    #
    # postinversion_params = {"pi_fc_min_max": None, "pi_bsd_min_max": None, "pi_misfit_max": None,
    #                         "pi_t_star_min_max": None}
    #
    # radiated_energy_params = {"max_freq_Er": None}
    #
    # statistics = {"reference_statistics": 'weighted_mean', "n_sigma": 1, "lower_percentage": 15.9, "mid_percentage": 50,
    #               "upper_percentage": 84.1, "nIQR": 1.5}
    #
    # config = ChainMap(time_window_params, spectrum_params, signal_noise_ratio_params, source_model_parameters,
    #                   spectral_model_params, postinversion_params, radiated_energy_params, statistics)


    # mg = Automag(project, inventoy)
    # mg.estimate_magnitudes(config)
