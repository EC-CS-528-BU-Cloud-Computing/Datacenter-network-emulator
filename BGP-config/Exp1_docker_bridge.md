1. Create two subnets
```
sudo docker network create --driver bridge --subnet 10.0.0.0/24 sw2srv0
sudo docker network create --driver bridge --subnet 10.0.1.0/24 sw2srv1
```

2. Create srv0 and srv1 
```
sudo docker run -dit --name srv0 --hostname srv0 --privileged --net sw2srv0 ubuntu
sudo docker run -dit --name srv1 --hostname srv1 --privileged --net sw2srv1 ubuntu
```

3. Create ToR
```
docker run -dit --name tor --hostname tor --privileged --net sw2srv0 frrouting/frr
docker network connect sw2srv1 tor
```



We change the default gateway because original default gateway is docker brigde which we cannot configure. Current IP addrs are different from the figure.

In three terminals:
```
sudo docker exec -it --privileged tor bash
# ifconfig
eth0      Link encap:Ethernet  HWaddr 02:42:0A:00:00:03  
          inet addr:10.0.0.3  Bcast:10.0.0.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:12 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:908 (908.0 B)  TX bytes:0 (0.0 B)

eth1      Link encap:Ethernet  HWaddr 02:42:0A:00:01:03  
          inet addr:10.0.1.3  Bcast:10.0.1.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:12 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0 
          RX bytes:908 (908.0 B)  TX bytes:0 (0.0 B)

lo        Link encap:Local Loopback  
          inet addr:127.0.0.1  Mask:255.0.0.0
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:0 errors:0 dropped:0 overruns:0 frame:0
          TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000 
          RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
```
```
sudo docker exec -it --privileged srv0 bash
root@srv0:/# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.0.1        0.0.0.0         UG    0      0        0 eth0
10.0.0.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0

root@srv0:/# route add default gw 10.0.0.3
root@srv0:/# route del default gw 10.0.0.1
root@srv0:/# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.0.3        0.0.0.0         UG    0      0        0 eth0
10.0.0.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0
```
```
sudo docker exec -it --privileged srv1 bash
root@srv1:/# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.1.1        0.0.0.0         UG    0      0        0 eth0
10.0.1.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0

root@srv1:/# route add default gw 10.0.1.3
root@srv1:/# route del default gw 10.0.1.1
root@srv1:/# route -n
Kernel IP routing table
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
0.0.0.0         10.0.1.3        0.0.0.0         UG    0      0        0 eth0
10.0.1.0        0.0.0.0         255.255.255.0   U     0      0        0 eth0
```


4. Configure OSPF in ToR
Add /etc/frr/vtysh.conf
```
!
! Sample configuration file for vtysh.
!
!service integrated-vtysh-config
!hostname quagga-router
!username root nopassword
!
service integrated-vtysh-config
```

Enable OSPF
```
bash-5.1# sed -i '/ospfd=no/c\ospfd=yes' /etc/frr/daemons 

# docker restart vs
# docker exec -it vs bash
bash-5.1# ps
PID   USER     TIME  COMMAND
    1 root      0:00 /sbin/tini -- /usr/lib/frr/docker-start
    7 root      0:00 {docker-start} /bin/ash /usr/lib/frr/docker-start
   15 root      0:00 /usr/lib/frr/watchfrr zebra ospfd staticd
   32 frr       0:00 /usr/lib/frr/zebra -d -F traditional -A 127.0.0.1 -s 90000000
   37 frr       0:00 /usr/lib/frr/ospfd -d -F traditional -A 127.0.0.1
   40 frr       0:00 /usr/lib/frr/staticd -d -F traditional -A 127.0.0.1
   42 root      0:00 bash
   48 root      0:00 ps

```



7. Configure OSPF routing n ToR
```
bash-5.1# vtysh

Hello, this is FRRouting (version 8.1_git).
Copyright 1996-2005 Kunihiro Ishiguro, et al.

83b31a638dcf# configure terminal
83b31a638dcf(config)# router ospf
83b31a638dcf(config-router)# network 10.0.0.0/24 area 0.0.0.0
83b31a638dcf(config-router)# network 10.0.1.0/24 area 0.0.0.0
83b31a638dcf(config-router)# do write memory
```

8. Ping from srv0 to srv1
```
root@srv0:/# ping 10.0.1.2
PING 10.0.1.2 (10.0.1.2): 56 data bytes
64 bytes from 10.0.1.2: icmp_seq=0 ttl=63 time=0.141 ms
64 bytes from 10.0.1.2: icmp_seq=1 ttl=63 time=0.083 ms
```