# Two servers on the same subnet are connected to a ToR switch.
# Service 0 
ip netns add srv0
ip netns exec srv0 ip link set dev lo up
ip netns exec srv0 ip addr add 10.0.0.1/24 dev lo
# Service 1 
ip netns add srv1
ip netns exec srv1 ip link set dev lo up
ip netns exec srv1 ip addr add 10.0.0.2/24 dev lo

# Create two veth
ip link add veth0 type veth peer name veth0p
ip link add veth1 type veth peer name veth1p
ip link set veth0 up
ip link set veth1 up


ip link set veth0p netns srv0
ip netns exec srv0 ip link set veth0p up
ip link set veth1p netns srv1
ip netns exec srv1 ip link set veth1p up

# Bridge
ip link add name sw type bridge
ip link set dev sw up

ip link set veth0 master sw
ip link set veth1 master sw
# Set IP for 
ip addr add 10.0.0.254 dev sw
bridge link

# Configure the routing
ip netns exec srv0 ip route add default dev veth0p
ip netns exec srv1 ip route add default dev veth1p


# Test
# ip netns exec srv0 ping 10.0.0.254
# ip netns 