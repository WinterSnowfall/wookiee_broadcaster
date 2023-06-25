# The Wookiee Broadcaster

A broadcast packet replication script for **Linux**, written in **Python 3**, which enables UDP broadcast LAN applications to communicate across two separate network interfaces/zones. This is particularly useful for playing LAN games via VPN, especially when several of the players reside behind NAT and only one of them has a VPN bridge that allows remote players to join.

### But why code YABU (yet another broadcasting utility)?

While there already are some good working examples out there (see the links provided below), almost all I could find use either low-level layer 2 magic or third party libraries to intercept and replicate the broadcast packets. I was also unable to find a utility which takes all of its required parameters from the command line and is flexible enough to meet a number of situations in which LAN-to-VPN games can find themselves in.

I had to ask myself: "Isn't there a simpler way to achieve this by using something more high-level, like sockets?". The answer, and the reason why you are reading these lines, is yes.

Here are other similar tools that I was able to find on GitHub:
* https://github.com/gqgunhed/py-udp-broadcast-forward
* https://github.com/nomeata/udp-broadcast-relay/

### I still don't get what this does. And what's with the weird name?

I'm glad you asked :). We'll take an example using one famous and other more obscure Star Wars universe characters (ergo, the name, which is a pun on the signature Wookiee weapon: https://starwars.fandom.com/wiki/Bowcaster). 

Let's say Chewbacca wants to play a LAN game with his good friend Shoran, which is high up in orbit around Kashyyyk, on some boring patrol mission. They both have an IPv4 VPN on their, ehm... holo-computers (which is a fallback for the more common IPv32 that the Galactic Senate mandated in use over 100 years ago).

However, Attichitcuk (Chewie's dad) wants to join in on the fun. And more than that, since he's the rather rich old chieftain of the tribe, he has the most advanced holo-computer in the group, so it makes sense for him to host the games. Sadly, he has no direct connection to Shoran, but Chewie could use his computer to link the two, at least in theory.

Let's put this in perspective. Here's a layout of what we're looking at:

```
Shoran's PC                         Chewie's PC
 ----------                         ------------
|          |                       |            |
| 5.0.0.2  |-----------------------|  5.0.0.1   | VPN
|          |                       |            |
 ----------                         ------------
    VPN                                  :
                                         :-- (routing logic)
                                         :                                Attichitcuk's PC
                                    ------------                           ------------
                                   |            |                         |            |
                           NAT LAN |  10.0.0.1  |-------------------------|  10.0.0.2  | NAT LAN 
                                   |            |                         |            |
                                    ------------                           ------------
```

Now Chewie knows his networking and since he's running Wookiee Linux, he's already forwarded all the ports required by the game between Shoran and his dad. His own routing is not a problem since his dad is visible and accessible, being on the same local network.

But Chewie still has a problem: layer 3 VPNs don't usually forward broadcast requests between network zones, even if he enables forwarding in his routing rules. More explicitly, UDP packets sent by Attichitcuk's PC on 255.255.255.255 across the 10.x.x.x zone won't cross over to 5.0.0.2. Damn, that's something Chewie can't solve by tinkering with his firewall rules.

What about Shoran's broadcast requests? Will they reach Attichitcuk? Usually, no, and this is a problem as well, but a far simpler one. Since Attichitcuk can use Chewie's PC as a gateway, he is technically able to route packets directly (back) to Shoran (no address translation is required). In order to get Shoran's broadcast packets to Attichitcuk, Chewie can employ some firewall trickery, as described here: https://odi.ch/weblog/posting.php?posting=731

Now he could do the same for Attichitcuk's broadcast packets in order to get them to Shoran, but there's one major issue that's stopping him: Shoran's PC can't resolve Attichitcuk's IP address since the latter is behind NAT. It won't know who sent the broadcast, so it won't know who to reply to.

What we need is some form of routing logic for broadcast packets to bridge the LAN behind NAT and the VPN interface on Chewie's PC. His PC will get the broadcast packets from Attichitcuk and replicate them on the VPN interface, by using his own VPN address as source (5.0.0.1). Remember that he's already set up forwarding rules, so anything coming to his PC on the VPN interface will now be automatically forwarded to Attichitcuk, and everything will work.

Let the Wookiee games begin!

So, by now it's either very clear what the Wookiee Broadcaster does, or I've confused you completely.

### Neat. I'll pretend I'm not confused. How does it work?

It's written for Linux, so you'll need a **Linux OS** with **python 3.6+** installed on the machine you plan to run it on. Since I've only used the standard sockets library, no external/additional packets are required.

You can run **./wookiee_broadcaster.py -h** to get some hints, but in short, you'll need to specify:

* -p <ports> = the port or ports on which the script will listen for packets - use port ranges to specify multiple ports, separated by ":", e.g.: 10000:10010
* -i <input> = the name of the network interface (as listed by ifconfig) on which the script will listen for incoming broadcast packets
* -o <output> = the name of the network interface (as listed by ifconfig) on which the script will replicate any broadcast packets received on the input interface

There are also a few optional command line arguments:

* -b = bidirectional mode - will forward broadcast packets from the output interface back to the input interface as well, though, as explained earlier, this is not usually that useful unless the network zones have bilateral routing capabilities or are somehow bridged (defaults to **False** if unspecified)
* -q = quiet mode - suppresses all logging messages (defaults to **False** if unspecified)

**Note**: All port values must be specified in the bindable, non-protected range of **1024:65535**.

To give you an example, you can run:

```
./wookiee_broadcaster.py -i eth0 -o ham0 -p 5000 2>&1 > /dev/null &
```

in order to start a background process which will replicate any broadcast packets received on port 5000, on the eth0 interface over to the ham0 interface, using the same output port (5000).

### Will this work on Windows?

Sadly, no. Because Windows and UDP broadcast sockets have a tense relationship at best, and the Wookiee Broadcaster needs to be able to listen to broadcast packets on a particular interface. This is unsupported on Windows, believe it or not, because Windows UDP sockets, depending on what Windows version you're using, will either listen for broadcast packets on ALL the network interfaces or only on the highest priority network interface (which is hardcoded, based on your system settings). Now you know why, among other things, Linux systems have established themselves as the backbone of the internet.

You can still use Windows machines as your peers/gaming systems, but the routing logic, along with the Wookiee Broadcaster, need to happen exclusively on a Linux host. This host can potentially be a Linux VM running on one of your Windows systems, using a bridged network adapter with its own LAN MAC/IP address and with a VPN service deployed on it (or a bridged adapter to a local VPN network).

### How come you're only listening to broadcasts on 255.255.255.255? There are plenty of other potential broadcast addresses, including local ones, like 10.0.0.255!

Fair enough, but most games will send out broadcasts on 255.255.255.255. I have yet to run across one which does this any differently, so... I haven't programmed that path yet. Feel free to tweak the code to your needs if you find its purpose insufficient.

