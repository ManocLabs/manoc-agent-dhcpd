#!/usr/bin/env python

import time
import json

from .parser import DHCPConfParser, DHCPLeasesParser
from manoc_agents.common import requests
from manoc_agents.common.requests import HTTPError
from manoc_agents.common.config import AgentConfig

class DHCPAgentConfig(AgentConfig):

    @property
    def dhcp_conf_file(self):
        return self.get('dhcp', 'dhcpd_conf', '/etc/dhcp/dhcpd.conf')

    @property
    def dhcp_leases_file(self):
        return self.get('dhcp', 'leases_file', '/var/lib/dhcpd/dhcpd.leases')


class DHCPAgent(object):

    def __init__(self,config):
        self.config = config
        self.auth   = (self.config.username, self.config.password)

        self._leases = None
        self._reservations = None
        
    @property
    def leases(self):
        if not self._leases:
            parser = DHCPLeasesParser()
            parser.read(self.config.dhcp_leases_file)
            self._leases = parser.parse_leases()
        return self._leases
    
    def leases_dict(self):
        [
            {
                'hwaddr' : l.macaddr.lower(),
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
            parser.read(self.config.dhcp_conf_file)
            self._reservations = parser.parse_reservation()
        return self._reservations

    def reservations_dict(self):
        [
            {
                'hwaddr'   : r.hwaddr,
                'ipaddr'   : r.ipaddr,
                'hostname' : r.hostname,
                'name'     : r.name
            }
            for r in self.reservations
        ]
    
    def update_leases(self):
        lease_url = self.config.manoc_url + '/api/v1/dhcp/lease'
        data = {
            'server' : self.config.server_name,
            'leases' : self.leases_dict()
        }    
        json_data = json.dumps(data)
        r = requests.POST(lease_url, self.auth, json=data)
        return r.json()
        
    def update_reservations(self):
        conf_url = self.config.manoc_url + '/api/v1/dhcp/reservation'
        data = {
            'server' : self.config.server_name,
            'reservations' : self.reservations_dict()
        }    
        
        r = requests.POST(conf_url, self.auth, json=data)
        return r.json()

