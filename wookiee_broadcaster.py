#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 1.51
@date: 28/08/2022
'''

import socket
import logging
import threading
import argparse
import subprocess
import signal
import ipaddress

##logging configuration block
logger_file_handler = logging.FileHandler('wookiee_broadcaster.log', encoding='utf-8')
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
logger_file_handler.setFormatter(logging.Formatter(logger_format))
#logging level for other modules
logging.basicConfig(format=logger_format, level=logging.ERROR) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
#logging level for current logger
logger.setLevel(logging.INFO) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.addHandler(logger_file_handler)

#constants
BROADCAST_ADDRESS = '255.255.255.255'
RECV_BUFFER_SIZE = 4096
INTF_SOCKOPT_REF = 25

def sigterm_handler(signum, frame):
    logger.info('Stopping wookiee_broadcaster due to SIGTERM...')
    raise SystemExit(0)

def wookiee_broadcaster(input_intf, input_ip, output_intf, output_ip, output_netmask, port):
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    receiver.setsockopt(socket.SOL_SOCKET, INTF_SOCKOPT_REF, bytes(input_intf, 'utf-8'))
    receiver.bind((BROADCAST_ADDRESS, port))
    
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    broadcaster.setsockopt(socket.SOL_SOCKET, INTF_SOCKOPT_REF, bytes(output_intf, 'utf-8'))
    broadcaster.bind((output_ip, port))
    
    output_network = ipaddress.IPv4Interface(f'{output_ip}/{output_netmask}').network
    
    while True:
        data, addr = receiver.recvfrom(RECV_BUFFER_SIZE)
        logger.debug(f'WB >>> {addr[0]}:{addr[1]} sent a packet on {input_intf}')
        #logger.debug(f'WB >>> {addr[0]}:{addr[1]} sent: {data}')
        
        if addr[0] != input_ip and ipaddress.IPv4Address(addr[0]) not in output_network:
            logger.info(f'WB >>> Replicating a packet from {input_intf}/{addr[0]}:{addr[1]} on {output_intf}/{BROADCAST_ADDRESS}:{port}')
            broadcaster.sendto(data, (BROADCAST_ADDRESS, port))
            
#catch SIGTERM and exit gracefully
signal.signal(signal.SIGTERM, sigterm_handler)

parser = argparse.ArgumentParser(description=('*** The Wookiee Broadcaster *** Replicates broadcast packets across network interfaces. '
                                              'Useful for TCP/IP and UDP/IP based multiplayer LAN games enjoyed using VPN.'), add_help=False)

required = parser.add_argument_group('required arguments')
group = required.add_mutually_exclusive_group()
optional = parser.add_argument_group('optional arguments')

required.add_argument('-i', '--input', help='Input interface name for listening to broadcast packets.', required=True)
required.add_argument('-o', '--output', help='Output interface name, on which the broadcast requests will be replicated.', required=True)
group.add_argument('-p', '--port', help='Port on which the broadcaster will listen for packets and also the replication port.')
group.add_argument('-r', '--range', help=('A range of ports on which the broadcaster will listen for packets and also the replication ports. '
                                         'The accepted format is <start_port>:<end_port>.'))

#reposition the standard -h flag at the bottom, in a custom optional section
optional.add_argument('-h', '--help', action='help', help='show this help message and exit')
optional.add_argument('-b', '--bidirectional', help='Replicate broadcasts coming from the output interface to the input interface as well',
                      action='store_true')

args = parser.parse_args()

if args.input == args.output:
    logger.critical('It\'s not wise to upset a wookiee...')
    raise SystemExit(1)

input_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.input}' + ' | grep -w inet | awk \'{print $2 " " $4;}\'', 
                                             shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
input_ip, input_netmask = input_ip_query_subprocess.communicate()[0].decode('utf-8').strip().split()
logger.debug(f'Input IP address is: {input_ip}')
logger.debug(f'Input IP netmask is: {input_netmask}')

if input_ip == '':
    logger.critical('Invalid input interface. Please retry with the correct interface name.')
    raise SystemExit(2)

output_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.output}' + ' | grep -w inet | awk \'{print $2 " " $4;}\'', 
                                              shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
output_ip, output_netmask = output_ip_query_subprocess.communicate()[0].decode('utf-8').strip().split()
logger.debug(f'Output IP address is: {output_ip}')
logger.debug(f'Output IP netmask is: {output_netmask}')

if output_ip == '':
    logger.critical('Invalid output interface. Please retry with the correct interface name.')
    raise SystemExit(3)
        
if args.port is not None:
    port = int(args.port)
    
    logger.info(f'Starting wookiee_broadcaster - listening on {args.input}/{BROADCAST_ADDRESS}:{port}, '
                f'broadcasting on {args.output}/{output_ip}:{port}')
    wookiee_thread = threading.Thread(target=wookiee_broadcaster, 
                                      args=(args.input, input_ip, args.output, output_ip, output_netmask, port), 
                                      daemon=True)
    wookiee_thread.start()
    
    if args.bidirectional:
        logger.info('*** Running in bidirectional mode ***')
        logger.info(f'Starting wookiee_broadcaster - listening on {args.output}/{BROADCAST_ADDRESS}:{port}, '
                    f'broadcasting on {args.input}/{input_ip}:{port}')
        wookiee_thread_b = threading.Thread(target=wookiee_broadcaster, 
                                            args=(args.output, output_ip, args.input, input_ip, input_netmask, port), 
                                            daemon=True)
        wookiee_thread_b.start()
    
    try:
        wookiee_thread.join()
    except KeyboardInterrupt:
        logger.info('Stopping wookiee_broadcaster due to keyboard interrupt...')
    
elif args.range is not None:
    start_port, end_port = [int(port) for port in args.range.split(':')]
    
    if end_port <= start_port:
        logger.critical('Incorrect use of the port range parameter. Please run -h to see needed parameters.')
        raise SystemExit(4)
    
    numeral_port_range = range(start_port, end_port + 1)
    
    wookiee_threads = [None for i in range(len(numeral_port_range))]
    wookiee_threads_b = wookiee_threads
    thread_counter = 0
    
    for range_port in numeral_port_range:
        logger.info(f'Starting wookiee_broadcaster - listening on {args.input}/{BROADCAST_ADDRESS}:{range_port}, '
                    f'broadcasting on {args.output}/{output_ip}:{range_port}')
        wookiee_threads[thread_counter] = threading.Thread(target=wookiee_broadcaster, 
                                                           args=(args.input, input_ip, args.output, output_ip, output_netmask, range_port),
                                                           daemon=True)
        wookiee_threads[thread_counter].start()
        
        if args.bidirectional:
            logger.info('*** Running in bidirectional mode ***')
            logger.info(f'Starting wookiee_broadcaster - listening on {args.output}/{BROADCAST_ADDRESS}:{range_port}, '
                        f'broadcasting on {args.input}/{input_ip}:{range_port}')
            wookiee_threads_b[thread_counter] = threading.Thread(target=wookiee_broadcaster, 
                                                                 args=(args.output, output_ip, args.input, input_ip, input_netmask, range_port),
                                                                 daemon=True)
            wookiee_threads_b[thread_counter].start()
            
        thread_counter += 1
        
    try:
        for wookiee_thread in wookiee_threads:
            wookiee_thread.join()
    except KeyboardInterrupt:
        logger.info('Stopping wookiee_broadcaster due to keyboard interrupt...')
    
else:
    logger.critical('Missing port or port range parameters. Please run -h to see needed parameters.')
    raise SystemExit(5)
