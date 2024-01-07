from surfquakecore.moment_tensor.sq_isola_tools import BayesianIsolaCore
from surfquakecore.moment_tensor.structures import MomentTensorInversionConfig, StationConfig, InversionParameters


class BayesianIsolaGUICore:
    def __init__(self, bayesian_isola: BayesianIsolaCore, model, entities, parameters):
        """

        :param bayesianIslacore:
        :param db:
        """
        self.model = model
        self.entities = entities
        self.parameters = parameters
        self.bayesian_isola = bayesian_isola

    def __get_mti_config(self, event_info):
        mti_config = MomentTensorInversionConfig(
            origin_date=event_info.origin_time,
            latitude=event_info.latitude,
            longitude=event_info.longitude,
            depth_km=event_info.depth,
            magnitude=event_info.mw,
            stations=[StationConfig(name=".", channels=["."])],
            inversion_parameters=InversionParameters(
                earth_model_file=self.parameters['earth_model'],
                location_unc=self.parameters['location_unc'],
                time_unc=self.parameters['time_unc'],
                depth_unc=self.parameters['depth_unc'],
                source_duration=self.parameters['source_duration'],
                rupture_velocity=self.parameters['rupture_velocity'],
                min_dist=self.parameters['min_dist'],
                max_dist=self.parameters['max_dist'],
                source_type=self.parameters['source_type']
            ),
        )
        return mti_config

    def run_inversion(self):
        for (i, entity) in enumerate(self.entities):
            try:
                event_info = self.model.find_by(latitude=entity[0].latitude, longitude=entity[0].longitude,
                            depth=entity[0].depth, origin_time=entity[0].origin_time)

                if event_info.mw is None:
                    # might be users has not ru magnitude module but wants to do an inversion
                    event_info.mw =3.0

                mti_config = self.__get_mti_config(event_info)
                print("Running inversion ", event_info.date, event_info.latitude, event_info.longitude, event_info.depth,
                      event_info.mw)
                self.bayesian_isola.run_inversion(mti_config)
            except:
                print("Failed Inversion of event ", event_info.date, event_info.latitude, event_info.longitude, event_info.depth,
                      event_info.mw)