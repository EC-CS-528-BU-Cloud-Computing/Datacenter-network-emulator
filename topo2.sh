# SW0
docker run -id --name sw0 --privileged -d frrouting/frr 

ip addr add 10.0.1.2/24 dev lo
ip netns add srv0
ip netns exec srv0 ip link set dev lo up
ip netns exec srv0 ip addr add 10.0.1.1/24 dev lo

# veth
ip link add veth0 type veth peer name veth0p
ip link set veth0 up
ip link set veth0p netns srv0
ip netns exec srv0 ip link set veth0p up

ip netns exec srv0 ip route add default dev veth0p

# SW1
docker run -id --name sw1 --privileged -d frrouting/frr

ip addr add 10.0.2.2/24 dev lo
ip netns add srv1
ip netns exec srv1 ip link set dev lo up
ip netns exec srv1 ip addr add 10.0.2.1/24 dev lo

# veth
ip link add veth1 type veth peer name veth1p
ip link set veth1 up
ip link set veth1p netns srv1
ip netns exec srv1 ip link set veth1p up

ip netns exec srv1 ip route add default dev veth1p