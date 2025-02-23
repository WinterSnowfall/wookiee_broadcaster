#!/bin/bash

# NOTE: this script uses ufw to setup relaying rules.
# Please ensure it is available to use on the system where
# you plan to run this script.

# VPN network with netmask
VPN_NETWORK="25.0.0.0/8"
# default gateway IP
DEFAULT_GATEWAY_IP="10.0.0.1"
# VPN gateway IP
VPN_GATEWAY_IP="10.0.0.8"
# dhcp switch for local connection
LOCAL_DHCP=false
# local network manager connection name
LOCAL_NM_CONNECTION_NAME="Wired connection 1"
# local network interface name
LOCAL_INTF="eth0"
# local IP, based on the interface name
LOCAL_IP=$(ip -4 addr show $LOCAL_INTF 2>/dev/null | grep -w inet | awk '{print $2}' | cut -d '/' -f 1)

# can only ever happen if an invalid LOCAL_INTF is used
if [ -z $LOCAL_IP ]
then
    echo "Unable to detect local IP address. Check the LOCAL_INTF parameter and retry."
    exit 1
fi

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

        # add generic ufw rules to allow traffic
        sudo ufw allow from $VPN_GATEWAY_IP to any
        sudo ufw allow from $VPN_NETWORK to any

        echo "Setup complete."
        ;;
    stop)
        sudo echo "Reverting local network connection settings..."

        # remove generic ufw rules to allow traffic
        sudo ufw delete allow from $VPN_GATEWAY_IP to any
        sudo ufw delete allow from $VPN_NETWORK to any

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
        exit 2
        ;;
esac

