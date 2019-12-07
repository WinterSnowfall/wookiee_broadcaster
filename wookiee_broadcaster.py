#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 0.5
@date: 7/12/2019
'''

import socket
import threading
import argparse
import subprocess
from time import sleep

def wookiee_broadcaster(input_intf, output_intf, output_ip, port):
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #receiver.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    receiver.setsockopt(socket.SOL_SOCKET, 25, bytes(input_intf, 'utf-8'))
    receiver.bind(('255.255.255.255', port))
    
    broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    #need root rights to bind to an interface, apparently
    broadcaster.setsockopt(socket.SOL_SOCKET, 25, bytes(output_intf, 'utf-8'))
    broadcaster.bind((output_ip, port))
    
    while True:
        data, addr = receiver.recvfrom(4096)
        #print(f'{addr[0]}:{addr[1]} sent: {data}')
        
        if addr[0] != output_ip:
            broadcaster.sendto(data, ('255.255.255.255', port))

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

output_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.output}' + " | grep -w inet | awk '{print $2;}'", shell=True, stdout=subprocess.PIPE)
output_ip = output_ip_query_subprocess.communicate()[0].decode('utf-8').strip()
print(f'Output IP address is: {output_ip}')

input_ip_query_subprocess = subprocess.Popen(f'ifconfig {args.input}' + " | grep -w inet | awk '{print $2;}'", shell=True, stdout=subprocess.PIPE)
input_ip = input_ip_query_subprocess.communicate()[0].decode('utf-8').strip()
print(f'Input IP address is: {input_ip}')

if args.input is None or args.output is None:
    print('Missing parameters. Please run -h to see needed parameters.')
    exit(1)
        
if args.port is not None:
    print(f'Starting wookiee_broadcaster - listening on {args.input}/255.255.255.255:{args.port}, broadcasting on {args.output}/{output_ip}:{args.port}')
    wookie_thread = threading.Thread(target=wookiee_broadcaster, args=(args.input, args.output, output_ip, int(args.port)))
    wookie_thread.setDaemon(True)
    wookie_thread.start()
    
    if args.bidirectional:
        print('*** Running in bidirectional mode ***')
        print(f'Starting wookiee_broadcaster - listening on {args.output}/255.255.255.255:{args.port}, broadcasting on {args.input}/{input_ip}:{args.port}')
        wookie_thread_b = threading.Thread(target=wookiee_broadcaster, args=(args.output, args.input, input_ip, int(args.port)))
        wookie_thread_b.setDaemon(True)
        wookie_thread_b.start()
    
elif args.range is not None:
    start_port, end_port = args.range.split(':')
    
    if int(end_port) <= int(start_port):
        print('Incorrect use of the port range parameter. Please run -h to see needed parameters.')
        exit(2)
    
    numeral_port_range = range(int(start_port), int(end_port) + 1)
    
    wookie_threads = [None for i in range(len(numeral_port_range))]
    wookie_threads_b = wookie_threads
    thread_counter = 0
    
    for range_port in range(int(start_port), int(end_port) + 1):
        print(f'Starting wookiee_broadcaster - listening on {args.input}/255.255.255.255:{range_port}, broadcasting on {args.output}/{output_ip}:{range_port}')
        wookie_threads[thread_counter] = threading.Thread(target=wookiee_broadcaster, args=(args.input, args.output, output_ip, int(range_port)))
        wookie_threads[thread_counter].setDaemon(True)
        wookie_threads[thread_counter].start()
        
        if args.bidirectional:
            print('*** Running in bidirectional mode ***')
            print(f'Starting wookiee_broadcaster - listening on {args.output}/255.255.255.255:{args.port}, broadcasting on {args.input}/{input_ip}:{range_port}')
            wookie_threads_b[thread_counter] = threading.Thread(target=wookiee_broadcaster, args=(args.output, args.input, output_ip, int(range_port)))
            wookie_threads_b[thread_counter].setDaemon(True)
            wookie_threads_b[thread_counter].start()
            
        thread_counter += 1
else:
    print('Missing port or port range parameters. Please run -h to see needed parameters.')
    exit(3)

while True:
    sleep(86400)
