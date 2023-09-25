class bayesian_isola_db:
    def __init__(self, metadata: dict, project: dict, parameters: dict, macro: dict):

        """
        ----------
        Parameters
        ----------
        metadata dict: information of stations
        project dict: information of seismogram data files available
        parameters: dictionary containing database entities and all GUI parameters
        """

        self.metadata = metadata
        self.project = project
        self.parameters = parameters
        self.macro = macro

    def get_info(self):
        print(self.macro)
