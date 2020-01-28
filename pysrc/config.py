import configparser
# from dotted_dict import DottedDict
import os, sys


class Config(configparser.ConfigParser):
    """
    Class the stores config.ini file in top-level
    directory.
    """

    # config_file_path = os.path.join(sys.path[0], 'config.ini')
    config_file_path = os.path.join(os.getenv("HOME"), "pasi/config.ini")
    """
    relative path to config file based on 
    where main.py is called.
    """
    def __init__(self):
        super(Config, self).__init__(self)
        self.read(self.config_file_path)

        # self.d = DottedDict({s: dict(self.items(s)) for s in self.sections()})

    def dump(self):
        with open(self.config_file_path, "w") as conf:
            self.write(conf)

    def pasi(self, section):
        """
        Returns section values of PASI header in config.ini

        Input: str
        return: str
        """

        return self['PASI'][section]

    def lisc(self, section):
        """
        Returns section values of lisc header in config.ini
        
        Input: str
        return: str
        """
        return self['LISC'][section]

    def sim_server(self, section):
        """
        Returns section values of sim_server header in config.ini
        
        Input: str
        return: str
        """
        return self['SIM_SERVER'][section]

    def switches(self, section):
        """
        returns section values of switches header in config.ini
        """
        return self['SWITCHES'][section]

    def update_switches(self, section, value, dump=True):
        """
        updates a field in switches section
        """

        self['SWITCHES'][section] = value
        if dump:
            self.dump()

    # def dotted_dict(self):
    #     return self.d
