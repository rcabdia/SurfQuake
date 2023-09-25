class bayesian_isola_db:
    def __init__(self, model, entities, metadata: dict, project: dict, parameters: dict, macro: dict):

        """
        ----------
        Parameters
        ----------
        metadata dict: information of stations
        project dict: information of seismogram data files available
        parameters: dictionary containing database entities and all GUI parameters
        """
        self.model = model
        self.entities = entities
        self.metadata = metadata
        self.project = project
        self.parameters = parameters
        self.macro = macro

    def get_info(self):
        for j in self.entities:
            event_info = self.model.find_by(id=j[0].id, get_first=True)
            print(event_info)
            phase_info = event_info.phase_info
            print(phase_info) # A list with phase picking info
            #sta = phase_info[0].station_code #example of info
            # TODO NEEDS TO FILTER PROJECT BASED ON EVENT_INFO AND PHASE INFO
            # TODO NEEDS TO PROCESS Data
