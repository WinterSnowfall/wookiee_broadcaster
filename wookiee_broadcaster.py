#!/usr/bin/env python3
'''
@author: Winter Snowfall
@version: 2.32
@date: 18/10/2024
'''

import socket
import logging
import multiprocessing
import argparse
import platform
import subprocess
import signal
import ipaddress

# logging configuration block
LOGGER_FORMAT = '%(asctime)s %(levelname)s >>> %(message)s'
# logging level for other modules
logging.basicConfig(format=LOGGER_FORMAT, level=logging.ERROR)
logger = logging.getLogger(__name__)
# logging level for current logger
logger.setLevel(logging.INFO) # DEBUG, INFO, WARNING, ERROR, CRITICAL

# constants
BROADCAST_ADDRESS = '255.255.255.255'
# valid (and bindable) port range boundaries
PORTS_RANGE = (1024, 65535)
# broadcast UDP packets are not typically all that large
RECV_BUFFER_SIZE = 2048 #bytes
# maximum number of packets that can be stacked for receive/send operations
PACKET_QUEUE_SIZE = 64 #packets

def sigterm_handler(signum, frame):
    # exceptions may happen here as well due to logger syncronization mayhem on shutdown
    try:
        logger.debug('WU >>> Stopping Wookiee Broadcaster process due to SIGTERM...')
    except:
        pass

    raise SystemExit(0)

def sigint_handler(signum, frame):
    # exceptions may happen here as well due to logger syncronization mayhem on shutdown
    try:
        logger.debug('WU >>> Stopping Wookiee Broadcaster process due to SIGINT...')
    except:
        pass

    raise SystemExit(0)

def wookiee_receiver(process_no, input_intf, input_ip,
                     output_network, port, exit_event, queue):
    # catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    # catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    logger.info(f'WB P{process_no} --- Starting receiver worker process...')

    try:
        receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            receiver.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, input_intf)
        except AttributeError:
            logger.critical(f'WB P{process_no} --- SO_BINDTODEVICE is not available.')
            exit_event.set()
        except OSError:
            logger.critical(f'WB P{process_no} --- Interface not found or unavailable.')
            exit_event.set()
        try:
            receiver.bind((BROADCAST_ADDRESS, port))
        except OSError:
            logger.critical(f'WB P{process_no} --- Interface unavailable or port {port} is in use.')
            exit_event.set()

        while not exit_event.is_set():
            data, addr = receiver.recvfrom(RECV_BUFFER_SIZE)
            logger.debug(f'WB P{process_no} --- Received a packet from {addr[0]}:{addr[1]}...')
            #logger.debug(f'WB P{process_no} >>> {addr[0]}:{addr[1]} sent: {data}')

            if addr[0] != input_ip and ipaddress.IPv4Address(addr[0]) not in output_network:
                if queue.full():
                    logger.error(f'WB P{process_no} --- Packet queue has hit its capacity limit!')
                queue.put(data)
            else:
                # if such packets are intercepted, traffic to the desired endpoint may be lost
                logger.warning(f'WB P{process_no} --- Ignoring a packet not intended for replication...')

    except SystemExit:
        pass

    finally:
        try:
            logger.debug(f'WB P{process_no} --- Closing receiver socket...')
            receiver.close()
            logger.debug(f'WB P{process_no} --- Receiver socket closed.')
        except:
            pass

    logger.info(f'WB P{process_no} --- Stopped receiver worker process.')

def wookiee_broadcaster(process_no, output_intf, output_ip,
                        port, exit_event, queue):
    # catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    # catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    logger.info(f'WB P{process_no} +++ Starting broadcaster worker process...')

    try:
        broadcaster = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        try:
            broadcaster.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, output_intf)
        except AttributeError:
            logger.critical(f'WB P{process_no} +++ SO_BINDTODEVICE is not available.')
            exit_event.set()
        except OSError:
            logger.critical(f'WB P{process_no} +++ Interface not found or unavailable.')
            exit_event.set()
        try:
            broadcaster.bind((output_ip, port))
        except OSError:
            logger.critical(f'WB P{process_no} +++ Interface unavailable or port {port} is in use.')
            exit_event.set()

        while not exit_event.is_set():
            data = queue.get()

            logger.info(f'WB P{process_no} +++ Replicated a packet on {output_ip}:{port}, broadcasting to {BROADCAST_ADDRESS}')
            broadcaster.sendto(data, (BROADCAST_ADDRESS, port))

    except SystemExit:
        pass

    finally:
        try:
            logger.debug(f'WB P{process_no} +++ Closing broadcaster socket...')
            broadcaster.close()
            logger.debug(f'WB P{process_no} +++ Broadcaster socket closed.')
        except:
            pass

    logger.info(f'WB P{process_no} +++ Stopped broadcaster worker process.')

if __name__ == "__main__":
    # catch SIGTERM and exit gracefully
    signal.signal(signal.SIGTERM, sigterm_handler)
    # catch SIGINT and exit gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    parser = argparse.ArgumentParser(description=('*** The Wookiee Broadcaster *** Replicates broadcast packets across network interfaces. '
                                                  'Useful for TCP/IP and UDP/IP based multiplayer LAN games enjoyed using VPN.'), add_help=False)

    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    required.add_argument('-p', '--ports', help=('Port(s) on which the broadcaster will listen for packets and also the replication port(s).'
                                              'Can also be specified as a port range, in the format of <start_port>:<end_port>.'),
                          required=True)
    required.add_argument('-i', '--input-intf', help='Input interface name for listening to broadcast packets.', required=True)
    required.add_argument('-o', '--output-intf', help='Output interface name, on which the broadcast requests will be replicated.', required=True)

    # reposition the standard -h flag at the bottom, in a custom optional section
    optional.add_argument('-h', '--help', action='help', help='show this help message and exit')
    optional.add_argument('-q', '--quiet', help='Disable all logging output.', action='store_true')

    args = parser.parse_args()

    if platform.system() == 'Windows':
        logger.critical('WB >>> The Wookiee Broadcaster is intended for Linux use only!')
        raise SystemExit(1)

    # disable all logging in quiet mode
    if args.quiet:
        logging.disable(logging.CRITICAL)

    # handle ranges by default, and single ports as a special case
    try:
        ports = [int(port) for port in args.ports.split(':')]
    except:
        logger.critical('WB >>> Invalid port value(s) specified. Please retry with valid port value(s).')
        raise SystemExit(2)

    if len(ports) > 1:
        try:
            start_port, end_port = ports[:]
        except:
            logger.critical('WB >>> Laugh it up, fuzzball...')
            raise SystemExit(3)

        if end_port <= start_port:
            logger.critical('WB >>> Incorrect use of the port range parameter. Please run -h to see needed parameters.')
            raise SystemExit(4)

        if start_port < PORTS_RANGE[0] or end_port > PORTS_RANGE[1]:
            logger.critical(f'WB >>> Please use valid ports, in the {PORTS_RANGE[0]}:{PORTS_RANGE[1]} range.')
            raise SystemExit(5)

        port_range = range(start_port, end_port + 1)
        port_range_len = len(port_range)

    # if only a single port is specified, store that in the range
    else:
        if ports[0] < PORTS_RANGE[0] or ports[0] > PORTS_RANGE[1]:
            logger.critical(f'WB >>> Please use a valid port, in the {PORTS_RANGE[0]}:{PORTS_RANGE[1]} range.')
            raise SystemExit(6)

        port_range = ports
        port_range_len = 1

    input_intf = bytes(args.input_intf, 'utf-8')
    logger.debug(f'WB >>> input_intf: {args.input_intf}')
    output_intf = bytes(args.output_intf, 'utf-8')
    logger.debug(f'WB >>> output_intf: {args.output_intf}')

    if input_intf == output_intf:
        logger.critical('WB >>> It\'s not wise to upset a wookiee...')
        raise SystemExit(7)

    try:
        input_ip_query_subprocess = subprocess.run(['ip', '-4', 'addr', 'show', args.input_intf],
                                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                                   check=True)
        input_ip_query_output = input_ip_query_subprocess.stdout.decode('utf-8')
        input_ip, input_netmask = input_ip_query_output[input_ip_query_output.find('inet ') + 5:
                                                        input_ip_query_output.find(' brd')].split('/')

        logger.debug(f'WB >>> input_ip: {input_ip}')
        logger.debug(f'WB >>> input_netmask: {input_netmask}')
        input_network = ipaddress.IPv4Interface(f'{input_ip}/{input_netmask}').network
        logger.debug(f'WB >>> input_network: {input_network}')

        if input_ip == '':
            logger.critical(f'Unable to obtain an IP address for {args.input_intf}. Please retry with a valid interface name.')
            raise SystemExit(8)
    except:
        logger.critical(f'Invalid input interface {args.input_intf}. Please retry with a valid interface name.')
        raise SystemExit(8)

    try:
        output_ip_query_subprocess = subprocess.run(['ip', '-4', 'addr', 'show', args.output_intf],
                                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                                   check=True)
        output_ip_query_output = output_ip_query_subprocess.stdout.decode('utf-8')
        output_ip, output_netmask = output_ip_query_output[output_ip_query_output.find('inet ') + 5:
                                                           output_ip_query_output.find(' brd')].split('/')

        logger.debug(f'WB >>> output_ip: {output_ip}')
        logger.debug(f'WB >>> output_netmask: {output_netmask}')
        output_network = ipaddress.IPv4Interface(f'{output_ip}/{output_netmask}').network
        logger.debug(f'WB >>> output_network: {output_network}')

        if output_ip == '':
            logger.critical(f'WB >>> Unable to obtain an IP address for {args.output_intf}. Please retry with a valid interface name.')
            raise SystemExit(9)
    except:
        logger.critical(f'WB >>> Invalid output interface {args.output_intf}. Please retry with a valid interface name.')
        raise SystemExit(9)

    wookiee_receiver_procs_list = [None] * port_range_len
    wookiee_broadcaster_procs_list = [None] * port_range_len

    broadcast_queue_list = [multiprocessing.Queue(PACKET_QUEUE_SIZE) for i in range(port_range_len)]
    exit_event = multiprocessing.Event()
    exit_event.clear()

    proc_counter = 0

    for port in port_range:
        logger.info(f'WB P{proc_counter + 1} >>> Starting Wookiee Broadcaster - listening on {args.input_intf}/{BROADCAST_ADDRESS}:{port}, '
                    f'broadcasting on {args.output_intf}/{output_ip}:{port}')
        wookiee_receiver_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_receiver,
                                                                            args=(proc_counter + 1, input_intf, input_ip,
                                                                                  output_network, port, exit_event,
                                                                                  broadcast_queue_list[proc_counter]),
                                                                            daemon=True)
        wookiee_receiver_procs_list[proc_counter].start()

        wookiee_broadcaster_procs_list[proc_counter] = multiprocessing.Process(target=wookiee_broadcaster,
                                                                               args=(proc_counter + 1, output_intf, output_ip,
                                                                                     port, exit_event, broadcast_queue_list[proc_counter]),
                                                                               daemon=True)
        wookiee_broadcaster_procs_list[proc_counter].start()

        proc_counter += 1

    try:
        # wait for the exit event or until an interrupt is received
        exit_event.wait()

    except SystemExit:
        # exceptions may happen here as well due to logger syncronization mayhem on shutdown
        try:
            exit_event.set()
            logger.info('WB >>> Stopping Wookiee Broadcaster...')
        except:
            exit_event.set()

    finally:
        logger.info('WB >>> Waiting for the receiver and broadcaster processes to complete...')

        for wookiee_proc in wookiee_receiver_procs_list:
            wookiee_proc.join()

        for wookiee_proc in wookiee_broadcaster_procs_list:
            wookiee_proc.join()

        logger.info('WB >>> The receiver and broadcaster processes have been stopped.')

    logger.info('WB >>> Ruow! (Goodbye)')
