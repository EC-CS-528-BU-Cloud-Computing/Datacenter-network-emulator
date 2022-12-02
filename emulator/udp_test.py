# Specify k 
import sys
import os
import subprocess as sp

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
    
    for (client_container, src_ip) in zip(host_names, host_ips):
        for (dest_container, dest_ip) in zip(host_names, host_ips):
            if dest_ip != src_ip:
                out = "WTF"
                try:
                    # Destination starts a UDP using netcat
                    print("Start UDP server at {}".format(dest_ip))
                    sp.check_output(['docker', 'exec', "-d", dest_container, "nc", '-l','-p', "999"]).decode("utf-8").strip()
                    # Source start UDP connection
                    # If the connection cannot be built it will throw Error
                    sp.check_output(['docker', 'exec', "-it", client_container,  "nc", "-z","-u", "-v", dest_ip, "999"])
                   
                    print("UDP Test success: Source : {} Destination: {}".format(src_ip, dest_ip))
                except sp.CalledProcessError as e:
                    print("UDP Test failed: Source : {} Destination: {}".format(src_ip, dest_ip))
                finally:
                    # In case the connection is not cleaned.
                    try:
                       pids = sp.check_output(['docker', 'exec', "-it", client_container,  "nc", "-z", "-v", dest_ip, "999"]).decode('utf-8').strip()
                       for pid in pids:
                           sp.check_output(['docker', 'exec', "kill", "-9", pid])
                    except sp.CalledProcessError as e:
                        print("Connection has been cleaned.")
