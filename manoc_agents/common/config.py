import ConfigParser
import os

class AgentConfig(object):

    def __init__(self, config_file=None):
        if not config_file:
            config_file = '/etc/manoc/conf.ini'
        config = ConfigParser.ConfigParser()
        config.read(config_file)
        self._config = config


    def get(self, section, option, default=None):
        try:
            return self._config.get(section, option)
        except ConfigParser.NoOptionError, ConfigParser.NoSectionError:
            return default  
        ## TODO exceptions
        
    @property
    def server_name(self):
        return self.get('common', 'server_name', os.uname()[1])
        
    @property
    def username(self):
        return self.get('common', 'username')
    
    @property
    def password(self):
        return self.get('common', 'password')

    @property
    def manoc_url(self):
        return self.get('common', 'manoc_url')
