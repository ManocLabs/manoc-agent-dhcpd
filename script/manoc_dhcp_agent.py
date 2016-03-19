from manoc_agents.dhcp import DHCPAgent
from manoc_agents.dhcp import DHCPAgentConfig

def main():
    #read configuration
    config = DHCPAgentConfig()
    server_name = config.server_name
    
    #parser = DHCPConfParser()
    #parser.read(config.dhcp_conf_file)
    #reservations = parser.parse_reservation()
    #print "Reservations"
    #print json.dumps(reservations,cls=DHCPReservation.Encoder)

    #parser = DHCPLeasesParser()
    #parser.read(config.dhcp_leases_file)
    #leases = parser.parse_leases()
    #print "Leases"
    #print '\n'.join([ str(l) for l in leases])
    #print json.dumps(leases,cls=DHCPLeases.Encoder)

    agent = DHCPAgent(config)
    agent.start_update()
    

if __name__ == '__main__':
  main()




