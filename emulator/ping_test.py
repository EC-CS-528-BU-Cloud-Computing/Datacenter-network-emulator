# Specify k 
import sys
import os

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 ping_test.py k")
        
    k = int(sys.argv[1])
    hosts_per_pod = int((k * k) / 4)
    hosts_per_edge = int(hosts_per_pod / (k / 2))
    host_ips = []
    host_names = []
    for pod in range(k):
        for p in range(hosts_per_pod):
            host_names.append("pod-{}-host-{}".format(pod, p))
        for edge in range(int(k/2)):
            for host in range(hosts_per_edge):
                host_ips.append("15.{}.{}.{}".format(pod, edge, host + 3))
                
    for (container, src_ip) in zip(host_names, host_ips):
        os.system("docker exec -it {} ping -c 1 -I eth1 {}".format(container, src_ip))
        