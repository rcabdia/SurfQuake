import os

from loc_flow_tools import root_dir
from surfquake.loc_flow_tools.internal import RealManager

if __name__ == '__main__':
    p_dir = os.path.join(os.path.dirname(root_dir), "demo", "Pick")
    station = os.path.join(os.path.dirname(root_dir), "demo", "Data", "station.dat")
    ttime = os.path.join(os.path.dirname(root_dir), "demo", "REAL", "tt_db", "ttdb.txt")

    real_handler = RealManager(pick_dir=p_dir, station_file=station, time_travel_table_file=ttime)
    real_handler.latitude_center = 42.75
    # real_handler.configure_real(RealD(day=14, month=10, year=2016, lat_center=42.75))
    print(real_handler.stations)
    # print(real_handler._buffer_data_from_real())
    for events_info in real_handler:
        print(events_info)
        print(events_info.events_date)

    real_handler.save()
    real_handler.compute_t_dist()
