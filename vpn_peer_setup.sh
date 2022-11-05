#!/bin/bash

#LAN network with netmask
LAN_NETWORK="10.0.0.0/24"
#default gateway IP
DEFAULT_GATEWAY_IP="10.0.0.1"
#VPN gateway IP
VPN_GATEWAY_IP="10.0.0.8"
#dhcp switch for local connection
LOCAL_DHCP=false
#local network manager connection name
LOCAL_NM_CONNECTION_NAME="Wired connection 1"
#local network interface name
LOCAL_INTF="eth0"
#local IP, based on the interface name
LOCAL_IP=$(ifconfig $LOCAL_INTF | grep -w inet | awk '{print $2;}')

case $1 in
    start)
        sudo echo "Setting up local network connection for VPN relay..."    
        sudo nmcli connection down "$LOCAL_NM_CONNECTION_NAME"
        if $LOCAL_DHCP
        then
            sudo nmcli connection modify "$LOCAL_NM_CONNECTION_NAME" ipv4.method manual ipv4.addr $LOCAL_IP/24 ipv4.gateway $VPN_GATEWAY_IP ipv4.dns $VPN_GATEWAY_IP
        else
            sudo nmcli connection modify "$LOCAL_NM_CONNECTION_NAME" ipv4.gateway $VPN_GATEWAY_IP
        fi
        sudo nmcli connection up "$LOCAL_NM_CONNECTION_NAME"
        echo "Setup complete."  
        ;;
    stop)
        sudo echo "Reverting local network connection settings..."  
        sudo nmcli connection down "$LOCAL_NM_CONNECTION_NAME"
        if $LOCAL_DHCP
        then
            sudo nmcli connection modify "$LOCAL_NM_CONNECTION_NAME" ipv4.method auto ipv4.addr "" ipv4.gateway "" ipv4.dns ""    
        else
            sudo nmcli connection modify "$LOCAL_NM_CONNECTION_NAME" ipv4.gateway $DEFAULT_GATEWAY_IP
        fi
        sudo nmcli connection up "$LOCAL_NM_CONNECTION_NAME"
        echo "Normal settings restored."
        ;;
    *)
        echo "Invalid option!"
        exit 1
esac

