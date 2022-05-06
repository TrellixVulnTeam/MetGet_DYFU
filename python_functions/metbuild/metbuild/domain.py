class Domain:
    def __init__(self, name, service, json):
        from metbuild.windgrid import WindGrid
        self.__name = name
        self.__service = service
        self.__json = json
        self.__grid = WindGrid(self.__json)
        self.__storm = None
        self.__valid = True
        self.__advisory = None
        self.__basin = None
        self.__storm_year = None
        self.__get_storm()

    def advisory(self):
        return self.__advisory

    def year(self):
        return self.__storm_year

    def basin(self):
        return self.__basin

    def storm(self):
        return self.__storm

    def name(self):
        return self.__name

    def service(self):
        return self.__service

    def grid(self):
        return self.__grid

    def json(self):
        return self.__json

    def __get_storm(self):
        if self.service() == "hwrf" or self.service() == "nhc":
            if "storm" in self.__json:
                self.__storm = self.__json["storm"]
            else: 
                self.__valid = False
        else:
            self.__storm = None
        if self.service() == "nhc":
            if "advisory" in self.__json:
                self.__advisory = self.__json["advisory"]
            else:
                self.__valid = False
            if "basin" in self.__json:
                self.__basin = self.__json["basin"]
            else:
                self.__valid = False
            if "year" in self.__json:
                self.__storm_year = self.__json["year"]
            else:
                self.__valid = False

