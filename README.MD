# The Wookiee Broadcaster

A broadcast package replication script for **Linux**, written in **Python 3**, which enables TCP/IP (or UDP/IP) LAN applications to communicate across two separate network interfaces/zones. This is particularly useful for playing LAN games via VPN, especially when several of the players reside behind NAT and only one of them has a VPN bridge that allows remote players to join.

# But why code YABU (yet another broadcasting utility)?

While there already are some good and working examples out there (see the links provided below), almost all I could find use either low-level layer 2 magic or some third party utilities to intercept and replicate the broadcast packets. I was also unable to find a utility which takes all of its required parameters from the command line and is flexible enough to meet a number of situations in which LAN-by-VPN games can get themselves into.

I had to ask myself: "Isn't there a simpler way to achieve this by using something more high-level, like sockets?". The answer, as you will soon find out, was yes.

Here are some other similar tools which I was able to find:
https://github.com/gqgunhed/py-udp-broadcast-forward
https://github.com/nomeata/udp-broadcast-relay/

# I still don't get what this does. And what's with the weird name?

I'm glad you asked :). We'll take an example using one famous and some more obscure Star Wars universe characters (ergo, the name, which is a pun on the signature Wookiee weapon).

Let's say Chewbacca wants to play a LAN game with his good friend Shoran, which is high up in orbit around Kashyyyk, on some boring patrol mission. They both have an IPv4 VPN on their, ehm... holo-computers (which is a fallback for the more common IPv32 that the Galactic Senate has voted into their legislature 100 years ago).

However, Attichitcuk (Chewie's dad) wants to join in as well in the fun. And more than that, since he's the father figure and old chieftain, he has the most advanced holo-computer in the group, so he wants to host the games. Sadly, he has no direct connection to Shoran, but Chewie could use his computer to link his dad to Shoran, at least in theory.

Let's put this a bit in perspective. Here's a layout of what we're looking at:


Shoran's PC                         Chewie's PC
 __________                         ____________
|          |                       |            |
| 5.0.0.2  |-----------------------|  5.0.0.1   | VPN
|__________|                       |____________|
                                         :
    VPN                                  :-- (routing logic)
                                         :                                Attichitcuk's PC
                                    _____:______                           ____________
                                   |            |                         |            |
                           NAT LAN |  10.0.0.1  |-------------------------|  10.0.0.2  | NAT LAN 
                                   |____________|                         |____________|



Now Chewie knows his networking and since he's running Wookiee Linux, he has already forwarded all the port required by the game between Shoran and his dad. His own routing is not a problem since his dad and himself are entirely visible and accessible to one another.

But Chewie still has a problem. Layer 3 VPNs don't usually forward broadcast requests between network zones, even if he enables forwarding in his routing rules. More explicitly, UDP packets sent by Attichitcuk's PC on 255.255.255.255 across the 10.x.x.x zone won't cross over to 5.0.0.2. Damn, that's something Chewie can't solve by tinkering with his firewall rules.

What about Shoran's broadcast requests? Will they reach Attichitcuk? Usually no, and this is a problem as well, but a far simpler one. Since Attichitcuk can use Chewie's PC as a gateway, he is technically able to route packets to Shoran (no address translation is required). In order to get Shoran's broadcast packets to Attichitcuk we can employ some trickery, as described here: https://odi.ch/weblog/posting.php?posting=731

Now we could do the same for Attichitcuk's broadcast packages in order to get them to Shoran, but we have one major issue that's stopping us: Shoran's PC can't resolve Attichitcuk's IP address since he is behind NAT, so it won't know who sent the broadcast.

What we need is some form or routing logic for broadcast packages to bridge the LAN NAT and VPN interfaces on Chewie's PC. His PC will get the broadcast packages from Attichitcuk and replicate them on the VPN interface, by using his own VPN address as source (5.0.0.1). Remember that he's already set up forwarding rules, so anything coming to his PC on the VPN interface will be forwarded to Attichitcuk.

So, by now it's either very clear what the Wookie Broadcaster does or I've confused you completely.

# Neat. I'll pretend I'm not confused. How does it work?

It's written for Linux, so you'll need a **Linux OS** with **python 3.6+** installed on the machine you plan to run it on. Since I've only used the standard sockets library, no external/additional packages are required.

You'll also need root rights to run it (sudo works just fine), because binding sockets to an interface is just not one of the things a regular user can do.

You can run **./wookiee_broadcaster.py -h** to get some hints, but in short, you'll need to specify:

-i <input> = the name of the network interface (as listed by ifconfig) on which the script will listen for incoming broadcast packets
-o <output> = the name of the network interface (as listed by ifconfig) on which the script will replicate any broadcast packages received on the input interface
-p <port> = the port on which the script will listen for packets
-r <range> = a range of ports on which the script will listen for packets, separated by ":", ex: 10000:10010
-b = bidirectional mode. Will forward broadcast packages from the output interface back to the input interface as well, though, as explained earlier, this is not usually that useful unless the network zones have bilateral routing capabilities or are somehow bridged.

To give you an example you can run:

```
sudo ./wookiee_broadcaster.py -i eth0 -o ham0 -p 5000 2>&1 > /dev/null &
```

To start a background process which will replicate any broadcast packets received on port 5000 through the eth0 interface onto the ham0 interface, using the same output port (5000).

# So how come you're only listening to broadcasts on 255.255.255.255? There are plenty of other potential broadcast addresses, including local ones like 10.0.0.255.

Fair enough, but most games will send out broadcasts on 255.255.255.255 and I have yet to run across one which does this any differently. Feel free to tweak the code to your needs if you find its purpose insufficient. 

# Can I reuse this code or "borrow" it?

Reuse it, change it, print it or write it on your living room walls if that brings you any sort of joy. Do whatever you want with it. If you need to put a name on this type of ultimate freedom type of license, I guess we can call it: http://www.wtfpl.net/.
