from optparse import OptionParser
from manoc_agents.dhcp import DHCPAgent, DHCPAgentConfig

def main():

    # parse command line options
    parser = OptionParser()
    parser.add_option("-c", "--config-file", dest="config_file",
                  help="read configuration from FILE", metavar="FILE")
    (options, args) = parser.parse_args()

    
    #read configuration
    config = DHCPAgentConfig(config_file = options.config_file)
    
    server_name = config.server_name
    
    agent = DHCPAgent(config)
    agent.update_leases()
    agent.update_reservations()
    

if __name__ == '__main__':
  main()




