from obspy import read, read_inventory, UTCDateTime
from loc_flow_isp.sq_isola_tools.mti_utilities import MTIManager
from loc_flow_isp.sq_isola_tools import BayesISOLA
if __name__ == "__main__":

    input_path = "/Users/roberto/Documents/SurfQuake/loc_flow_isp/sq_isola_tools/examples_read/input/example_ISP"
    crust_model = "/Users/roberto/Documents/SurfQuake/loc_flow_isp/sq_isola_tools/examples_read/input/example_ISP/Iberia.dat"
    outdir = "/Users/roberto/Documents/SurfQuake/loc_flow_isp/sq_isola_tools/examples_read/input/example_ISP/output"
    path_seismograms = "/Users/roberto/Documents/ISP/isp/examples/Moment_Tensor_example/*233*"
    path_metadata = "/Users/roberto/Documents/ISP/isp/Metadata/xml/metadata.xml"
    inv = read_inventory(path_metadata)
    st = read(path_seismograms)
    #st.plot()
    start = UTCDateTime("2018-08-21T00:20:00.0")
    end = UTCDateTime("2018-08-21T00:35:00.0")
    o_time = "2018-08-21 00:28:57" #'%Y-%m-%d %H:%M:%S'
    st.trim(starttime=start,endtime=end)
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
    mt = MTIManager(st, inv, 42.71, -7.70, 0.0, 0.0, input_path)
    [st, deltas, stations_isola_path] = mt.get_stations_index()
    inputs = BayesISOLA.load_data(outdir=outdir)
    inputs.set_event_info(lat=42.71, lon=-7.70, depth=11.0, mag=3.5, t=o_time)
    inputs.set_source_time_function('triangle', 2.0)
    inputs.read_network_coordinates(stations_isola_path) #changed stn['useN'] = stn['useE'] = stn['useZ'] = False to True
    inputs.read_crust(crust_model)
    inputs.write_stations()
    #inputs.load_files(paz_path, separator='', pz_dir=pz_dir, pz_separator='', pz_suffix='.pz')
    inputs.data_raw = st
    inputs.create_station_index()
    inputs.data_deltas = deltas
    print("end")
    grid = BayesISOLA.grid(
        inputs,
        location_unc=3000,  # m
        depth_unc=3000,  # m
        time_unc=1,  # s
        step_x=200,  # m
        step_z=200,  # m
        max_points=500,
        circle_shape=True,
        rupture_velocity=1000  # m/s
    )
    data = BayesISOLA.process_data(
        inputs,
        grid,
        threads=8,
        use_precalculated_Green="auto",
        fmax=0.04,
        fmin=0.08,
        correct_data=False
    )

    cova = BayesISOLA.covariance_matrix(data)
    cova.covariance_matrix_noise(crosscovariance=True, save_non_inverted=True)

    solution = BayesISOLA.resolve_MT(data, cova, deviatoric=False)
    # deviatoric=True: force isotropic component to be zero

    plot = BayesISOLA.plot(solution)
    plot.html_log(h1='Example_Test')
