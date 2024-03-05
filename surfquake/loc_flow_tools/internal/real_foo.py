from __future__ import annotations
import math

# This is an old attept to translate REAL c code into python

#import os
#from dataclasses import dataclass
# from typing import List
#
# from surfquake.loc_flow_tool import root_dir
# from surfquake.loc_flow_tools.internal import Station, RealV, TimeTravelTable, RealR
#
# import numpy as np
#
# MAXTIME = 2700000.00
# rad = math.pi / 180.0
# sph = 1.0 / 298.257
#
#
# @dataclass
# class Trig:
#     trig: float = 1.e8
#     weight: float = 0.
#     amp: float = 0.
#
#     def __lt__(self, other):
#         if not isinstance(other, Trig):
#             other = 0 if np.isnan(other) else other
#             return self.trig < other
#         return self.trig < other.trig
#
#     def __le__(self, other):
#         if not isinstance(other, Trig):
#             other = 0 if np.isnan(other) else other
#             return self.trig <= other
#         return self.trig <= other.trig
#
#     def __gt__(self, other):
#         if not isinstance(other, Trig):
#             other = 0 if np.isnan(other) else other
#             return self.trig > other
#         return self.trig > other.trig
#
#     def __ge__(self, other):
#         if not isinstance(other, Trig):
#             other = 0 if np.isnan(other) else other
#             return self.trig >= other
#         return self.trig >= other.trig
#
#
# def projections(x1: float, x2: float):
#     return math.sin(x1) * math.cos(x2), math.sin(x1) * math.sin(x2),  math.cos(x1), math.sin(x2), -math.cos(x2)
#
#
# def ddistaz(stalat: float, stalon: float, evtlat: float, evtlon: float):
#     scolat = math.pi / 2. - math.atan((1. - sph) * (1. - sph) * math.tan(stalat * rad))
#     ecolat = math.pi / 2. - math.atan((1. - sph) * (1. - sph) * math.tan(evtlat * rad))
#     slon = stalon * rad
#     elon = evtlon * rad
#     a, b, c, d, e = projections(scolat, slon)
#     aa, bb, cc, dd, ee = projections(ecolat, elon)
#     delta = math.acos(a * aa + b * bb + c * cc)
#     delta = delta / rad
#
#     g, h, k = -c * e,  c * d, -math.sin(scolat)
#     gg, hh, kk = -cc * ee, cc * dd, -math.sin(ecolat)  # TODO this is not used?
#     rhs1 = (aa - d) * (aa - d) + (bb - e) * (bb - e) + cc * cc - 2.
#     rhs2 = (aa - g) * (aa - g) + (bb - h) * (bb - h) + (cc - k) * (cc - k) - 2.
#     dbaz = math.atan2(rhs1, rhs2)
#     if dbaz < 0.0:
#         dbaz += 2 * math.pi
#     baz = dbaz / rad
#     if math.fabs(baz - 360.) < .00001:
#         baz = 0.0
#
#     return delta, baz
#
#
# def read_stations(station_file: str) -> List[Station]:
#     stations = []
#     with open(station_file, 'r') as f:
#         # expect to be lon, lat, network, station, component, elevation
#         while v := f.readline():
#             lon, lat, network, station, component, elevation = v.strip().split()
#             stations.append(
#                 Station(float(lon), float(lat), network, station, component, float(elevation))
#
#             )
#     return stations
#
#
# def read_pick(pick_file: str):
#     if not os.path.isfile(pick_file):
#         return []
#
#     with open(pick_file, 'r') as f:
#         while line := f.readline().strip():
#             trig, weight, amp = line.split()
#             yield float(trig), float(weight), float(amp)
#
#
# def read_ttime(ttime_file: str):
#     if not os.path.isfile(ttime_file):
#         return []
#
#     with open(ttime_file, 'r') as f:
#         while line := f.readline().strip():
#             g_dist, depth, p_time, s_time, p_ray_p, s_ray_p, \
#                 p_hslow, s_hslow, p_phase, s_phase = line.split()
#             yield float(g_dist), float(depth), float(p_time), float(s_time), \
#                 float(p_ray_p), float(s_ray_p), float(p_hslow), float(s_hslow), p_phase, s_phase
#
#
# def has_pick(pick_dir: str, st: Station) -> bool:
#     pick_p_file = os.path.join(pick_dir, f"{st.network}.{st.name}.P.txt")
#     pick_s_file = os.path.join(pick_dir, f"{st.network}.{st.name}.S.txt")
#     if not (os.path.isfile(pick_p_file) or os.path.isfile(pick_s_file)):
#         return False
#     return True
#
#
#
# def run_real(station_file: str, pick_dir: str, ttime_file: str, lat_center: float):
#     # ref: https://github.com/Dal-mzhang/REAL/blob/master/REAL_userguide_July2021.pdf
#     # igrid=1 when RealG is passed on
#     real_v = RealV(6.2, 3.3)
#     is_zero_elevation = real_v.station_elevation_correction == 0
#     real_r = RealR(0.1, 20, 0.04, 2, 5)
#     dx, rx = real_r.search_grid_size, real_r.search_range_h
#
#     trx: float = 0.
#     GCarc0: float = 180.
#
#     # If no specified distance range, make sure to use distance covered by travel time table
#     if (trx > 0 and GCarc0 == 180) or (trx > 0 and GCarc0 > trx - 0.05):
#         GCarc0 = trx - 0.05
#
#     # read station information
#     stations = read_stations(station_file)
#     # maximum number of P/S picks recorded at one station
#     nps: int = 20000
#
#     # clear stations with no pick
#     stations = [st for st in stations if has_pick(pick_dir, st)]
#     nst = len(stations)
#     TGP = np.zeros((nst, nps), dtype=object)  # default
#     TGS = np.zeros((nst, nps), dtype=object)  # default
#     TGP[:] = Trig()
#     TGS[:] = Trig()
#
#     stlamax, stlamin = max(stations, key=lambda s: s.lat).lat, min(stations, key=lambda s: s.lat).lat
#     stlomax, stlomin = max(stations, key=lambda s: s.lon).lon, min(stations, key=lambda s: s.lon).lon
#     distmax, baz = ddistaz(stlamin, stlomin, stlamax, stlomax)
#     GCarc0 = min(GCarc0, distmax)
#
#     # Load time travel table
#     TB: List[TimeTravelTable] = []
#     for v in read_ttime(ttime_file):
#         TB.append(TimeTravelTable(*v))
#
#     # populate arrays TGP, TGS
#     for i, stat in enumerate(stations):
#         pick_p_file = os.path.join(pick_dir, f"{stat.network}.{stat.name}.P.txt")
#         pick_s_file = os.path.join(pick_dir, f"{stat.network}.{stat.name}.S.txt")
#
#         for j, v in enumerate(read_pick(pick_p_file)):
#             trig, weight, amp = v
#             if trig > MAXTIME:
#                 trig = 1.0e8
#             TGP[i][j] = Trig(trig=trig, weight=weight, amp=amp)
#
#         for j, v in enumerate(read_pick(pick_s_file)):
#             trig, weight, amp = v
#             if trig > MAXTIME:
#                 trig = 1.0e8
#             TGS[i][j] = Trig(trig=trig, weight=weight, amp=amp)
#
#         if is_zero_elevation:
#             stat.elevation = 0.
#
#     # find where max trig happens
#     max_tgp = np.max(np.argmax(TGP, axis=1))
#     max_tgs = np.max(np.argmax(TGS, axis=1))
#     # max number of picks
#     nps = max(max_tgs, max_tgp)
#     # slice data and sort
#     TGP, TGS = np.sort(TGP[:, 0:nps:]), np.sort(TGS[:, 0:nps:])
#     print(TGP)
#
#     dx2 = dx / math.cos(lat_center * rad)
#     rx2 = rx / math.cos(lat_center * rad)
#     dx1, rx1 = dx, rx
#
#     # ptw = sqrt((dx1 * 111.19) * (dx1 * 111.19) + (dx1 * 111.19) * (dx1 * 111.19) + dh * dh) / vp0
#     # stw = sqrt((dx1 * 111.19) * (dx1 * 111.19) + (dx1 * 111.19) * (dx1 * 111.19) + dh * dh) / vs0
#     #
#     # if (tint < nrt * stw)
#     #     tint = nrt * stw;
#     # fprintf(stderr, "p-window= nrt*ptw = %.2f * %.2f sec = %.2f sec\n", nrt, ptw,
#     #         nrt * ptw);
#     # fprintf(stderr, "s-window= nrt*stw = %.2f * %.2f sec = %.2f sec\n", nrt, stw,
#     #         nrt * stw);
#     # fprintf(stderr, "event-window= %.2f sec\n", tint);
#     # fprintf(stderr, "Largest distance %.2f degree was used\n", GCarc0)
#     #
#     # dxmin = nxd * GCarc0 * 111.19;
#     # fprintf(stderr, "events with nearest event-station distance > nxd * GCarc0 will be discarded\n")
#     # fprintf(stderr, "i.e., %.2f * %.2f deg. = %.2f km\n", nxd, GCarc0, dxmin)
#
#
#     print(stations)
#
#
# if __name__ == '__main__':
#     p_dir = os.path.join(os.path.dirname(root_dir), "demo", "Pick", "20161013")
#     station = os.path.join(os.path.dirname(root_dir), "demo", "Data", "station.dat")
#     ttime = os.path.join(os.path.dirname(root_dir), "demo", "REAL", "tt_db", "ttdb.txt")
#     run_real(station, p_dir, ttime, 42.7)


