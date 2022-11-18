#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 1.70
@date: 18/11/2022
'''

import socket
import logging
import multiprocessing
import argparse
import subprocess
import signal
import ipaddress
from time import sleep

##logging configuration block
logger_format = '%(asctime)s %(levelname)s >>> %(message)s'
#logging level for other modules
logging.basicConfig(format=logger_format, level=logging.ERROR) #DEBUG, INFO, WARNING, ERROR, CRITICAL
logger = logging.getLogger(__name__)
#logging level for current logger
logger.setLevel(logging.INFO) #DEBUG, INFO, WARNING, ERROR, CRITICAL

#constants
BROADCAST_ADDRESS = '255.255.255.255'
#broadcast UDP packets are not typically all that large
RECV_BUFFER_SIZE = 2048 #bytes
PACKET_QUEUE_SIZE = 4 #packets
#allow spawned processes to fully initialize before the process is started
PROCESS_SPAWN_WAIT_INTERVAL = 0.1 #seconds

def sigterm_handler(signum, frame):
    #exceptions may happen here as well due to logger syncronization mayhem on shutdown
    try:
        logger.debug('Stopping Wookiee Broadcaster due to SIGTERM...')
    except:
        pass
            
    raise SystemExit(0)

def sigint_handler(signum, frame):
    #exceptions may happen here as well due to logger syncronization mayhem on shutdown
    try:
        logger.debug('WU >>> Stopping Wookiee Broadcaster child process due to SIGINT...')
    except:
        pass
            
    raise SystemExit(0)

def wookiee_receiver(process_no, input_intf, input_ip, 
                     output_network, port, exit_event, queue):
    #catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)
    
    logger.info(f'WB P{process_no} >>> Starting receiver worker process...')
    
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, input_intf)
    receiver.bind((BROADCAST_ADDRESS, port))
    
    try:
        while not exit_event.is_set():
            data, addr = receiver.recvfrom(RECV_BUFFER_SIZE)
            logger.debug(f'WB P{process_no} >>> Received a packet from {addr[0]}:{addr[1]}...')
            #logger.debug(f'WB P{process_no} >>> {addr[0]}:{addr[1]} sent: {data}')
            
            if addr[0] != input_ip and ipaddress.IPv4Address(addr[0]) not in output_network:
                queue.put(data)
            else:
                logger.debug(f'WB P{process_no} >>> Ignoring a packet not intended for replication...')
    except:
        pass        
    finally:
        receiver.close()
        
    logger.info(f'WB P{process_no} >>> Stopped receiver worker process.')
    
def wookiee_broadcaster(process_no, output_intf, output_ip, 
                        port, exit_event, queue):
    #catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)
    
    logger.info(f'WB P{process_no} >>> Starting broadcaster worker process...')
    
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, output_intf)
    broadcaster.bind((output_ip, port))
    
    try:
        while not exit_event.is_set():
            data = queue.get()
            
            logger.info(f'WB P{process_no} >>> Replicated a packet to {BROADCAST_ADDRESS}:{port}')
            broadcaster.sendto(data, (BROADCAST_ADDRESS, port))
    except:
        pass
    finally:
        broadcaster.close()
            
    logger.info(f'WB P{process_no} >>> Stopped broadcaster worker process.')
            
if __name__=="__main__":
    #catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    
    bidirectional_mode = False
    
    parser = argparse.ArgumentParser(description=('*** The Wookiee Broadcaster *** Replicates broadcast packets across network interfaces. '
                                                  'Useful for TCP/IP and UDP/IP based multiplayer LAN games enjoyed using VPN.'), add_help=False)
    
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')
    
    required.add_argument('-i', '--input', help='Input interface name for listening to broadcast packets.', required=True)
    required.add_argument('-o', '--output', help='Output interface name, on which the broadcast requests will be replicated.', required=True)
    required.add_argument('-p', '--ports', help=('Port(s) on which the broadcaster will listen for packets and also the replication port(s).'
                                              'Can also be specified as a port range, in the format of <start_port>:<end_port>.'), 
                          required=True)
    
    #reposition the standard -h flag at the bottom, in a custom optional section
    optional.add_argument('-h', '--help', action='help', help='show this help message and exit')
    optional.add_argument('-b', '--bidirectional', help='Replicate broadcasts coming from the output interface to the input interface as well',
                          action='store_true')
    
    args = parser.parse_args()
    
    input_intf = bytes(args.input, 'utf-8')
    logger.debug(f'WB >>> input_intf: {args.input}')
    output_intf = bytes(args.output, 'utf-8')
    logger.debug(f'WB >>> output_intf: {args.output}')
    
    if input_intf == output_intf:
        logger.critical('WB >>> It\'s not wise to upset a wookiee...')
        raise SystemExit(1)
    
    try:
        input_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.input}' + ' | grep -w inet | awk \'{print $2 " " $4;}\'', 
                                                     shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        input_ip, input_netmask = input_ip_query_subprocess.communicate()[0].decode('utf-8').strip().split()
        
        logger.debug(f'WB >>> input_ip: {input_ip}')
        logger.debug(f'WB >>> input_netmask: {input_netmask}')
    
        input_network = ipaddress.IPv4Interface(f'{input_ip}/{input_netmask}').network
        
        if input_ip == '':
            logger.critical(f'Invalid input interface {args.input}. Please retry with a valid interface name.')
            raise SystemExit(2)
    except:
        logger.critical(f'Invalid input interface {args.input}. Please retry with a valid interface name.')
        raise SystemExit(2)
    
    try:
        output_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.output}' + ' | grep -w inet | awk \'{print $2 " " $4;}\'', 
                                                      shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        output_ip, output_netmask = output_ip_query_subprocess.communicate()[0].decode('utf-8').strip().split()
        logger.debug(f'WB >>> output_ip: {output_ip}')
        logger.debug(f'WB >>> output_netmask: {output_netmask}')
        
        output_network = ipaddress.IPv4Interface(f'{output_ip}/{output_netmask}').network
        
        if output_ip == '':
            logger.critical(f'WB >>> Invalid output interface {args.output}. Please retry with a valid interface name.')
            raise SystemExit(3)
    except:
        logger.critical(f'WB >>> Invalid output interface {args.output}. Please retry with a valid interface name.')
        raise SystemExit(3)
             
    #handle ranges as default, and single ports as a special case
    try:
        ports = [int(port) for port in args.ports.split(':')]
    except:
        logger.critical('WB >>> Invalid port value(s) specified. Please retry with valid port value(s).')
        raise SystemExit(4)
    
    if len(ports) > 1:
        try:
            start_port, end_port = ports[:]
        except:
            logger.critical('WB >>> Laugh it up, fuzzball...')
            raise SystemExit(5)
    
        if end_port <= start_port:
            logger.critical('WB >>> Incorrect use of the port range parameter. Please run -h to see needed parameters.')
            raise SystemExit(6)
        
        port_range = range(start_port, end_port + 1)
        port_range_len = len(port_range)
        
    #if only a single port is specified, store that in the range
    else:
        port_range = ports
        port_range_len = 1
        
    if args.bidirectional:
        logger.info('*** Running in bidirectional mode ***')
                
        bidirectional_mode = True
        #double the length of all elements if bidirectional mode is enabled
        port_range_len *= 2
    
    wookiee_receiver_procs_list = [None] * port_range_len
    wookiee_broadcaster_procs_list = [None] * port_range_len
    
    broadcast_queue_list = [multiprocessing.Queue(PACKET_QUEUE_SIZE) for i in range(port_range_len)]
    exit_event = multiprocessing.Event()
    exit_event.clear()
    
    proc_counter = 0
    
    for port in port_range:
        logger.info(f'WB P{proc_counter + 1} >>> Starting Wookiee Broadcaster - listening on {args.input}/{BROADCAST_ADDRESS}:{port}, '
                    f'broadcasting on {args.output}/{output_ip}:{port}')
        wookiee_receiver_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_receiver, 
                                                                            args=(proc_counter + 1, input_intf, input_ip, 
                                                                                  output_network, port, exit_event, 
                                                                                  broadcast_queue_list[proc_counter]),
                                                                            daemon=True)
        wookiee_receiver_procs_list[proc_counter].start()
        
        sleep(PROCESS_SPAWN_WAIT_INTERVAL)
        
        wookiee_broadcaster_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_broadcaster, 
                                                                               args=(proc_counter + 1, output_intf, output_ip, 
                                                                                     port, exit_event, broadcast_queue_list[proc_counter]),
                                                                               daemon=True)
        wookiee_broadcaster_procs_list[proc_counter].start()
        
        sleep(PROCESS_SPAWN_WAIT_INTERVAL)
        
        if bidirectional_mode:
            proc_counter += 1
            
            logger.info(f'WB P{proc_counter + 1} >>> Starting Wookiee Broadcaster - listening on {args.output}/{BROADCAST_ADDRESS}:{port}, '
                        f'broadcasting on {args.input}/{input_ip}:{port}')
            wookiee_receiver_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_receiver, 
                                                                                args=(proc_counter + 1, output_intf, output_ip, 
                                                                                      input_network, port, exit_event,
                                                                                      broadcast_queue_list[proc_counter]),
                                                                                daemon=True)
            wookiee_receiver_procs_list[proc_counter].start()
            
            sleep(PROCESS_SPAWN_WAIT_INTERVAL)
            
            wookiee_broadcaster_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_broadcaster, 
                                                                                   args=(proc_counter + 1, input_intf, input_ip, 
                                                                                         port, exit_event, broadcast_queue_list[proc_counter]),
                                                                                   daemon=True)
            wookiee_broadcaster_procs_list[proc_counter].start()
            
            sleep(PROCESS_SPAWN_WAIT_INTERVAL)
            
        proc_counter += 1
        
    try:
        for wookiee_proc in wookiee_receiver_procs_list:
            wookiee_proc.join()
        
        for wookiee_proc in wookiee_broadcaster_procs_list:
            wookiee_proc.join()
                
    except KeyboardInterrupt:
        #not sure why a second KeyboardInterrupt gets thrown here on shutdown at times
        try:
            logger.info('WB >>> Stopping Wookiee Broadcaster due to keyboard interrupt...')
            exit_event.set()
        except KeyboardInterrupt:
            exit_event.set()
    
    logger.info('WB >>> Ruow! (Goodbye)')
    