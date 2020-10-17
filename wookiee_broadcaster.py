#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 1.3
@date: 18/10/2020
'''

import socket
import logging
import threading
import argparse
import subprocess

##logging configuration block
log_file_full_path = 'wookiee_broadcaster.log'
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
logger_file_handler = logging.FileHandler(log_file_full_path, mode='w', encoding='utf-8')
logger_file_formatter = logging.Formatter(logger_format)
logger_file_handler.setFormatter(logger_file_formatter)
logging.basicConfig(format=logger_format, level=logging.INFO) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
logger.addHandler(logger_file_handler)

#constants
BROADCAST_ADDRESS = '255.255.255.255'
RECV_BUFFER_SIZE = 4096
INTF_SOCKOPT_REF = 25

def wookiee_broadcaster(input_intf, output_intf, output_ip, port):
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    receiver.setsockopt(socket.SOL_SOCKET, INTF_SOCKOPT_REF, bytes(input_intf, 'utf-8'))
    receiver.bind((BROADCAST_ADDRESS, port))
    
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    broadcaster.setsockopt(socket.SOL_SOCKET, INTF_SOCKOPT_REF, bytes(output_intf, 'utf-8'))
    broadcaster.bind((output_ip, port))
    
    while True:
        data, addr = receiver.recvfrom(RECV_BUFFER_SIZE)
        logger.debug(f'WB >>> {addr[0]}:{addr[1]} sent: {data}')
        
        if addr[0] != output_ip:
            logger.info(f'WB >>> Replicating a packet received from {addr[0]}:{addr[1]} on {BROADCAST_ADDRESS}:{port}')
            broadcaster.sendto(data, (BROADCAST_ADDRESS, port))

parser = argparse.ArgumentParser(description='*** The Wookiee Broadcaster *** Replicates broadcast packets across network interfaces. \
                                             Useful for TCP/IP and UDP/IP based multiplayer LAN games enjoyed using VPN.')
optional = parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
group = required.add_mutually_exclusive_group()

required.add_argument('-i', '--input', help='Input interface name for listening to broadcast packets.', required=True)
required.add_argument('-o', '--output', help='Output interface name, on which the broadcast requests will be replicated.', required=True)
group.add_argument('-p', '--port', help='Port on which the broadcaster will listen for packets and also the replication port.')
group.add_argument('-r', '--range', help='A range of ports on which the broadcaster will listen for packets and also the replication ports. \
                                          The accepted format is <start_port>:<end_port>.')
parser.add_argument('-b', '--bidirectional', help='Replicate broadcasts coming from the output interface to the input interface as well',
                    action='store_true')

parser._action_groups.append(optional)
args = parser.parse_args()

if args.input == args.output:
    logger.error('It\'s not wise to upset a wookiee...')
    exit(1)

output_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.output}' + " | grep -w inet | awk '{print $2;}'", shell=True, stdout=subprocess.PIPE)
output_ip = output_ip_query_subprocess.communicate()[0].decode('utf-8').strip()
logger.debug(f'Output IP address is: {output_ip}')

input_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.input}' + " | grep -w inet | awk '{print $2;}'", shell=True, stdout=subprocess.PIPE)
input_ip = input_ip_query_subprocess.communicate()[0].decode('utf-8').strip()
logger.debug(f'Input IP address is: {input_ip}')
        
if args.port is not None:
    port = int(args.port)
    
    logger.info(f'Starting wookiee_broadcaster - listening on {args.input}/{BROADCAST_ADDRESS}:{port}, broadcasting on {args.output}/{output_ip}:{port}')
    wookiee_thread = threading.Thread(target=wookiee_broadcaster, args=(args.input, args.output, output_ip, port))
    wookiee_thread.setDaemon(True)
    wookiee_thread.start()
    
    if args.bidirectional:
        logger.info('*** Running in bidirectional mode ***')
        logger.info(f'Starting wookiee_broadcaster - listening on {args.output}/{BROADCAST_ADDRESS}:{port}, broadcasting on {args.input}/{input_ip}:{port}')
        wookiee_thread_b = threading.Thread(target=wookiee_broadcaster, args=(args.output, args.input, input_ip, port))
        wookiee_thread_b.setDaemon(True)
        wookiee_thread_b.start()
    
    try:
        wookiee_thread.join()
    except KeyboardInterrupt:
        pass
    
elif args.range is not None:
    start_port, end_port = [int(port) for port in args.range.split(':')]
    
    if end_port <= start_port:
        logger.error('Incorrect use of the port range parameter. Please run -h to see needed parameters.')
        exit(2)
    
    numeral_port_range = range(start_port, end_port + 1)
    
    wookiee_threads = [None for i in range(len(numeral_port_range))]
    wookiee_threads_b = wookiee_threads
    thread_counter = 0
    
    for range_port in numeral_port_range:
        logger.info(f'Starting wookiee_broadcaster - listening on {args.input}/{BROADCAST_ADDRESS}:{range_port}, broadcasting on {args.output}/{output_ip}:{range_port}')
        wookiee_threads[thread_counter] = threading.Thread(target=wookiee_broadcaster, args=(args.input, args.output, output_ip, range_port))
        wookiee_threads[thread_counter].setDaemon(True)
        wookiee_threads[thread_counter].start()
        
        if args.bidirectional:
            logger.info('*** Running in bidirectional mode ***')
            logger.info(f'Starting wookiee_broadcaster - listening on {args.output}/{BROADCAST_ADDRESS}:{range_port}, broadcasting on {args.input}/{input_ip}:{range_port}')
            wookiee_threads_b[thread_counter] = threading.Thread(target=wookiee_broadcaster, args=(args.output, args.input, input_ip, range_port))
            wookiee_threads_b[thread_counter].setDaemon(True)
            wookiee_threads_b[thread_counter].start()
            
        thread_counter += 1
        
    try:
        for wookiee_thread in wookiee_threads:
            wookiee_thread.join()
    except KeyboardInterrupt:
        pass
    
else:
    logger.error('Missing port or port range parameters. Please run -h to see needed parameters.')
    exit(3)

logger.info("Stopping wookiee_broadcaster...")
