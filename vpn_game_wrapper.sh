#!/bin/bash

#IP of the LAN player
LAN_PLAYER_IP="10.0.0.2"
#IP of the VPN player
VPN_PLAYER_IP="25.0.0.2"
#LAN network with netmask
LAN_NETWORK="10.0.0.0/24"
#VPN network with netmask
VPN_NETWORK="25.0.0.0/8"
#local LAN broadcast address
LAN_BROADCAST_IP="10.0.0.255"
#local LAN interface name
LAN_INTF="eth0"
#local VPN interface name
VPN_INTF="ham0"

echo "*** WinterSnowfall's VPN game wrapper for Mint/Ubuntu ***"
echo ""
echo ">>> Your LAN player IP is set to : $LAN_PLAYER_IP"
echo ">>> Your VPN player IP is set to : $VPN_PLAYER_IP"
echo ""
echo "######################################"
echo "#                                    #"
echo "#   (1)  Torchlight 2 (default)      #"
echo "#   (2)  Worms Armageddon            #"
echo "#   (3)  Divinity Original Sin EE    #"
echo "#   (4)  Majesty 2                   #"
echo "#                                    #"
echo "######################################"
echo ""
echo -n ">>> Choose your destiny: "
read game
echo ">>> Outstanding!"

#local VPN IP
VPN_LOCAL_IP=`ifconfig $VPN_INTF | grep -w inet | awk '{print $2;}'`
#echo ">>> Local VPN IP address is: "$VPN_LOCAL_IP

#ensure ipv4 forarding between adapters is enabled
sudo sysctl -w net.ipv4.ip_forward=1

#add generic ufw rules to allow traffic
sudo ufw allow from $LAN_NETWORK to any
sudo ufw allow from $VPN_NETWORK to any
sudo ufw default reject incoming

#switch default forwarding policy to ACCEPT
sudo iptables -P FORWARD ACCEPT

#add game-specific broadcasting/NAT rules
case $game in
    2)
        echo ">>> Setting up Worms Armageddon..."
        #broadcast NAT
        sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 17012 -j TEE --gateway $LAN_BROADCAST_IP
        sudo ./wookiee_broadcaster -i $LAN_INTF -o $VPN_INTF -p 17012 >/dev/null 2>&1 &
        #regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 17012 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p tcp -s $VPN_PLAYER_IP --dport 17011 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p tcp -s $VPN_PLAYER_IP --dport 50000:55000 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 17012 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p tcp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 17011 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p tcp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 50000:55000 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    3)
        echo ">>> Setting up Divinty Original Sin EE..."
        #broadcast NAT
        sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 23243:23262 -j TEE --gateway $LAN_BROADCAST_IP
        sudo ./wookiee_broadcaster -i $LAN_INTF -o $VPN_INTF -r 23243:23262 >/dev/null 2>&1 &
        #regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 23243:23262 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 23243:23262 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    4)
        echo ">>> Setting up Majesty 2..."
        #broadcast NAT
        sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 3210 -j TEE --gateway $LAN_BROADCAST_IP
        sudo ./wookiee_broadcaster -i $LAN_INTF -o $VPN_INTF -p 3210 >/dev/null 2>&1 &
        #regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 3210 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 3210 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
    *)
        echo ">>> Setting up Torchlight 2..."
        #broadcast NAT
        sudo iptables -t mangle -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP -d 255.255.255.255 --dport 4549 -j TEE --gateway $LAN_BROADCAST_IP
        sudo ./wookiee_broadcaster -i $LAN_INTF -o $VPN_INTF -p 4549 >/dev/null 2>&1 &
        #regular NAT
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 4549 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A PREROUTING -i $VPN_INTF -p udp -s $VPN_PLAYER_IP --dport 30000:65000 -j DNAT --to-destination $LAN_PLAYER_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 4549 -j SNAT --to-source $VPN_LOCAL_IP
        sudo iptables -t nat -A POSTROUTING -o $VPN_INTF -p udp -s $LAN_PLAYER_IP -d $VPN_PLAYER_IP --dport 30000:65000 -j SNAT --to-source $VPN_LOCAL_IP
        ;;
esac

#wait to revert on input
echo ">>> VPN gaming setup complete!"
echo -n ">>> Press any key to terminate..."
read terminate

#terminate all broadcast replication processes
for process in `ps -ef | grep ./wookiee_broadcaster | grep -v grep | awk '{print $2;}'`
do
    sudo kill $process
done

#remove game-specific broadcasting/NAT rules
#
#careful with flushing the nat tables, some services
#(e.g. docker) will also add some rules here -
#it is better to individually remove above rules in this case
#
sudo iptables -t nat -F
sudo iptables -t mangle -F

#switch default forwarding policy to DROP
sudo iptables -P FORWARD DROP

#remove generic rules
sudo ufw default deny incoming
sudo ufw delete allow from $VPN_NETWORK to any
sudo ufw delete allow from $LAN_NETWORK to any

#disable ipv4 forwarding (if needed)
sudo sysctl -w net.ipv4.ip_forward=0

