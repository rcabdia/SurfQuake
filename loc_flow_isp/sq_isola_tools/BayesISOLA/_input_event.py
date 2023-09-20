#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import math
from obspy import UTCDateTime

def read_event_info(self, filename):
	"""
	Read event coordinates, magnitude, and time from a file in specified format (see below)
	
	:param filename: path to file
	:type filename: string
	
	.. rubric:: File format
	.. code-block:: none
	
		longitude  latitude
		depth
		moment_magnitude
		date [YYYYmmDD] (unused)
		hour
		minute
		second
		agency which provides this location

	.. rubric:: File example::		
	.. code-block:: none

		21.9877  38.4045
		6
		4.5
		20120425
		10
		34
		11.59
		UPSL
	
	The function also sets ``rupture_length`` to :math:`\sqrt{111 \cdot 10^M}`, where `M` is the magnitude.
	"""
	inp_event  = open(filename, 'r')
	l = inp_event.readlines()
	inp_event.close()
	e = {}
	e['lon'], e['lat'] = l[0].split()
	e['depth'] = float(l[1])*1e3
	e['mag'] = float(l[2])
	e['t'] = UTCDateTime(l[3])+int(l[4])*3600+int(l[5])*60+float(l[6])
	e['agency'] = l[7].rstrip()
	self.event = e
	self.log('\nHypocenter location:\n  Agency: {agency:s}\n  Origin time: {t:s}\n  Lat {lat:8.3f}   Lon {lon:8.3f}   Depth {d:3.1f} km'.format(t=e['t'].strftime('%Y-%m-%d %H:%M:%S'), lat=float(e['lat']), lon=float(e['lon']), d=e['depth']/1e3, agency=e['agency']))
	self.log('\nEvent info: '+filename)
	self.rupture_length = math.sqrt(111 * 10**self.event['mag'])		# M6 ~ 111 km2, M5 ~ 11 km2 		REFERENCE NEEDED

def set_event_info(self, lat, lon, depth, mag, t, agency=''):
	"""
	Sets event coordinates, magnitude, and time from parameters given to this function
	
	:param lat: event latitude
	:type lat: float
	:param lon: event longitude
	:type lon: float
	:param depth: event depth in km
	:type lat: float
	:param mag: event moment magnitude
	:type lat: float
	:param t: event origin time
	:type t: :type starttime: :class:`~obspy.core.utcdatetime.UTCDateTime` or string
	:param agency: agency which provides this location
	:type lat: string, optional
	
	Sets ``rupture_length`` to :math:`\sqrt{111 \cdot 10^M}`, where `M` is the magnitude.
	"""
	if type(t) == str:
		t = UTCDateTime(t)
	self.event = {'lat' : lat, 'lon' : lon, 'depth' : float(depth)*1e3, 'mag' : float(mag), 't' : t, 'agency' : agency}
	self.log('\nHypocenter location:\n  Agency: {agency:s}\n  Origin time: {t:s}\n  Lat {lat:8.3f}   Lon {lon:8.3f}   Depth{d:4.1f} km'.format(t=t.strftime('%Y-%m-%d %H:%M:%S'), lat=float(lat), lon=float(lon), d=float(depth), agency=agency))
	self.rupture_length = math.sqrt(111 * 10**self.event['mag'])		# M6 ~ 111 km2, M5 ~ 11 km2 		REFERENCE NEEDED

def set_source_time_function(self, type, t0=0, t1=0):
	"""
	Sets the source time function for calculating elementary seismograms.
	
	This function writes file ``green/soutype.dat``, which is read by ``green/elemse`` (function ``fsource()`` at the end of ``elemse.for``).
	"""
	icc = 1 # parameter-1 is used as number of derivatives in complex domain (1 = no derivative, 2 = a derivative etc.)
	if type in ("step", "Heaviside", "step in displacement"):
		ics = 7
		icc = 2
		description = "step in displacement"
	elif type in ("triangle", "triangular", "triangle in velocity"): # t0 needed
		ics = 4
		description = "triangle in velocity, length = {0:3.1f} s".format(t0)
	elif type in ("Bouchon", "Bouchon's smooth step"):
		ics = 2
		icc = 2
		description = "Bouchon's smooth step, length = {0:3.1f} s".format(t0)
	elif type in ("Brune", ): # t0 needed
		ics = 9
		description = "Brune, length = {0:3.1f} s".format(t0)
	# TODO source complex spectrum is given as array and written to a file (uncomment reading file 301 in elemse.for)
	self.stf_description = description
	f = open('green/soutype.dat', 'w')
	f.write("{0:d}\n{1:3.1f}\n{2:3.1f}\n{3:d}\n".format(ics, t0, t1, icc))
	f.close()
	
