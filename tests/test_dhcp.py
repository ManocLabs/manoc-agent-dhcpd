from manoc_agents.dhcp import DHCPAgent, DHCPAgentConfig
from manoc_agents.dhcp.parser import  DHCPConfParser, DHCPLeasesParser

import os.path

LEASES_FILE = os.path.join('tests', 'resources' ,'dhcpd.leases')
RESERVATIONS_FILE = os.path.join('tests', 'resources' ,'reservation.example')

def test_conf_parser():
    print "CURDIR", os.path.curdir
    parser = DHCPConfParser()
    parser.read(RESERVATIONS_FILE)
    reservations = parser.parse_reservations()
    
    assert len(reservations) == 10
    assert reservations[0].name == 'PC021010097'
    assert reservations[0].hwaddr == '00:00:00:ac:00:7a'
    assert reservations[0].ipaddr == '172.21.10.97'
    assert reservations[0].hostname == 'PC021010097.mydomain.org'
    
def test_leases_parser():
    parser = DHCPLeasesParser()
    parser.read(LEASES_FILE)
    leases = parser.parse_leases()
    assert len(leases) == 35

    assert leases[0].hwaddr == '00:00:00:00:00:00'


def test_dhcp_agent():
    MOCK_USER = 'admin'
    MOCK_PASSWD = 'passwd'

    path = '/post'
    
    class MockConf(object):
        server_name = 'testserver'
        username = MOCK_USER
        password = MOCK_PASSWD
        manoc_url = 'http://manoc-server/'
        dhcpd_leases_file = LEASES_FILE
        dhcpd_conf_file = RESERVATIONS_FILE        

    class TestAgent(DHCPAgent):        
        def post_to_manoc(self, path, data):
            if path == '/api/v1/dhcp/reservation':
                assert data['reservations'] != None
                return
            if path == '/api/v1/dhcp/lease':
                assert data['leases'] != None
                return

            # cannot be here!
            assert path != None
                                
    conf = MockConf()
    agent = TestAgent(conf)
    agent.update_reservations()    
    agent.update_leases()    
