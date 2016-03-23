import re
import time

class DHCPReservation(object):
   
    def __init__(self, name, hostname, ipaddr, hwaddr):
        self.name = name 
        self.hwaddr = hwaddr
        self.ipaddr = ipaddr
        self.hostname = hostname or ''
       
    def __str__(self):
        return "%s at %s(%s)" % (self.hwaddr, self.ipaddr, self.hostname)
  

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
   
    def __init__(self, ipaddr, start, end, status, hwaddr, hostname):
        self.ipaddr   = ipaddr 
        self.start    = time.strptime(start, "%Y/%m/%d %H:%M:%S")
        self.end      = time.strptime(end, "%Y/%m/%d %H:%M:%S")
        self.status   = status or ''
        self.hwaddr  = hwaddr or ''
        self.hostname = hostname or ''
   
    def __str__(self):
        return "%s(%s) %s: start:%s end:%s status:%s" % \
            (self.ipaddr, self.hwaddr, self.hostname, self.start, self.end, self.status)

    def __repr__(self):
        return "DHCPLeases(%s,%s,%s,%s,%s,%s)" % \
            (self.ipaddr,  self.start,  self.end,  \
             self.status, self.hwaddr, self.hostname)

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
              hardware\ \S+\ (?P<hwaddr>(?:[0-9a-f]{2}:){5}[0-9a-f]{2})
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

       
