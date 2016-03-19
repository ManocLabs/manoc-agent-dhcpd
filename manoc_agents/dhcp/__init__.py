#!/usr/bin/env python

import re
import time
import ConfigParser
import json
from manoc_agents.common import requests
from manoc_agents.common.requests import HTTPError
class DHCPReservation(object):
   
    def __init__(self, name, hostname, ipaddr, hwaddr):
        self.name = name 
        self.hwaddr = hwaddr
        self.ipaddr = ipaddr
        self.hostname = hostname or ''
       
    def __str__(self):
        return "%s at %s(%s)" % (self.hwaddr, self.ipaddr, self.hostname)

    def __repr__(self):
        return "DHCPReservation(%s,%s,%s,%s)" % \
            (self.name, self.hostname, self.ipaddr, self.hwaddr)
    
    class Encoder(json.JSONEncoder):
        def default(self, obj):
            return obj.name,obj.hwaddr,obj.ipaddr,obj.hostname  


class DHCPConfParser(object):
    '''A Simple class to parse dhcp leases and reservations'''
   
    res_re = re.compile(r"""
        \s*host\s+(?P<name>[\w\d-]+)\s*{
        (?:
          \s*
          (?:
            hardware\ ethernet\s+(?P<hwaddr>(?:[0-9a-f]{2}:){5}[0-9a-f]{2})
          |
            fixed-address\s+(?P<ipaddr>(?:\d{1,3}\.){3}\d{1,3})
          |
            option\ host-name\s+ "(?P<hostname>[^"]+)"
          |
            [^;}]+
          )
          ;
        )+
        \s*}\s*""",
        re.X)   

    include_re = re.compile(r"""\s*include\s+"(?P<filename>[^"]+)"\s*;""");

    def read(self, filename, parse_includes=True):
        text = open(filename,'r').read()

        if parse_includes:
            for match in self.include_re.finditer(text):
                incl_file = match.group('filename')
                text += open(incl_file, 'r').read()
        self._text = text


    def parse_reservation(self):
        result_list = []

        for match in self.res_re.finditer(self._text):
            result_list.append( DHCPReservation(**match.groupdict()) )
        return result_list

class DHCPLeases(object):
   
    def __init__(self, ipaddr, start, end, status, macaddr, hostname):
        self.ipaddr   = ipaddr 
        self.start    = time.strptime(start, "%Y/%m/%d %H:%M:%S")
        self.end      = time.strptime(end, "%Y/%m/%d %H:%M:%S")
        self.status   = status or ''
        self.macaddr  = macaddr or ''
        self.hostname = hostname or ''
   
    def __str__(self):
        return "%s(%s) %s: start:%s end:%s status:%s" % \
            (self.ipaddr, self.macaddr, self.hostname, self.start, self.end, self.status)

    def __repr__(self):
        return "DHCPLeases(%s,%s,%s,%s,%s,%s)" % \
            (self.ipaddr,  self.start,  self.end,  \
             self.status, self.macaddr, self.hostname)

    class Encoder(json.JSONEncoder):
 
        def default(self, obj):
            return obj.ipaddr,self.__to_unixtime(obj.start),\
                self.__to_unixtime(obj.end),obj.status,\
                obj.macaddr.lower(),obj.hostname    

        def __to_unixtime(self,date):
            return int(time.mktime(date))

    
class DHCPLeasesParser(object):
    leases_re = re.compile(r"""
        \s*lease\s
        (?P<ipaddr>(?:\d{1,3}\.){3}\d{1,3})\s*{
        (?:
          \s*
          (?:
              starts\s+\d\s+(?P<start>\d{4}\/\d{2}\/\d{2}\s\d{2}:\d{2}:\d{2})
            |
              ends\s+\d\s+(?P<end>\d{4}\/\d{2}\/\d{2}\s\d{2}:\d{2}:\d{2})
        
            |
              binding\ state\s+(?P<status>\w+)
            |
              hardware\ \S+\ (?P<macaddr>(?:[0-9a-f]{2}:){5}[0-9a-f]{2})
            |
              client-hostname\s+"(?P<hostname>.*)"
            |
              [^;}]+
          )
          ;
        )+
        \s*}\s*""", re.X)
   

    def read(self, filename):
        self._text = open(filename,"r").read()

    def parse_leases(self):
        result_list = []

        for match in self.leases_re.finditer(self._text):
            result_list.append( DHCPLeases(**match.groupdict()) )
        return result_list

       
class DHCPAgentConfig(object):
   
    def __init__(self, filepath=None):
        if not filepath:
            filepath = '/etc/manoc/conf.ini'

        config = ConfigParser.RawConfigParser()
        config.read(filepath)
        self._config = config

    @property
    def dhcp_conf_file(self):
        path = self._config.get('DHCP', 'dhcpd_conf')
        if not path:
            path = '/etc/dhcp/dhcpd.conf'
        return path

    @property
    def dhcp_leases_file(self):
        path = self._config.get('DHCP', 'leases_file')
        if not path:
            path = "/var/lib/dhcpd/dhcpd.leases"
        return path

    @property
    def server_name(self):
        hostname = self._config.get('Common', 'server_name')
        if not hostname:
            import os
            hostname = os.uname()[1]
        return hostname
  
    @property
    def username(self):
       return self._config.get('DHCP', 'username')
    @property
    def password(self):
       return self._config.get('DHCP', 'password')
    @property
    def start_url(self):
       return self._config.get('DHCP', 'start_url')

class DHCPAgent(object):
    
    UPDATE_STATUS_SUCCESS = 'success'
    UPDATE_STATUS_WORKING = 'working'
    UPDATE_STATUS_ERROR   = 'error'
    UPDATE_STATUS_UNKNOWN = 'unknown'
    UPDATE_STATUS_TIMEOUT = 'timeout'
    UPDATE_STATUS_HTTP_ERROR = 'connection error'

    def __init__(self,config):
        self.config = config

    def start_update(self):
        """Call the  service to update all the profiles, return True if the
        service returns success.
        """
        parser = DHCPLeasesParser()
        parser.read(self.config.dhcp_leases_file)
        leases = parser.parse_leases()
        data   = "\""+self.config.server_name + "\" , "+ \
                       json.dumps(leases,cls=DHCPLeases.Encoder)
        try:
            url = self.config.start_url
            print("calling url %s", url)
            auth=(self.config.username, self.config.password)
            r = requests.GET(url, auth, data)
          
            data = r.json()
            
            print("response: %s", str(data))
            if data.get('successful', False):
                self.status = self.UPDATE_STATUS_WORKING
                return True
            else:
                self.status = self.ERROR
                return False
        except HTTPError:
                self.status = self.UPDATE_STATUS_HTTP_ERROR
                return False

