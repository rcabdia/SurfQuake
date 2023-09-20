#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import numpy as np

from obspy import UTCDateTime

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from loc_flow_isp.sq_isola_tools.BayesISOLA.fileformats import read_elemse, read_elemse_from_files
from loc_flow_isp.sq_isola_tools.BayesISOLA.helpers import my_filter


def align_yaxis(ax1, ax2, v1=0, v2=0):
	"""
	Adjust ax2 ylimit so that v2 in ax2 is aligned to v1 in ax1
	"""
	_, y1 = ax1.transData.transform((0, v1))
	_, y2 = ax2.transData.transform((0, v2))
	inv = ax2.transData.inverted()
	_, dy = inv.transform((0, 0)) - inv.transform((0, y1-y2))
	miny, maxy = ax2.get_ylim()
	ax2.set_ylim(miny+dy, maxy+dy)

def plot_seismo(self, outfile='$outdir/seismo.png', comp_order='ZNE', cholesky=False, obs_style='k', obs_width=3, synt_style='r', synt_width=2, add_file=None, add_file_style='k:', add_file_width=2, add_file2=None, add_file2_style='b-', add_file2_width=2, plot_stations=None, plot_components=None, sharey=False):
	"""
	Plots the fit between observed and simulated seismogram.
	
	:param outfile: path to file for plot output; if ``None`` plots to the screen
	:type outfile: string, optional
	:param comp_order: order of component in the plot, supported are 'ZNE' (default) and 'NEZ'
	:type comp_order: string, optional
	:param cholesky: plots standardized seismogram instead of original ones
	:type cholesky: bool, optional
	:param obs_style: line style for observed data
	:param obs_width: line width for observed data
	:param synt_style: line style for simulated data
	:param synt_width: line width for simulated data
	:param add_file: path to a reference file generated by function :func:`save_seismo`
	:type add_file: string or None, optional
	:param add_file_style: line style for reference data
	:param add_file_width: line width for reference data
	:param add_file2: path to second reference file
	:type add_file2: string or None, optional
	:param add_file2_style: line style for reference data
	:param add_file2_width: line width for reference data
	:param plot_stations: list of stations to plot; if ``None`` plots all stations
	:type plot_stations: list or None, optional
	:param plot_components: list of components to plot; if ``None`` plots all components
	:type plot_components: list or None, optional
	:param sharey: if ``True`` the y-axes for all stations have the same limits, otherwise the limits are chosen automatically for every station
	:type sharey: bool, optional
	"""
	if cholesky and not len(self.cova.LT) and not len(self.cova.LT3):
		raise ValueError('Covariance matrix not set. Run "covariance_matrix()" first.')
	data = self.data.data_shifts[self.MT.centroid['shift_idx']]
	npts = self.data.npts_slice
	samprate = self.data.samprate
	if self.MT.centroid['path']:
		elemse = read_elemse_from_files(self.inp.nr, self.MT.centroid['path'], self.inp.stations, self.inp.event['t'], self.data.samprate, self.data.npts_elemse, self.data.invert_displacement)
	else:
		elemse = read_elemse(self.inp.nr, self.data.npts_elemse, 'green/elemse'+self.MT.centroid['id']+'.dat', self.inp.stations, self.data.invert_displacement)
	#if not no_filter:
	for r in range(self.inp.nr):
		for e in range(6):
			my_filter(elemse[r][e], self.inp.stations[r]['fmin'], self.inp.stations[r]['fmax'])
			elemse[r][e].trim(UTCDateTime(0)+self.data.elemse_start_origin)

	plot_stations, comps, f, ax, ea = self.plot_seismo_backend_1(plot_stations, plot_components, comp_order, sharey=(cholesky or sharey), title_prefix=('','pseudo ')[cholesky and self.cova.LT3!=[]], ylabel=('velocity [m/s]', None)[cholesky])
	
	t = np.arange(0, (npts-0.5) / samprate, 1. / samprate)
	if add_file:
		add = np.load(add_file)
	if add_file2:
		add2 = np.load(add_file2)
	d_max = 0
	for sta in plot_stations:
		r = plot_stations.index(sta)
		#if no_filter:
			#SAMPRATE = self.data_unfiltered[sta][0].stats.sampling_rate
			#NPTS = int(npts/samprate * SAMPRATE), 
			#SHIFT = int(round(self.MT.centroid['shift']*SAMPRATE))
			#T = np.arange(0, (NPTS-0.5) / SAMPRATE, 1. / SAMPRATE)
		SYNT = {}
		for comp in range(3):
			SYNT[comp] = np.zeros(npts)
			for e in range(6):
				SYNT[comp] += elemse[sta][e][comp].data[0:npts] * self.MT.centroid['a'][e,0]
		comps_used = 0
		for comp in comps:
			synt = SYNT[comp]
			#if no_filter:
				#D = np.empty(NPTS)
				#for i in range(NPTS):
					#if i+SHIFT >= 0:	
						#D[i] = self.data_unfiltered[sta][comp].data[i+SHIFT]
			#else:
			d = data[sta][comp][0:len(t)]
			if cholesky and self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
				if self.cova.LT3:
					#print(r, comp) # DEBUG
					d    = np.zeros(npts)
					synt = np.zeros(npts)
					x1 = -npts
					for COMP in range(3):
						if not self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[COMP]]:
							continue
						x1 += npts; x2 = x1+npts
						y1 = comps_used*npts; y2 = y1+npts
						#print(self.cova.LT3[sta][y1:y2, x1:x2].shape, data[sta][COMP].data[0:npts].shape) # DEBUG
						d    += np.dot(self.cova.LT3[sta][y1:y2, x1:x2], data[sta][COMP].data[0:npts])
						synt += np.dot(self.cova.LT3[sta][y1:y2, x1:x2], SYNT[COMP])
				else:
					d    = np.dot(self.cova.LT[sta][comp], d)
					synt = np.dot(self.cova.LT[sta][comp], synt)
				comps_used += 1
			c = comps.index(comp)
			#if no_filter:
				#ax[r,c].plot(T,D, color='k', linewidth=obs_width)
			if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]] or not cholesky: # do not plot seismogram if the component is not used and Cholesky decomposition is plotted
				l_d, = ax[r,c].plot(t,d, obs_style, linewidth=obs_width)
				if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
					d_max = max(max(d), -min(d), d_max)
			else:
				ax[r,c].plot([0],[0], 'w', linewidth=0)
			if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
				l_s, = ax[r,c].plot(t,synt, synt_style, linewidth=synt_width)
				d_max = max(max(synt), -min(synt), d_max)
			else:
				if not cholesky:
					ax[r,c].plot(t,synt, color='gray', linewidth=2)
			if add_file:
				ax[r,c].plot(t, add[:, 3*sta+comp], add_file_style, linewidth=add_file_width)
			if add_file2:
				ax[r,c].plot(t, add2[:, 3*sta+comp], add_file2_style, linewidth=add_file2_width)
	ax[-1,0].set_ylim([-d_max, d_max])
	ea.append(f.legend((l_d, l_s), ('inverted data', 'modeled (synt)'), loc='lower center', bbox_to_anchor=(0.5, 1.-0.0066*len(plot_stations)), ncol=2, numpoints=1, fontsize='small', fancybox=True, handlelength=3)) # , borderaxespad=0.1
	ea.append(f.text(0.1, 1.06-0.004*len(plot_stations), 'x', color='white', ha='center', va='center'))
	outfile = outfile.replace('$outdir', self.outdir)
	self.plot_seismo_backend_2(outfile, plot_stations, comps, ax, extra_artists=ea)
	if cholesky:
		self.plots['seismo_cova'] = outfile
	elif sharey:
		self.plots['seismo_sharey'] = outfile
	else:
		self.plots['seismo'] = outfile

def plot_covariance_function(self, outfile='$outdir/covariance.png', comp_order='ZNE', crosscovariance=False, style='k', width=2, plot_stations=None, plot_components=None):
	"""
	Plots the covariance functions on whose basis is the data covariance matrix generated
	
	:param outfile: path to file for plot output; if ``None`` plots to the screen
	:type outfile: string, optional
	:param comp_order: order of component in the plot, supported are 'ZNE' (default) and 'NEZ'
	:type comp_order: string, optional
	:param crosscovariance: if ``True`` plots also the crosscovariance between components
	:param crosscovariance: bool, optional
	:param style: line style
	:param width: line width
	:param plot_stations: list of stations to plot; if ``None`` plots all stations
	:type plot_stations: list or None, optional
	:param plot_components: list of components to plot; if ``None`` plots all components
	:type plot_components: list or None, optional
	"""
	if not len(self.cova.Cf):
		raise ValueError('Covariance functions not calculated or not saved. Run "covariance_matrix(save_covariance_function=True)" first.')
	data = self.data.data_shifts[self.MT.centroid['shift_idx']]
	
	plot_stations, comps, f, ax, ea = self.plot_seismo_backend_1(plot_stations, plot_components, comp_order, crosscomp=crosscovariance, yticks=False, ylabel=None)
	
	dt = 1. / self.data.samprate
	t = np.arange(-np.floor(self.cova.Cf_len/2) * dt, (np.floor(self.cova.Cf_len/2)+0.5) * dt, dt)
	COMPS = (1,3)[crosscovariance]
	for sta in plot_stations:
		r = plot_stations.index(sta)
		for comp in comps:
			c = comps.index(comp)
			for C in range(COMPS): # if crosscomp==False: C = 0
				d = self.cova.Cf[sta][(comp,C)[crosscovariance],comp]
				#if len(t) != len(d): # DEBUG
					#t = np.arange(-np.floor(len(d)/2) * dt, (np.floor(len(d)/2)+0.5) * dt, dt) # DEBUG
					#print(len(d), len(t)) # DEBUG
				if type(d)==np.ndarray and self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
					color = style
					if len(t) != len(d):
						t = np.arange(-np.floor(len(d)/2) * dt, (np.floor(len(d)/2)+0.5) * dt, dt)
					ax[COMPS*r+C,c].plot(t, d, color=style, linewidth=width)
				else:
					ax[COMPS*r+C,c].plot([0],[0], 'w', linewidth=0)
		if crosscovariance:
			ax[3*r,  0].set_ylabel(' \n Z ')
			ax[3*r+1,0].set_ylabel(data[sta][0].stats.station + '\n N ')
			ax[3*r+2,0].set_ylabel(' \n E ')
	outfile = outfile.replace('$outdir', self.outdir)
	self.plot_seismo_backend_2(outfile, plot_stations, comps, ax, yticks=False, extra_artists=ea)
	self.plots['covariance_function'] = outfile

def plot_noise(self, outfile='$outdir/noise.png', comp_order='ZNE', obs_style='k', obs_width=2, plot_stations=None, plot_components=None):
	"""
	Plots the noise records from which the covariance matrix is calculated together with the inverted data
	
	:param outfile: path to file for plot output; if ``None`` plots to the screen
	:type outfile: string, optional
	:param comp_order: order of component in the plot, supported are 'ZNE' (default) and 'NEZ'
	:type comp_order: string, optional
	:param obs_style: line style
	:param obs_width: line width
	:param plot_stations: list of stations to plot; if ``None`` plots all stations
	:type plot_stations: list or None, optional
	:param plot_components: list of components to plot; if ``None`` plots all components
	:type plot_components: list or None, optional
	"""
	samprate = self.data.samprate
	
	plot_stations, comps, f, ax, ea = self.plot_seismo_backend_1(plot_stations, plot_components, comp_order)
	
	t = np.arange(0, (self.data.npts_slice-0.5) / samprate, 1. / samprate)
	d_max = 0
	for sta in plot_stations:
		r = plot_stations.index(sta)
		for comp in comps:
			d = self.data.data_shifts[self.MT.centroid['shift_idx']][sta][comp][0:len(t)]
			c = comps.index(comp)
			if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
				color = obs_style
				d_max = max(max(d), -min(d), d_max)
			else:
				color = 'gray'
			ax[r,c].plot(t, d, color, linewidth=obs_width)
			if len(self.data.noise[sta]) > comp:
				NPTS = len(self.data.noise[sta][comp].data)
				T = np.arange(-NPTS * 1. / samprate, -0.5 / samprate, 1. / samprate)
				ax[r,c].plot(T, self.data.noise[sta][comp], color, linewidth=obs_width)
				if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
					d_max = max(max(self.data.noise[sta][comp]), -min(self.data.noise[sta][comp]), d_max)
	ax[-1,0].set_ylim([-d_max, d_max])
	ymin, ymax = ax[r,c].get_yaxis().get_view_interval()
	for r in range(len(plot_stations)):
		for i in range(len(comps)):
			l4 = ax[r,i].add_patch(mpatches.Rectangle((-NPTS/samprate, -ymax), NPTS/samprate, 2*ymax, color=(1.0, 0.6, 0.4))) # (x,y), width, height
			l5 = ax[r,i].add_patch(mpatches.Rectangle((0, -ymax), self.data.npts_slice/samprate, 2*ymax, color=(0.7, 0.7, 0.7)))
	ea.append(f.legend((l4, l5), ('$C_D$', 'inverted'), 'lower center', bbox_to_anchor=(0.5, 1.-0.0066*len(plot_stations)), ncol=2, fontsize='small', fancybox=True, handlelength=3, handleheight=1.2)) # , borderaxespad=0.1
	ea.append(f.text(0.1, 1.06-0.004*len(plot_stations), 'x', color='white', ha='center', va='center'))
	outfile = outfile.replace('$outdir', self.outdir)
	self.plot_seismo_backend_2(outfile, plot_stations, comps, ax, extra_artists=ea)
	self.plots['noise'] = outfile
	
def plot_spectra(self, outfile='$outdir/spectra.png', comp_order='ZNE', plot_stations=None, plot_components=None):
	"""
	Plots spectra of inverted data, standardized data, and before-event noise together
	
	:param outfile: path to file for plot output; if ``None`` plots to the screen
	:type outfile: string, optional
	:param comp_order: order of component in the plot, supported are 'ZNE' (default) and 'NEZ'
	:type comp_order: string, optional
	:param plot_stations: list of stations to plot; if ``None`` plots all stations
	:type plot_stations: list or None, optional
	:param plot_components: list of components to plot; if ``None`` plots all components
	:type plot_components: list or None, optional
	"""
	if not len(self.cova.LT) and not len(self.cova.LT3):
		raise ValueError('Covariance matrix not set. Run "covariance_matrix()" first.')
	data = self.data.data_shifts[self.MT.centroid['shift_idx']]
	npts = self.data.npts_slice
	samprate = self.data.samprate

	plot_stations, comps, fig, ax, ea = self.plot_seismo_backend_1(plot_stations, plot_components, comp_order, yticks=False, xlabel='frequency [Hz]', ylabel='amplitude spectrum [m/s]')
	
	#plt.yscale('log')
	ax3 = np.empty_like(ax)
	fmin = np.zeros_like(ax, dtype=float)
	fmax = np.zeros_like(fmin)
	for i in range(len(plot_stations)):
		for j in range(len(comps)):
			#ax[i,j].set_yscale('log')
			ax3[i,j] = ax[i,j].twinx()
			#ax3[i,j].set_yscale('log')
	ax3[0,0].get_shared_y_axes().join(*ax3.flatten().tolist())

	dt = 1./samprate
	DT = 0.5*dt
	f = np.arange(0, samprate*0.5 * (1-0.5/npts), samprate / npts)
	D_filt_max = 0
	for sta in plot_stations:
		r = plot_stations.index(sta)
		SYNT = {}
		comps_used = 0
		for comp in comps:
			d = data[sta][comp][0:npts]
			d_filt = d.copy()
			c = comps.index(comp)
			if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
				if self.cova.LT3:
					d_filt = np.zeros(npts)
					x1 = -npts
					for COMP in comps:
						if not self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[COMP]]:
							continue
						x1 += npts; x2 = x1+npts
						y1 = comps_used*npts; y2 = y1+npts
						d_filt += np.dot(self.cova.LT3[sta][y1:y2, x1:x2], data[sta][COMP].data[0:npts])
				else:
					d_filt = np.dot(self.cova.LT[sta][comp], d)
				comps_used += 1
				fmin[r,c] = self.inp.stations[sta]['fmin']
				fmax[r,c] = self.inp.stations[sta]['fmax']
			ax[r,c].tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
			ax[r,c].yaxis.offsetText.set_visible(False) 
			ax3[r,c].get_yaxis().set_visible(False)
			if self.inp.stations[sta][{0:'useZ', 1:'useN', 2:'useE'}[comp]]:
				noise = self.data.noise[sta][comp]
				NPTS = len(noise)
				NOISE  = np.sqrt(np.square(np.real(np.fft.fft(noise))*DT)*npts*dt / (NPTS*DT))
				f2 = np.arange(0, samprate*1. * (1-0.5/NPTS), samprate*2 / NPTS)
				D      = np.absolute(np.real(np.fft.fft(d))*dt)
				D_filt = np.absolute(np.real(np.fft.fft(d_filt))*dt)
				D_filt_max = max(D_filt_max, max(D_filt))
				l_d,     = ax[r,c].plot(f, D[0:len(f)],          'k', linewidth=2, zorder=2)
				l_filt, = ax3[r,c].plot(f, D_filt[0:len(f)],     'r', linewidth=1, zorder=3)
				l_noise, = ax[r,c].plot(f2, NOISE[0:len(f2)], 'gray', linewidth=4, zorder=1)
			else:
				ax[r,c].plot([0],[0], 'w', linewidth=0)
	#y3min, y3max = ax3[-1,0].get_yaxis().get_view_interval()
	ax3[-1,0].set_ylim([0, D_filt_max])
	#print (D_filt_max, y3max, y3min)
	align_yaxis(ax[0,0], ax3[0,0])
	ax[0,0].set_xlim(0, self.data.fmax*1.5)
	#ax[0,0].set_xscale('log')
	#f.legend((l4, l5), ('$C_D$', 'inverted'), 'upper center', ncol=2, fontsize='small', fancybox=True)
	ea.append(fig.legend((l_d, l_filt, l_noise), ('data', 'standardized data (by $C_D$)', 'noise'), loc='lower center', bbox_to_anchor=(0.5, 1.-0.0066*len(plot_stations)), ncol=3, numpoints=1, fontsize='small', fancybox=True, handlelength=3)) # , borderaxespad=0.1
	ea.append(fig.text(0.1, 1.06-0.004*len(plot_stations), 'x', color='white', ha='center', va='center'))
	ymin, ymax = ax[r,c].get_yaxis().get_view_interval()
	for r in range(len(plot_stations)):
		for c in range(len(comps)):
			if fmax[r,c]:
				ax[r,c].add_artist(Line2D((fmin[r,c], fmin[r,c]), (0, ymax), color='g', linewidth=1))
				ax[r,c].add_artist(Line2D((fmax[r,c], fmax[r,c]), (0, ymax), color='g', linewidth=1))
	outfile = outfile.replace('$outdir', self.outdir)
	self.plot_seismo_backend_2(outfile, plot_stations, comps, ax, yticks=False, extra_artists=ea)
	self.plots['spectra'] = outfile

def plot_seismo_backend_1(self, plot_stations, plot_components, comp_order, crosscomp=False, sharey=True, yticks=True, title_prefix='', xlabel='time [s]', ylabel='velocity [m/s]'):
	"""
	The first part of back-end for functions :func:`plot_seismo`, :func:`plot_covariance_function`, :func:`plot_noise`, :func:`plot_spectra`. There is no need for calling it directly.
	"""
	data = self.data.data_shifts[self.MT.centroid['shift_idx']]
	
	plt.rcParams.update({'font.size': 22})
	
	if not plot_stations:
		plot_stations = range(self.inp.nr)
	if plot_components:
		comps = plot_components
	elif comp_order == 'NEZ':
		comps = [1, 2, 0]
	else:
		comps = [0, 1, 2]
	
	COMPS = (1,3)[crosscomp]
	f, ax = plt.subplots(len(plot_stations)*COMPS, len(comps), sharex=True, sharey=('row', True)[sharey], figsize=(len(comps)*6, len(plot_stations)*2*COMPS))
	if len(plot_stations)==1 and len(comps)>1: # one row only
		ax = np.reshape(ax, (1,len(comps)))
	elif len(plot_stations)>1 and len(comps)==1: # one column only
		ax = np.reshape(ax, (len(plot_stations),1))
	elif len(plot_stations)==1 and len(comps)==1: # one cell only
		ax = np.array([[ax]])

	for c in range(len(comps)):
		ax[0,c].set_title(title_prefix+data[0][comps[c]].stats.channel[2])

	for sta in plot_stations:
		r = plot_stations.index(sta)
		ax[r,0].set_ylabel(data[sta][0].stats.station + u"\n{0:1.0f} km, {1:1.0f}°".format(self.inp.stations[sta]['dist']/1000, self.inp.stations[sta]['az']), fontsize=16)
		#SYNT = {}
		#comps_used = 0
		for comp in comps:
			c = comps.index(comp)
			for C in range(COMPS): # if crosscomp==False: C = 0
				ax[COMPS*r+C,c].set_frame_on(False)
				ax[COMPS*r+C,c].locator_params(axis='x',nbins=7)
				ax[COMPS*r+C,c].tick_params(labelsize=16)
				if c==0:
					if yticks:
						ax[r,c].ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
						ax[r,c].get_yaxis().tick_left()
					else:
						ax[COMPS*r+C,c].tick_params(axis='y', which='both', left=False, right=False, labelleft=False)
						ax[COMPS*r+C,c].yaxis.offsetText.set_visible(False) 
				else:
					ax[COMPS*r+C,c].get_yaxis().set_visible(False)
				if r == len(plot_stations)-1 and C==COMPS-1:
					ax[COMPS*r+C,c].get_xaxis().tick_bottom()
				else:
					ax[COMPS*r+C,c].get_xaxis().set_visible(False)
	extra_artists = []
	if xlabel:
		extra_artists.append(f.text(0.5, 0.04+0.002*len(plot_stations), xlabel, ha='center', va='center'))
	if ylabel:
		extra_artists.append(f.text(0.04*(len(comps)-1)-0.02, 0.5, ylabel, ha='center', va='center', rotation='vertical'))
	return plot_stations, comps, f, ax, extra_artists

def plot_seismo_backend_2(self, outfile, plot_stations, comps, ax, yticks=True, extra_artists=None):
	"""
	The second part of back-end for functions :func:`plot_seismo`, :func:`plot_covariance_function`, :func:`plot_noise`, :func:`plot_spectra`. There is no need for calling it directly.
	"""
	xmin, xmax = ax[0,0].get_xaxis().get_view_interval()
	ymin, ymax = ax[-1,0].get_yaxis().get_view_interval()
	if yticks:
		for r in range(len(plot_stations)):
			ymin, ymax = ax[r,0].get_yaxis().get_view_interval()
			ymax = np.round(ymax,int(-np.floor(np.log10(ymax)))) # round high axis limit to first valid digit
			ax[r,0].add_artist(Line2D((xmin, xmin), (0, ymax), color='black', linewidth=1))
			ax[r,0].yaxis.set_ticks((0., ymax))  
	for c in range(len(comps)):
		ax[-1,c].add_artist(Line2D((xmin, xmax), (ymin, ymin), color='black', linewidth=2))
	if outfile:
		if extra_artists:
			plt.savefig(outfile, bbox_extra_artists=extra_artists, bbox_inches='tight')
			#plt.savefig(outfile, bbox_extra_artists=(legend,))
		else:
			plt.savefig(outfile, bbox_inches='tight')
	else:
		plt.show()
	plt.clf()
	plt.close('all')
