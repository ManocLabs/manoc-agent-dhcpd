from manoc_agents.dhcp import DHCPConfParser, DHCPLeasesParser

SAMPLE_LEASES="""
lease 192.168.10.1 {
    starts 6 2010/01/06 00:40:00;
    ends 6 2010/01/06 12:40:00;
    hardware ethernet 00:11:22:33:44:55;
    uid 00:00:00:00:00:00;
    client-hostname "example-host1";
}

lease 192.168.10.2 {
    starts 6 2009/12/25 01:00:00;
    ends 6 2009/12/25 13:00:00;
    hardware ethernet 00:aa:22:33:44:55;
    uid 00:00:00:00:00:00;
    client-hostname "example-host2";
}

"""

class TestParsers:
    def test_conf_parser(self):
        parser = DHCPConfParser()
        #reservations = parser.parse_reservation()

        assert parser
    def test_leases_parser(self):

        class MyParser(DHCPLeasesParser):
            def read(self, filename):
                self._text = SAMPLE_LEASES
            
        parser = MyParser()
        parser.read('dummy')
        leases = parser.parse_leases()
        assert(len(leases) == 2)
