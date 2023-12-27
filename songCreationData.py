class SongCreationData:
    def __init__(self,logger):
        self.song_description = ""
        self.theme = ""
        self.melody = ""
        self.rhythm = ""
        self.lyrics = ""
        self.structure = ""
        self.segments = {}
        self.total_duration = "120"
        self.arrangements = ""
        self.sonicpi_code = ""
        self.review = ""
        self.album_url = ""
        self.logger = logger

    def set_parameter(self, param_name, value):
        if hasattr(self, param_name):
            setattr(self, param_name, value)

    def get_parameter(self, param_name):
        return getattr(self, param_name, None)

    def print_attributes(self):
        self.logger.info("------------------------ start logging parameters ------------------------")
        for attr in self.__dict__:
            attr_value = getattr(self, attr)
            self.logger.info(f"{attr} : {attr_value}")
        self.logger.info("------------------------- end logging parameters -------------------------")

    def update_parameters_from_response(self, response_data):
        for key in response_data:
            if hasattr(self, key):
                # Check if the attribute is a dictionary (or a nested structure)
                if isinstance(response_data[key], dict):
                    # If the attribute already exists and is a dictionary, update it
                    if isinstance(getattr(self, key), dict):
                        getattr(self, key).update(response_data[key])
                    else:
                        # If the attribute does not exist or is not a dictionary, set it directly
                        setattr(self, key, response_data[key])
                else:
                    # If the attribute is not a dictionary, set it directly
                    setattr(self, key, response_data[key])
        self.print_attributes()