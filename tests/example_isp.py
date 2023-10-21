#from obspy import read, read_inventory, UTCDateTime
#from loc_flow_isp.sq_isola_tools.mti_utilities import MTIManager
#from loc_flow_isp.sq_isola_tools import BayesISOLA

from obspy import read, read_inventory, UTCDateTime
from mti_utilities import MTIManager
import BayesISOLA
import os

if __name__ == "__main__":

    green_folder = "/Users/roberto/Documents/SurfQuake/surfquake/sq_isola_tools/examples_read/green"
    input_path = "/Users/roberto/Documents/SurfQuake/surfquake/sq_isola_tools/examples_read/input/example_ISP"
    crust_model = "/Users/roberto/Documents/SurfQuake/surfquake/sq_isola_tools/examples_read/input/example_ISP/Iberia.dat"
    outdir = "/Users/roberto/Documents/SurfQuake/surfquake/sq_isola_tools/examples_read/input/example_ISP/output"
    path_seismograms = "/Users/roberto/Documents/ISP/isp/examples/Moment_Tensor_example/*233*"
    path_metadata = "/Users/roberto/Documents/ISP/isp/Metadata/xml_test/inv_test.xml"
    working_directory = "/Users/roberto/Documents/SurfQuake/surfquake/sq_isola_tools/examples_read/input/example_ISP/working"

    if not os.path.exists(working_directory):
        os.makedirs(working_directory)
    MTIManager.move_files2workdir(green_folder, working_directory)
    inv = read_inventory(path_metadata)
    st = read(path_seismograms)
    st.plot()
    start = UTCDateTime("2018-08-21T00:20:00.0")
    end = UTCDateTime("2018-08-21T00:35:00.0")
    p_wave = UTCDateTime("2018-08-21T00:29:14")
    o_time = "2018-08-21 00:28:57" #'%Y-%m-%d %H:%M:%S'

    st.trim(starttime=start, endtime=end)
    f1 = 0.01
    f2 = 0.02
    f3 = 0.35 * st[0].stats.sampling_rate
    f4 = 0.40 * st[0].stats.sampling_rate
    pre_filt = (f1, f2, f3, f4)
    st.detrend(type='constant')
    # ...and the linear trend
    st.detrend(type='linear')
    st.taper(max_percentage=0.05)
    st.remove_response(inventory=inv, pre_filt=pre_filt, output="VEL", water_level=60)
    st.detrend(type='linear')
    st.taper(max_percentage=0.05)
    #st.plot()
    mt = MTIManager(st, inv, 42.71, -7.70, 0.0, 0.0, input_path, working_directory=working_directory)
    # creates stream and stations.txt (inside input_path) --> ready to create self.stations
    [st, deltas] = mt.get_stations_index()

    inputs = BayesISOLA.load_data(outdir=outdir)

    #creates self.event
    inputs.set_event_info(lat=42.71, lon=-7.70, depth=11.0, mag=3.5, t=o_time)
    # Sets the source time function for calculating elementary seismograms inside green folder type, working_directory, t0=0, t1=0
    inputs.set_source_time_function('triangle', working_directory,  t0=2.0, t1= 0.5)
    # edit self.stations_index / #modified original stn['useN'] = stn['useE'] = stn['useZ'] = False
    inputs.read_network_coordinates(os.path.join(working_directory, "stations.txt"))

    stations = inputs.stations
    stations_index = inputs.stations_index

    # NEW FILTER STATIONS PARTICIPATION BY RMS THRESHOLD
    
    # TODO STILL NEEDS TO BE TESTED
    #mt.get_traces_participation(p_wave, 60, 4)
    #inputs.stations,inputs.stations_index = mt.filter_mti_inputTraces(stations, stations_index)

    # read crustal file and writes in green folder
    inputs.read_crust(crust_model, output=os.path.join(working_directory, "crustal.dat")) #read_crust(source, output='green/crustal.dat')

    # writes station.dat in working folder from self.stations
    inputs.write_stations(working_directory)
    #inputs.load_files(paz_path, separator='', pz_dir=pz_dir, pz_separator='', pz_suffix='.pz')
    inputs.data_raw = st
    inputs.create_station_index()
    inputs.data_deltas = deltas
    print("end")
    grid = BayesISOLA.grid(inputs, working_directory, location_unc=3000, depth_unc=3000, time_unc=1, step_x=200, step_z=200, max_points=500,
        circle_shape=True, rupture_velocity=1000)

    data = BayesISOLA.process_data(inputs,  working_directory, grid, threads=4, use_precalculated_Green=True,
                                   fmax=0.04, fmin=0.08, correct_data=False)

    cova = BayesISOLA.covariance_matrix(data)
    cova.covariance_matrix_noise(crosscovariance=True, save_non_inverted=True)

    solution = BayesISOLA.resolve_MT(data, cova, working_directory, deviatoric=False, from_axistra=True)
    # deviatoric=True: force isotropic component to be zero

    plot = BayesISOLA.plot(solution, working_directory, from_axistra=True)
    plot.html_log(h1='Example_Test')
