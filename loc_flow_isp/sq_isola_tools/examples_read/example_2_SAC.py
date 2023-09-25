#! /usr/bin/env python
import os
from loc_flow_isp.sq_isola_tools import BayesISOLA
if __name__ == "__main__":

	outdir = os.path.join(os.getcwd(),'input/example_2_SAC/output')
	event_info_dir = os.path.join(os.getcwd(), 'input/example_2_SAC/event.isl')
	network_coordinates_path = os.path.join(os.getcwd(), 'input/example_2_SAC/network.stn')
	crustal_path = os.path.join(os.getcwd(), 'input/example_2_SAC/crustal.dat')
	paz_path = os.path.join(os.getcwd(), 'input/example_2_SAC/sac/')
	pz_dir = os.path.join(os.getcwd(), 'input/example_2_SAC/pzfiles/')

	inputs = BayesISOLA.load_data(outdir = outdir)
	inputs.read_event_info(event_info_dir)
	#inputs.set_event_info(lat = , lon=, depth=,mag =, t = ,)
	inputs.set_source_time_function('triangle', 2.0)
	inputs.read_network_coordinates('input/example_2_SAC/network.stn')
	inputs.read_crust('input/example_2_SAC/crustal.dat')
	inputs.load_files(paz_path, separator='', pz_dir=pz_dir, pz_separator='', pz_suffix='.pz')
	inputs.detect_mouse(figures=True)

	grid = BayesISOLA.grid(
		inputs,
		location_unc = 1000, # m
		depth_unc = 3000, # m
		time_unc = 1, # s
		step_x = 200, # m
		step_z = 200, # m
		max_points = 500,
		circle_shape = True,
		rupture_velocity = 1000 # m/s
		)

	data = BayesISOLA.process_data(
		inputs,
		grid,
		threads = 8,
		use_precalculated_Green = 'auto',
		fmax = 0.15,
		fmin = 0.02
		)

	cova = BayesISOLA.covariance_matrix(data)
	cova.covariance_matrix_noise(crosscovariance=True, save_non_inverted=True)

	solution = BayesISOLA.resolve_MT(data, cova, deviatoric=False)
		# deviatoric=True: force isotropic component to be zero

	plot = BayesISOLA.plot(solution)
	plot.html_log(h1='Example 2 (2013-12-12 00:59:18 Sargans)', mouse_figures='mouse/')
