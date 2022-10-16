Exp3


1. Step up topology

```
docker run -id --name sw0 frrouting/frr bash
docker run -id --name sw1 frrouting/frr bash
```

```
sudo docker network create --driver bridge --subnet 172.16.0.0/24 net
```

Note: Use default docker bridge to connect vs0 and vs1, as ge2 and ge3 interfaces

```
sudo ./create_vnet.sh -n 1 sw0 
sudo ./create_vnet.sh -n 1 sw1 
# docker network connect net vs0
# docker network connect net vs1
ip netns list
sw1-srv0 (id: 3)
sw0-srv0 (id: 2)

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
# vtysh

5fa4220fb2f2# configure t
5fa4220fb2f2(config)# router bgp 65001
5fa4220fb2f2(config-router)# bgp router-id 10.0.2.2 
5fa4220fb2f2(config-router)# bgp log-neighbor-changes
5fa4220fb2f2(config-router)# timers bgp 3 9
5fa4220fb2f2(config-router)# neighbor ISL peer-group
5fa4220fb2f2(config-router)# neighbor ISL remote-as 65000
5fa4220fb2f2(config-router)# neighbor ISL advertisement-interval 0
5fa4220fb2f2(config-router)# neighbor ISL timers connect 5
5fa4220fb2f2(config-router)# neighbor 172.16.0.1 peer-group ISL
5fa4220fb2f2(config-router)# address-family ipv4 unicast
5fa4220fb2f2(config-router-af)# neighbor ISL activate
5fa4220fb2f2(config-router-af)# network 10.0.2.0/24
5fa4220fb2f2(config-router-af)# network 10.0.1.0/24
network 172.16.0.0/24
5fa4220fb2f2(config-router-af)# maximum-paths 64
5fa4220fb2f2(config-router-af)# exit-address-family
# do write memory
```


```
# sed -i '/bgpd=no/c\bgpd=yes' /etc/frr/daemons 
# exit
sudo docker vs0 restart 
sudo docker exec -it vs0 bash 
# vtysh

5fa4220fb2f2# configure t
5fa4220fb2f2(config)# router bgp 65000
5fa4220fb2f2(config-router)# bgp router-id 10.0.1.2 
5fa4220fb2f2(config-router)# bgp log-neighbor-changes
5fa4220fb2f2(config-router)# timers bgp 3 9
5fa4220fb2f2(config-router)# neighbor ISL peer-group
5fa4220fb2f2(config-router)# neighbor ISL remote-as 65001
5fa4220fb2f2(config-router)# neighbor ISL advertisement-interval 0
5fa4220fb2f2(config-router)# neighbor ISL timers connect 5
5fa4220fb2f2(config-router)# neighbor 172.16.0.2 peer-group ISL
5fa4220fb2f2(config-router)# address-family ipv4 unicast
5fa4220fb2f2(config-router-af)# neighbor ISL activate
5fa4220fb2f2(config-router-af)# network 10.0.2.0/24
5fa4220fb2f2(config-router-af)# network 10.0.1.0/24
network 172.16.0.0/24
5fa4220fb2f2(config-router-af)# maximum-paths 64
5fa4220fb2f2(config-router-af)# exit-address-family
# do write memory
```
```
# vtysh
# show bgp summary
```

Test:
```
sudo ip netns exec sw0-srv0 ping 10.0.2.1
PING 10.0.2.1 (10.0.2.1) 56(84) bytes of data.
64 bytes from 10.0.2.1: icmp_seq=1 ttl=62 time=0.133 ms
64 bytes from 10.0.2.1: icmp_seq=2 ttl=62 time=0.059 ms
64 bytes from 10.0.2.1: icmp_seq=3 ttl=62 time=0.060 ms
```

```
sudo ip netns exec sw1-srv0 ping 10.0.1.1
PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
64 bytes from 10.0.1.1: icmp_seq=1 ttl=62 time=0.096 ms
64 bytes from 10.0.1.1: icmp_seq=2 ttl=62 time=0.059 ms
64 bytes from 10.0.1.1: icmp_seq=3 ttl=62 time=0.059 ms
```