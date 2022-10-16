Exp 2

Use docker bridge.
```
sudo docker network create --driver bridge --subnet 10.0.0.0/24 net1
sudo docker run -dit --name srv0 --hostname srv0 --privileged --net net1 ubuntu
sudo docker run -dit --name srv1 --hostname srv1 --privileged --net net1 ubuntu
```



```
root@srv0:/# ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.0.2  netmask 255.255.255.0  broadcast 10.0.0.255
        ether 02:42:0a:00:00:02  txqueuelen 0  (Ethernet)
        RX packets 2489  bytes 23778573 (23.7 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 1491  bytes 115682 (115.6 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 6  bytes 1130 (1.1 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 6  bytes 1130 (1.1 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0


root@srv1:/# ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.0.3  netmask 255.255.255.0  broadcast 10.0.0.255
        ether 02:42:0a:00:00:03  txqueuelen 0  (Ethernet)
        RX packets 2777  bytes 23797489 (23.7 MB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 2164  bytes 147200 (147.2 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 6  bytes 1130 (1.1 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 6  bytes 1130 (1.1 KB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```
In host:
```
br-fbb4fa237615: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.0.1  netmask 255.255.255.0  broadcast 10.0.0.255
        inet6 fe80::42:32ff:febc:fdc7  prefixlen 64  scopeid 0x20<link>
        ether 02:42:32:bc:fd:c7  txqueuelen 0  (Ethernet)
        RX packets 3656  bytes 211740 (211.7 KB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 5254  bytes 47575206 (47.5 MB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
```

Test:
```
root@srv1:/# ping 10.0.0.2
PING 10.0.0.2 (10.0.0.2): 56 data bytes
64 bytes from 10.0.0.2: icmp_seq=0 ttl=64 time=0.136 ms
64 bytes from 10.0.0.2: icmp_seq=1 ttl=64 time=0.066 ms
64 bytes from 10.0.0.2: icmp_seq=2 ttl=64 time=0.067 ms
64 bytes from 10.0.0.2: icmp_seq=3 ttl=64 time=0.071 ms
```