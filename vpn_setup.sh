#!/bin/bash

# NOTE: this script uses ufw and iptables to setup relaying rules.
# Please ensure both are available to use on the system where
# you plan to run this script.

######### SCRIPT PARAMETERS - MUST BE CONFIGURED PROPERLY ###########

# IP of the LAN player
LAN_PLAYER_IP="10.0.0.2"
# IP of the VPN player
VPN_PLAYER_IP="25.0.0.2"
# VPN player is hosting the game
VPN_PLAYER_IS_HOSTING=false
# LAN network with netmask
LAN_NETWORK="10.0.0.0/24"
# VPN network with netmask
VPN_NETWORK="25.0.0.0/8"
# local LAN broadcast address
LAN_BROADCAST_IP="10.0.0.255"
# local LAN interface name
LAN_INTF="eth0"
# local VPN interface name
VPN_INTF="ham0"
# path to the Wookiee Broadcaster script on the local host
LOCAL_WB_PATH="/home/username/wookiee_broadcaster.py"
# Wookiee Broadcaster script of binary name
LOCAL_WB_NAME=$(basename $LOCAL_WB_PATH)
# local VPN IP
VPN_LOCAL_IP=$(ip -4 addr show $VPN_INTF 2>/dev/null | grep -w inet | awk '{print $2}' | cut -d '/' -f 1)

# can only ever happen if an invalid VPN_INTF is used
if [ -z $VPN_LOCAL_IP ]
then
    echo "Unable to detect VPN IP address. Check the VPN_INTF parameter and retry."
    exit 1
fi

######################### IMPORTANT NOTE ############################
#                                                                   #
# The following also need to be true on the LAN_PLAYER_IP host for  #
# the forwarding to work properly:                                  #
#                                                                   #
# a) The local (LAN) IP of the host that is running the VPN         #
#    (and this script) must be configured as gateway on             #
#    LAN_PLAYER_IP's network interface                              #
# b) No ports should be blocked/firewalled between the two hosts,   #
#    especially not the ones used for direct/broadcast traffic      #
# c) 255.255.255.255 traffic must also be allowed on both hosts     #
#                                                                   #
#####################################################################

echo "*** WinterSnowfall's VPN relay setup script for Linux ***"
echo ""
echo ">>> LAN IP is set to : $LAN_PLAYER_IP"
echo ">>> VPN IP is set to : $VPN_PLAYER_IP"
echo ""
echo "####################################################"
echo "#                                                  #"
echo "#   (1)  Anno 1404: Venice                         #"
echo "#   (2)  Divinty Original Sin - Enhanced Edition   #"
echo "#   (3)  Majesty 2                                 #"
echo "#   (4)  Torchlight 2                              #"
echo "#   (5)  Worms Armageddon                          #"
echo "#                                                  #"
echo "####################################################"
echo ""
read -p ">>> Pick a game from the list: " game

# ensure ipv4 forwarding between adapters is enabled
sudo sysctl -w net.ipv4.ip_forward=1

# add generic ufw rules to allow traffic
sudo ufw allow from $LAN_NETWORK to any
sudo ufw allow from $VPN_NETWORK to any

# switch default forwarding policy to ACCEPT
sudo iptables -P FORWARD ACCEPT

# add game-specific broadcasting/NAT rules
case $game in
    1)
        echo ">>> Setting up Anno 1404: Venice..."
        # broadcast NAT
        if $VPN_PLAYER_IS_HOSTING
        then
            sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 9100 -j TEE --gateway $LAN_BROADCAST_IP
        else
            $LOCAL_WB_PATH -p 9100 -i $LAN_INTF -o $VPN_INTF >> wookiee_broadcaster.log 2>&1 &
        fi
        # regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 16000 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 9100:9103 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 16000 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 9100:9103 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    2)
        echo ">>> Setting up Divinty Original Sin - Enhanced Edition..."
        # broadcast NAT
        if $VPN_PLAYER_IS_HOSTING
        then
            sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 23243:23262 -j TEE --gateway $LAN_BROADCAST_IP
        else
            $LOCAL_WB_PATH -p 23243:23262 -i $LAN_INTF -o $VPN_INTF -q >> wookiee_broadcaster.log 2>&1 &
        fi
        # regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 23243:23262 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 23243:23262 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    3)
        echo ">>> Setting up Majesty 2..."
        # broadcast NAT
        if $VPN_PLAYER_IS_HOSTING
        then
            sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 3210 -j TEE --gateway $LAN_BROADCAST_IP
        else
            $LOCAL_WB_PATH -p 3210 -i $LAN_INTF -o $VPN_INTF >> wookiee_broadcaster.log 2>&1 &
        fi
        # regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 3210 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 3210 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    4)
        echo ">>> Setting up Torchlight 2..."
        # broadcast NAT
        if $VPN_PLAYER_IS_HOSTING
        then
            sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 4549 -j TEE --gateway $LAN_BROADCAST_IP
        else
            $LOCAL_WB_PATH -p 4549 -i $LAN_INTF -o $VPN_INTF >> wookiee_broadcaster.log 2>&1 &
        fi
        # regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 4549 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 30000:65000 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 4549 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 30000:65000 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    5)
        echo ">>> Setting up Worms Armageddon..."
        # broadcast NAT
        if $VPN_PLAYER_IS_HOSTING
        then
            sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 17012 -j TEE --gateway $LAN_BROADCAST_IP
        else
            $LOCAL_WB_PATH -p 17012 -i $LAN_INTF -o $VPN_INTF >> wookiee_broadcaster.log 2>&1 &
        fi
        # regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 17012 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p tcp -s $VPN_PLAYER_IP --dport 17011 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p tcp -s $VPN_PLAYER_IP --dport 50000:55000 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 17012 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p tcp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 17011 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p tcp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 50000:55000 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    *)
        echo ">>> Invalid option!"
        exit 2
        ;;
esac

echo ">>> VPN relay setup complete!"

read -p ">>> Press any key to terminate..."

# terminate all broadcast replication processes
pkill -f $LOCAL_WB_NAME > /dev/null 2>&1

# remove game-specific broadcasting/NAT rules
# 
# careful with flushing the nat tables, some services
# (e.g. docker) will also add some rules here -
# it is better to individually remove above rules in this case
# 
sudo iptables -t nat -F
sudo iptables -t mangle -F

# switch default forwarding policy to DROP
sudo iptables -P FORWARD DROP

# remove generic rules
sudo ufw delete allow from $VPN_NETWORK to any
sudo ufw delete allow from $LAN_NETWORK to any

# disable ipv4 forwarding (if needed)
sudo sysctl -w net.ipv4.ip_forward=0

echo ">>> VPN relay has been deconfigured."

