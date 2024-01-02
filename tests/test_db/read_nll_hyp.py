from surfquake.Utils import read_nll_performance
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
event_file = ""
cat = read_nll_performance.read_nlloc_hyp_ISP("/Users/roberto/Documents/SurfQuake/surfquake/loc_flow_tools/"
                                              "location_aux/loc/last.hyp")

# Origin = read_nll_performance.read_nlloc_hyp_ISP('/Users/roberto/Documents/SurfQuake/surfquake/loc_flow_tools/'
#                                               'location_aux/loc/last.hyp')
# picks = Origin.events[0].picks

focal_parameters = [cat[0].origins[0]["time"], cat[0].origins[0]["latitude"],
                    cat[0].origins[0]["longitude"],
                    cat[0].origins[0]["depth"] * 1E-3]
time = cat[0].origins[0]["time"]
time = time.strftime('%m/%d/%Y %H:%M:%S.%f')
date_object = datetime.strptime(time, '%m/%d/%Y %H:%M:%S.%f')

#'02/01/2022 23:20:40.876581'
#event = cat[0]
arrivals = cat[0]["origins"][0]["arrivals"]

geodetics = {}
for arrival in arrivals:
    geodetics["distance_km"] = arrival.distance_km
    geodetics["distance_degrees"] = arrival.distance_degrees
    geodetics["azimuth"] = arrival.azimuth
    geodetics["takeoff_angle"] = arrival.takeoff_angle
    geodetics["time_weight"] = arrival.time_weight
print(geodetics)