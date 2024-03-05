# This is an old version to run travel time calculation of REAL


# import multiprocessing
# import os
# from dataclasses import dataclass
# from typing import List, Optional
# from multiprocessing import Pool as ThreadPool
#
# import numpy as np
# from obspy.core.event import Arrival
# from obspy.taup import TauPyModel
# from obspy.taup.tau import Arrivals
# from obspy.taup.taup_create import build_taup_model
#
# from ..caching.caching import Cache
# from ..models import global_model_path
# from ..utils import HashUtils
#
#
# @dataclass
# class ArrivalPSData:
#     dist: float
#     depth: float
#     p_name: str
#     s_name: str
#     p_time: float
#     s_time: float
#     p_ray_param: float
#     s_ray_param: float
#     p_h_slowness: float
#     s_h_slowness: float
#
#     def __str__(self):
#         return f"{self.dist} {self.depth} {self.p_time} {self.s_time} {self.p_ray_param} {self.s_ray_param} " \
#                f"{self.p_h_slowness} {self.s_h_slowness} {self.p_name} {self.s_name}"
#
#
# class TimeTravelHandler:
#
#     def __init__(self, model_path: Optional[str] = None, **kwargs):
#         """
#         Handles the generation of travel timetable
#
#         :param model_path: The .np file to load. If no file is given then a default global model will be used.
#         :param kwargs:
#         :keyword max_angular_distance: The max angular distance in degree. Default = 1.4
#         :keyword max_depth: The max depth in km. Default = 20.
#         :keyword delta_dist: The interval that max_angular_distance will be divided. Default = 0.01
#         :keyword delta_depth: The interval that max_depth will be divided. Default = 1
#         """
#
#         self.phase_list: List[str] = ["P", "p", "S", "s"]
#
#         self._model: Optional[TauPyModel] = None
#         self._model_hash: str = ''  # used to know if model has changed
#         if not model_path:
#             # loads default model
#             self.load_model(global_model_path)
#         else:
#             self.load_model(model_path)
#
#         self._max_angular_distance = float(kwargs.get('max_angular_distance', 1.4))  # dist range in deg.
#         self._max_depth = float(kwargs.get('max_depth', 20.))  # depth in km
#
#         self._delta_dist = float(kwargs.get('delta_dist', 0.01))  # dist interval, be exactly divided by dist
#         self._delta_depth = float(kwargs.get('delta_depth', 1.))  # depth interval, be exactly divided by dep
#
#         n_depth = int(self._max_depth / self._delta_depth) + 1
#         self._depths = [d * self._delta_depth for idx, d in enumerate(range(0, n_depth, 1))]
#         n_angular_dist = int(self._max_angular_distance / self._delta_dist) + 1
#         self._angular_distances = [d * self._delta_dist for idx, d in enumerate(range(1, n_angular_dist, 1))]
#
#         self._tt_data: List[ArrivalPSData] = []
#         self._cache = Cache()
#
#     @property
#     def tt_data(self):
#         return self._tt_data
#
#     @property
#     def model(self):
#         return self._model
#
#     @property
#     def cache_id(self):
#         return HashUtils.hash_args(self._max_angular_distance, self._max_depth,
#                                    self._delta_dist, self._delta_depth, self._model_hash)
#
#     def load_model(self, filename: str):
#         """
#         Load the TauPyModel from the .nd file.
#
#         :param filename: The path to your model .nd
#         :return:
#         """
#         build_taup_model(filename, verbose=False)
#         model_name = os.path.basename(filename).replace('.nd', '')
#         self._model = TauPyModel(model=model_name)
#         self._model_hash = HashUtils.create_hash(filename)
#
#     @staticmethod
#     def _parse_arrival_ray_h_slowness(arr: Arrival):
#         ray_param = arr.ray_param * 2. * np.pi / 360.
#         h_slowness = -1. * (ray_param / 111.19) / np.tan(arr.takeoff_angle * np.pi / 180.)
#         return ray_param, h_slowness
#
#     def _compute_travel_time(self, dist: float, depth: float):
#
#         arrivals: Arrivals = self.model.get_travel_times(source_depth_in_km=depth, distance_in_degree=dist,
#                                                          phase_list=self.phase_list)
#         p_arrivals = [a for a in arrivals if a.name.lower() == 'p']
#         s_arrivals = [a for a in arrivals if a.name.lower() == 's']
#         if len(s_arrivals) == 0:
#             raise ValueError("No S travel time, most likely low velocity issue")
#         if len(p_arrivals) == 0:
#             raise ValueError("No P travel time, most likely low velocity issue")
#
#         # gets the first p and s wave
#         p_arr, s_arr = p_arrivals[0], s_arrivals[0]
#         # parse ray and slowness
#         p_ray_param, p_h_slowness = self._parse_arrival_ray_h_slowness(p_arr)
#         s_ray_param, s_h_slowness = self._parse_arrival_ray_h_slowness(s_arr)
#
#         return ArrivalPSData(
#             dist=dist,
#             depth=depth,
#             s_name=s_arr.name,
#             p_name=p_arr.name,
#             s_time=s_arr.time,
#             p_time=p_arr.time,
#             p_h_slowness=p_h_slowness,
#             s_h_slowness=s_h_slowness,
#             p_ray_param=p_ray_param,
#             s_ray_param=s_ray_param,
#         )
#
#     def clear(self):
#         self._tt_data = []
#
#     def clear_cache(self):
#         self._cache.clear_cache(self.cache_id)
#
#     def save(self, output: str):
#         with open(output, 'w') as f:
#             all([f.write(f"{data}\n") for data in self._tt_data])
#
#     def generate_travel_time_table(self):
#         self.clear()
#
#         # try to get from cache first
#         self._tt_data = self._cache.get_cache(self.cache_id)
#         if self._tt_data is not None:
#             return self._tt_data
#
#         workers = max(2, (multiprocessing.cpu_count() - 1))
#         with ThreadPool(workers) as pool:
#             res = [pool.apply_async(self._compute_travel_time, args=(dist, depth), )
#                    for depth in self._depths for dist in self._angular_distances]
#
#             self._tt_data = [r.get() for r in res]
#             # cache data
#             self._cache.cache_array(self.cache_id, self._tt_data)
#
#
# if __name__ == '__main__':
#     import time
#     from .. import out_data_dir
#
#     t0 = time.time()
#     tth = TimeTravelHandler()
#     tth.generate_travel_time_table()
#     tth.save(os.path.join(out_data_dir, 'ttdb.txt'))
#     tf = time.time()
#     print(f"Process took: {tf - t0:0.2f} seconds")
