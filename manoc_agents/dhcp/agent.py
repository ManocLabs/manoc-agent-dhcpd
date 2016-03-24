import time
import json

from .parser import DHCPConfParser, DHCPLeasesParser

from manoc_agents.common import requests
from manoc_agents.common.requests import HTTPError
from manoc_agents.common.config import AgentConfig

class DHCPAgentConfig(AgentConfig):

    @property
    def dhcpd_conf_file(self):
        return self.get('dhcp', 'dhcpd_conf', '/etc/dhcp/dhcpd.conf')

    @property
    def dhcpd_leases_file(self):
        return self.get('dhcp', 'leases_file', '/var/lib/dhcpd/dhcpd.leases')


class DHCPAgent(object):

    MANOC_API_PATH = '/api/v1'
    MANOC_API_LEASE_PATH = MANOC_API_PATH + '/dhcp/lease'
    MANOC_API_RESERVATION_PATH = MANOC_API_PATH + '/dhcp/reservation'
    
    def __init__(self, config):
        self.config = config
        self.auth   = (self.config.username, self.config.password)

        self._leases = None
        self._reservations = None
        
    @property
    def leases(self):
        if not self._leases:
            parser = DHCPLeasesParser()
            parser.read(self.config.dhcpd_leases_file)
            self._leases = parser.parse_leases()
        return self._leases
    
    def leases_dict(self):
        return [
            {
                'hwaddr' : l.hwaddr.lower(),
                'ipaddr' : l.ipaddr,
                'start'  : int(time.mktime(l.start)),
                'end'    : int(time.mktime(l.end)),
                'hostname' : l.hostname,
                'status' : l.status
            }
            for l in self.leases
        ]

    @property
    def reservations(self):
        if not self._reservations:
            parser = DHCPConfParser()
            parser.read(self.config.dhcpd_conf_file)
            self._reservations = parser.parse_reservations()
        return self._reservations

    def reservations_dict(self):
        return [
            {
                'hwaddr'   : r.hwaddr,
                'ipaddr'   : r.ipaddr,
                'hostname' : r.hostname,
                'name'     : r.name
            }
            for r in self.reservations
        ]
    
    def update_leases(self):
        data = {
            'server' : self.config.server_name,
            'leases' : self.leases_dict()
        }
        r = self.post_to_manoc(self.MANOC_API_LEASE_PATH, data)
        return r
    
    def update_reservations(self):
        data = {
            'server' : self.config.server_name,
            'reservations' : self.reservations_dict()
        }
        r = self.post_to_manoc(self.MANOC_API_RESERVATION_PATH, data)
        return r

    def post_to_manoc(self, api_path, data):
        url = self.config.manoc_url + api_path
        r = requests.POST(url, self.auth, json=data)
        return r.json()

