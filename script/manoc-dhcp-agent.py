#!/usr/bin/env python

import re
import time
import ConfigParser
import json
import urllib2
import base64
import xml.dom.minidom


class PreemptiveBasicAuthHandler(urllib2.HTTPBasicAuthHandler):
    '''Preemptive basic auth.

    Instead of waiting for a 403 to then retry with the credentials,
    send the credentials if the url is handled by the password manager.
    Note: please use realm=None when calling add_password.'''

    def http_request(self, req):
        url = req.get_full_url()
        realm = None
        # this is very similar to the code from retry_http_basic_auth()
        # but returns a request object.
        user, pw = self.passwd.find_user_password(realm, url)
        if pw:
            raw = "%s:%s" % (user, pw)
            auth = 'Basic %s' % base64.b64encode(raw).strip()
            req.add_unredirected_header(self.auth_header, auth)
        return req

    https_request = http_request
    

class RequestException(IOError):
    """A generic Exception while processing the request."""

    response = None
    request = None

    def __init__(self, *args, **kwargs):        
        self.response = kwargs.pop('response', None)
        self.request = kwargs.pop('request', None)
        if self.response is not None and self.request is None:
            if hasattr(self.response, 'request'):
                self.request = self.response.request            
        super(RequestException, self).__init__(*args, **kwargs)
        
        
class HTTPError(RequestException):
    """An HTTP error occurred."""
    pass

    
class Response():
    
    def __init__(self, url, auth=None, data=None):        
        req = urllib2.Request(url)    
        if data:
            req.add_data(data)
        
        if auth is not None:
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None, url, auth[0], auth[1])
 
            auth_manager = PreemptiveBasicAuthHandler(password_manager)
            opener = urllib2.build_opener(auth_manager).open
        else:
            opener = urllib2.urlopen
      
        self.request = req
        self._opener = opener    
        self._data = None
        self._is_error = False
        self._handler = None  
        self._raise_on_http_error = False
        
    def raise_on_http_error(self):
        self._raise_on_http_error = True
        
    def code(self):
        if self._code:
            return self._code
        elif self._handler:
            return self._handler.getcode()
        else:
            return None 
            
    def header(self, name):
        return self._handler.headers.getheader(name) 
        
    def read(self):
        if self._is_error:
            return None
        if self._data is None:
            try:
                self._handler = self._opener(self.request)    
                self._data = self._handler.read() 
            except urllib2.HTTPError as e:
                self._code = e.code 
                self._is_error = True
                raise HTTPError(response=self)
            except:
                self._is_error = True
                raise  RequestException(response=self)
            if self._raise_on_http_error and self._handler.getcode() != 200:
                raise HTTPError(response=self)
        return self._data        
    
    def json(self):        
        return json.loads(self.read()) 
    
    def xml(self):
        return xml.dom.minidom.parseString(self.read())
    
def GET(url, *args, **kwargs):
    return Response(url, *args, **kwargs)

def POST(url, data, *args, **kwargs):
    kwargs['data'] = data
    return Response(url, *args, **kwargs)


class DHCPReservationEncoder(json.JSONEncoder):
 
    def default(self, obj):
        return obj.name,obj.hwaddr,obj.ipaddr,obj.hostname  


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

class  DHCPLeaseEncoder(json.JSONEncoder):
 
    def default(self, obj):
        return obj.ipaddr,self.__to_unixtime(obj.start),\
               self.__to_unixtime(obj.end),obj.status,\
               obj.macaddr.lower(),obj.hostname    

    def __to_unixtime(self,date):
        return int(time.mktime(date))

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
              


def main():
    #read configuration
    config = DHCPAgentConfig()
    server_name = config._config.get('Common', 'server_name')

    parser = DHCPConfParser()
    parser.read(config.dhcp_conf_file)
    reservations = parser.parse_reservation()
    print "Reservations"
    print json.dumps(reservations,cls=DHCPReservationEncoder)


    parser = DHCPLeasesParser()
    parser.read(config.dhcp_leases_file)
    leases = parser.parse_leases()
    print "Leases"
    #print '\n'.join([ str(l) for l in leases])
    print json.dumps(leases,cls=DHCPLeaseEncoder)


    

if __name__ == '__main__':
  main()




