from manoc_agents.dhcp import DHCPConfParser, DHCPLeasesParser

import os.path


def test_conf_parser():
    print "CURDIR", os.path.curdir
    parser = DHCPConfParser()
    parser.read(os.path.join('tests', 'resources' ,'reservation.example'))
    reservations = parser.parse_reservation()
    
    assert len(reservations) == 10
    assert reservations[0].name == 'PC021010097'
    assert reservations[0].hwaddr == '00:00:00:ac:00:7a'
    assert reservations[0].ipaddr == '172.21.10.97'
    assert reservations[0].hostname == 'PC021010097.mydomain.org'
    
def test_leases_parser():
    parser = DHCPLeasesParser()
    parser.read(os.path.join('tests', 'resources' ,'dhcpd.leases'))
    leases = parser.parse_leases()
    assert len(leases) == 35

    assert leases[0].hwaddr == '00:00:00:00:00:00'
