#! /usr/bin/env python

from obspy import UTCDateTime
import BayesISOLA

inputs = BayesISOLA.load_data(outdir = 'output/6')
inputs.set_event_info(lat=39.35, lon=13.44, depth=450, mag=5.8, t=UTCDateTime('2016-10-28 20:02:49.1'), agency='EMSC')
	# https://www.emsc-csem.org/Earthquake/earthquake.php?id=540429#summary
inputs.read_network_coordinates('input/network.stn')
inputs.load_streams_fdsnws(
	[
		'http://webservices.ingv.it/fdsnws/',
		'http://www.orfeus-eu.org/fdsnws/',
		'http://eida.ethz.ch/fdsnws/', 
		'http://erde.geophysik.uni-muenchen.de/fdsnws/',
		'http://geofon.gfz-potsdam.de/fdsnws/',
		'http://eida.bgr.de/fdsnws/',
		'http://ws.resif.fr/fdsnws/'
	],
	t_before=500, t_after=200, save_to='input/seismo')
# inputs.detect_mouse(figures=True)

grid = BayesISOLA.grid(inputs,
	location_unc = 30e3, # m
	depth_unc = 20e3, # m
	time_unc = 20, # s
	step_x = 15e3, # m
	step_z = 10e3, # m
	max_points = 125,
	circle_shape = False,
	rupture_velocity = 3000 # m/s
	)

data = BayesISOLA.process_data(inputs, grid,
	fmin = 0.02,
	fmax = 0.10,
	velocity_ot_the_slowest_wave = 2500,
	calculate_or_verify_Green=False,
	trim_filter_data=True,
	decimate_shift=False,
	threads = 8,
	)
data.decimate_shift()
# data.use_elemse_from_syngine('ak135f_5s', 'input/GFs')
data.use_elemse_from_syngine('prem_a_5s', 'input/GFs')

cova = BayesISOLA.covariance_matrix(data)
cova.covariance_matrix_SACF(T=20, save_non_inverted=True)

solution = BayesISOLA.resolve_MT(data, cova, deviatoric=False)
# solution.print_solution(MT_comp_precision=3)

plot = BayesISOLA.plot(solution)
plot.logtext['crust'] = ''
plot.html_log(h1='Example 10 Syngine (2016-10-28 20:02:49 Tyrrhenian Sea)')
