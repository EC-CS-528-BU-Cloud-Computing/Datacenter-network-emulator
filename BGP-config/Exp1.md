Exp 1


1. Create a docker with two front panel ports

```
$ docker run -id --name sw debian bash
$ sudo $sonic-buildimage/platform/vs/create_vnet.sh -n 2 sw
$ ip netns list
sw-srv1 (id: 2)
sw-srv0 (id: 1)
```

2. Start sonic virtual switch docker

```
$ docker run --privileged --network container:sw --name vs -d frrouting/frr
```

3. Setup IP in the virtual switch docker
(eth1 and eth2 already up in the frr container)

```
$ docker exec -it vs bash
bash-5.1# ip addr add 10.0.0.2/24 dev eth1
bash-5.1# ip addr add 10.0.1.2/24 dev eth2
```

4. Setup IP in the server network namespace

```
$ sudo ip netns exec sw-srv0 ifconfig eth0 10.0.0.1/24
$ sudo ip netns exec sw-srv0 ip route add default via 10.0.0.2
$ sudo ip netns exec sw-srv1 ifconfig eth0 10.0.1.1/24
$ sudo ip netns exec sw-srv1 ip route add default via 10.0.1.2
```


5. Ping from sw-srv0 to sw-srv1

```
sudo ip netns exec sw-srv0 ping 10.0.1.1
PING 10.0.1.1 (10.0.1.1) 56(84) bytes of data.
64 bytes from 10.0.1.1: icmp_seq=1 ttl=63 time=0.135 ms
64 bytes from 10.0.1.1: icmp_seq=2 ttl=63 time=0.036 ms
```

Ping from sw-srv1 to sw-srv0
```
sudo ip netns exec sw-srv1 ping 10.0.0.1
PING 10.0.0.1 (10.0.0.1) 56(84) bytes of data.
64 bytes from 10.0.0.1: icmp_seq=1 ttl=63 time=0.032 ms
64 bytes from 10.0.0.1: icmp_seq=2 ttl=63 time=0.033 ms
```

