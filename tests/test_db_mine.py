import os
from surfquake.db import db


dir_path = '/Users/roberto/Documents/SurfQuake'
db.set_db_url("sqlite:///{}/isp_test.db".format(dir_path))
db.start()
from surfquake.Gui.Models.sql_alchemy_model import SQLAlchemyModel
from surfquake.db.models import EventLocationModel, FirstPolarityModel, MomentTensorModel, PhaseInfoModel
el_columns = [getattr(EventLocationModel, c)
                      for c in EventLocationModel.__table__.columns.keys()[1:]]

pi_columns = [getattr(PhaseInfoModel, c)
                       for c in PhaseInfoModel.__table__.columns.keys()[1:]]

fp_columns = [getattr(FirstPolarityModel, c)
                      for c in FirstPolarityModel.__table__.columns.keys()[2:]]

mti_columns = [getattr(MomentTensorModel, c)
                       for c in MomentTensorModel.__table__.columns.keys()[2:]]

columns = [*el_columns, *fp_columns, *mti_columns]

col_names = ['Origin Time', 'Transformation', 'RMS',
                     'Latitude', 'Longitude', 'Depth', 'Uncertainty',
                     'Max. Hor. Error', 'Min. Hor. Error', 'Ellipse Az.',
                     'No. Phases', 'Az. Gap', 'Max. Dist.', 'Min. Dist.',
                     'Mb', 'Mb Error', 'Ms', 'Ms Error', 'Ml', 'Ml Error',
                     'Mw', 'Mw Error', 'Mc', 'Mc Error', 'Strike', 'Dip',
                     'Rake', 'Misfit', 'Az. Gap', 'Stat. Pol. Count', 'Latitude_mti', 'Longitude_mti', 'Depth_mti',
                     'VR', 'CN', 'dc', 'clvd', 'iso', 'Mw_mt', 'Mo', 'Strike_mt', 'dip_mt', 'rake_mt', 'mrr', 'mtt',
                     'mpp',
                     'mrt', 'mrp', 'mtp']

entities = [EventLocationModel, FirstPolarityModel, MomentTensorModel]
model = SQLAlchemyModel(entities, columns, col_names)
model.addJoinArguments(EventLocationModel.first_polarity, isouter=True)
model.addJoinArguments(EventLocationModel.moment_tensor, isouter=True)


## filter by query ###

mag = EventLocationModel.ml.between(2, 4)
model.setFilter(mag)
model.revertAll()

entities = model.getEntities()

lat = []
lon = []
depth = []
mag = []
for j in entities:
     lat.append(j[0].latitude)
     lon.append(j[0].longitude)
     depth.append(j[0].depth)
     event_info = EventLocationModel.find_by(id=j[0].id, get_first=True)
     phase_info = event_info.phase_info # A list with phase picking info
     sta = phase_info[0].station_code





#col_names = ['id', 'event_info_id', 'station_code', 'phase', 'time']


###### model phases ########
# columns = [*pi_columns]
# entity_pi = PhaseInfoModel.find_by(event_info_id='20220202143717', get_first=True)


######


# for j in entities:
#     lat.append(j[0].latitude)
#     lon.append(j[0].longitude)
#     depth.append(j[0].depth)

for j in entities:
    print(j[0].id)
