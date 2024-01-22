import pandas as pd
from surfquake.db import db

dir_path = '/Users/roberto/Documents/SurfQuake'
db.set_db_url("sqlite:///{}/surfquake.db".format(dir_path))
db.start()
from surfquake.Gui.Models.sql_alchemy_model import SQLAlchemyModel
from surfquake.db.models import EventLocationModel, FirstPolarityModel, MomentTensorModel, PhaseInfoModel
df = pd.read_csv("/Users/roberto/Documents/SurfQuake/surfquake/magnitudes_output/magnitudes_output.txt")
print(df)
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
filters = [EventLocationModel.latitude >= 15., EventLocationModel.longitude < 10]
entities = EventLocationModel.find_by_filter(filters=filters)
#event_model = EventLocationModel.find_by(latitude=origin.latitude, longitude=origin.longitude,
#                                                 depth=origin.depth, origin_time=origin.time.datetime)