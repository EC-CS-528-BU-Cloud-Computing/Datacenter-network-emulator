Exp3


1. Step up topology

```
docker run -id --name sw0 frrouting/frr bash
docker run -id --name sw1 frrouting/frr bash
```

```
sudo ./create_vnet.sh -n 1 sw0 
sudo ./create_vnet.sh -n 1 sw1 
ip netns list
sw1-srv0 (id: 3)
sw0-srv0 (id: 2)
docker run --privileged --network container:sw0 --name vs0 -d frrouting/frr
docker run --privileged --network container:sw1 --name vs1 -d frrouting/frr
```


```
sudo ip netns exec sw0-srv0 ifconfig eth0 10.0.1.1/24
sudo ip netns exec sw0-srv0 ip route add default via 10.0.1.2
sudo ip netns exec sw1-srv0 ifconfig eth0 10.0.2.1/24
sudo ip netns exec sw1-srv0 ip route add default via 10.0.2.2
```

Test:
```
sudo ip netns exec sw0-srv0 ping 10.0.1.2
sudo ip netns exec sw1-srv0 ping 10.0.2.2

```

create veth pairs in two switch containers:
```
# docker inspect -f '{{.State.Pid}}' vs1
35888
# docker inspect -f '{{.State.Pid}}' vs0
36017
# ln -sfT /proc/35888/ns/net /var/run/netns/35888
# ln -sfT /proc/36017/ns/net /var/run/netns/36017
ip link add v-eth-vs1 type veth peer name v-eth-vs2
ip link set v-eth-vs1 netns 35888
ip link set v-eth-vs2 netns 36017
ip -n 36017 addr add 172.16.0.1/24 dev v-eth-vs2
ip -n 35888 addr add 172.16.0.2/24 dev v-eth-vs1
ip -n 36017 link set v-eth-vs2 up
ip -n 35888 link set v-eth-vs1 up
```


2. configure BGP
```
# sed -i '/bgpd=no/c\bgpd=yes' /etc/frr/daemons 
# exit
sudo docker vs1 restart 
sudo docker exec -it vs1 bash 
```

/etc/frr/bgpd.conf:
```
!
! Zebra configuration saved from vty
!   2022/10/16 02:57:14
!
frr version 8.1_git
frr defaults traditional
!
hostname 5fa4220fb2f2
!
!
!
router bgp 65001
 bgp router-id 10.0.2.2
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 timers bgp 3 9
 neighbor 172.16.0.1 remote-as 65000
 neighbor 172.16.0.1 advertisement-interval 0
 neighbor 172.16.0.1 timers connect 5
 !
 address-family ipv4 unicast
  neighbor 172.16.0.1 activate
  network 10.0.2.0 mask 255.255.255.0
 exit-address-family
!
log file bgpd.log
!
exit
!
!
!
!
!
```


```
# sed -i '/bgpd=no/c\bgpd=yes' /etc/frr/daemons 
# exit
sudo docker vs0 restart 
sudo docker exec -it vs0 bash 
# vtysh
```

/etc/frr/bgpd.conf:
```
!
! Zebra configuration saved from vty
!   2022/10/16 02:55:25
!
frr version 8.1_git
frr defaults traditional
!
hostname bf07395187a3
!
!
!
router bgp 65000
 bgp router-id 10.0.1.2
 bgp log-neighbor-changes
 no bgp ebgp-requires-policy
 timers bgp 3 9
 neighbor 172.16.0.2 remote-as 65001
 neighbor 172.16.0.2 advertisement-interval 0
 neighbor 172.16.0.2 timers connect 5
 !
 address-family ipv4 unicast
  neighbor 172.16.0.2 activate
  network 10.0.1.0 mask 255.255.255.0
 exit-address-family
!
exit
!
!
!
!
!
```


In vs0:
```
# vtysh
bf07395187a3# show ip route bgp
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

B>* 10.0.2.0/24 [20/0] via 172.16.0.2, v-eth-vs2, weight 1, 00:02:43

```
In vs1:
```
5fa4220fb2f2# show ip route bgp
Codes: K - kernel route, C - connected, S - static, R - RIP,
       O - OSPF, I - IS-IS, B - BGP, E - EIGRP, N - NHRP,
       T - Table, v - VNC, V - VNC-Direct, A - Babel, F - PBR,
       f - OpenFabric,
       > - selected route, * - FIB route, q - queued, r - rejected, b - backup
       t - trapped, o - offload failure

B>* 10.0.1.0/24 [20/0] via 172.16.0.1, v-eth-vs1, weight 1, 00:03:22
```

Test:
```
sudo ip netns exec sw0-srv0 ping 10.0.2.1
PING 10.0.2.1 (10.0.2.1) 56(84) bytes of data.
64 bytes from 10.0.2.1: icmp_seq=1 ttl=62 time=0.087 ms
64 bytes from 10.0.2.1: icmp_seq=2 ttl=62 time=0.045 ms
```

```
sudo ip netns exec sw1-srv0 ping 10.0.1.1
PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
64 bytes from 10.0.1.1: icmp_seq=1 ttl=62 time=0.079 ms
64 bytes from 10.0.1.1: icmp_seq=2 ttl=62 time=0.044 ms
```