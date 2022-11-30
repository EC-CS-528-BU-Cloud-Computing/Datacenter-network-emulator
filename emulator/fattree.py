from mimetypes import init
import subprocess as sp
import docker
import os
'''
A Python class launches containers for FatTree.

Naming:

Core switch: core-{switch_id}
Pod Aggreagation Switch: pod-{pod_id}-agg-{switch_id}
Pod Edge Switch: pod-{pod_id}-edge-{switch_id}
Pod Host: pod-{id}-host-{host_id}

Switch runs sonic-frr images.
Host runs ubuntu image.

'''
class FatTree:
    def __init__(self, k) -> None:
        assert (k >= 2 and k % 2 == 0)
        self.k = k
        self.client =  docker.from_env()
        self.num_of_core_sw = int((self.k * self.k) / 4)
        self.num_of_sw_per_pod = int(self.k)
        self.num_of_host_per_pod = int((self.k * self.k) / 4)
        self.num_of_half_pod_sw = int(self.k / 2)

    def createContainers(self):
        # Start containers
        # Core
        for i in range(self.num_of_core_sw):
            self.client.containers.run("frrouting/frr" ,detach=True, init=True, name="core-{}".format(i), privileged=True)
       
        for i in range(self.k):
            # Pod Switch
            for j in range(int(self.num_of_sw_per_pod / 2)):
                # Aggregation
                self.client.containers.run("frrouting/frr" ,detach=True, init=True, name="pod-{}-agg-{}".format(i, j), privileged=True)
                # Edge
                self.client.containers.run("frrouting/frr" ,detach=True, init=True, name="pod-{}-edge-{}".format(i, j), privileged=True)
            # Host
            for j in range(self.num_of_host_per_pod):
                self.client.containers.run("ubuntu", detach=True, init=True, tty=True, name="pod-{}-host-{}".format(i, j), privileged=True)
                # os.system("docker exec -it pod-{}-host-{} echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections".format(i, host_id))
                os.system("docker exec -it pod-{}-host-{} apt update".format(i, j))
                os.system("docker exec -it pod-{}-host-{} apt install dialog apt-utils -y".format(i, j))
                os.system("docker exec -it pod-{}-host-{} apt install -y -q net-tools".format(i, j))
                os.system("docker exec -it pod-{}-host-{} apt install -y -q inetutils-ping".format(i, j))
        
    # WARNING: It will destroy all containers.
    def distroyContainers(self):
        for i in range(self.num_of_core_sw):
            try: 
                core_sw = self.client.containers.get("core-{}".format(i))
                core_sw.stop()
                core_sw.remove()
            except: 
                print("didn't find core-{}".format(i))
        
        for i in range(self.k):
            # Pod Switch
            for j in range(int(self.num_of_sw_per_pod / 2)):
                # Aggregation
                try: 
                    agg_sw = self.client.containers.get("pod-{}-agg-{}".format(i, j))
                    agg_sw.stop()
                    agg_sw.remove()
                except:
                    print("didn't find pod-{}-agg-{}".format(i, j))
                # Edge
                try:
                    edge_sw = self.client.containers.get("pod-{}-edge-{}".format(i, j))
                    edge_sw.stop()
                    edge_sw.remove()
                except:
                    print("didn't find pod-{}-edge-{}".format(i, j))
            # Host
            for j in range(self.num_of_host_per_pod):
                try: 
                    host = self.client.containers.get("pod-{}-host-{}".format(i, j))
                    host.stop()
                    host.remove()
                except:
                    print("didn't find pod-{}-host-{}".format(i, j))

    def assignLoIP(self):
        # Assign loopback IPs
        # Core
        core_id = 0
        for i in range(1, int(self.k / 2) + 1):
            for j in range(1, int(self.k / 2) + 1):
                os.system("docker exec core-{} ip addr add 10.{}.{}.{}/32 dev lo".format(core_id, self.k, j, i))
                print("core-{}".format(core_id), "lo addr:", "10.{}.{}.{}/32".format(self.k, j, i))
                core_id += 1
        
        for i in range(self.k):
            
            # Pod Switch
            # Aggregation
            for j in range(0, int(self.k / 2)):
                os.system("docker exec pod-{}-agg-{} ip addr add 10.{}.{}.1/24 dev lo".format(i, j, i, j + int(self.k / 2)))
                print("pod-{}-agg-{}".format(i, j), "lo addr:", "10.{}.{}.1/24".format(i, j + int(self.k / 2)))
            # Edge
            for j in range(0, int(self.k / 2)):
                os.system("docker exec pod-{}-edge-{} ip addr add 10.{}.{}.1/24 dev lo".format(i, j, i, j))
                print("pod-{}-edge-{}".format(i, j), "lo addr:", "10.{}.{}.1/24".format(i, j))
            
            # Host
            host_id = 0
            for j in range(int(self.k / 2)):
                for h in range(2, int(self.k / 2) + 2):
                    os.system("docker exec -it pod-{}-host-{} ip addr add 10.{}.{}.{}/24 dev lo".format(i, host_id, i, j, h))
                    print("pod-{}-host-{}".format(i, host_id), "lo addr:", "10.{}.{}.{}/24".format(i, j, h))
                    host_id += 1
        print("finish assigning loopback interface ip addresses.")


    def addLinks(self):
        
        # This function add veth pairs between containers and assign IP addresses to veth interfaces
        # Interface address subnet 169.0.0.0/8
        # Routers and hosts loopback interface address subnet 10.0.0.0/8 -- based on fattree paper

        # Add links between core switches and aggregation switches
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            agg = x - 1
            for y in range(1, self.num_of_half_pod_sw + 1):
                pid_core = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'core-{}'.format(core_id)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_core, pid_core))
                # print("core-{}".format(core_id), "pid =", pid_core)
                for pod in range(0, self.k):
                    pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                    # print("pod-{}-agg-{}".format(pod, agg), "pid =", pid_agg)
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                    
                    os.system("sudo ip link add ca-c-{}-p-{}-a-{} type veth peer name ca-p-{}-a-{}-c-{}".format(core_id, pod, agg, pod, agg, core_id))
                    os.system("sudo ip link set ca-c-{}-p-{}-a-{} netns {}".format(core_id, pod, agg, int(pid_core)))
                    os.system('sudo ip link set ca-p-{}-a-{}-c-{} netns {}'.format(pod, agg, core_id, int(pid_agg)))

                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ca-c-{}-p-{}-a-{}'.format(int(pid_core), 169, self.k + pod, agg, core_id, core_id, pod, agg))
                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ca-p-{}-a-{}-c-{}'.format(int(pid_agg), 169, self.k + pod, agg + self.num_of_half_pod_sw, core_id, pod, agg, core_id))

                    os.system('sudo ip -n {} link set dev ca-c-{}-p-{}-a-{} up'.format(int(pid_core), core_id, pod, agg))
                    os.system('sudo ip -n {} link set dev ca-p-{}-a-{}-c-{} up'.format(int(pid_agg), pod, agg, core_id))  
                   
                    print('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ca-c-{}-p-{}-a-{}'.format(int(pid_core), 169, self.k + pod, agg, core_id, core_id, pod, agg))
                    print('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ca-p-{}-a-{}-c-{}'.format(int(pid_agg), 169, self.k + pod, agg + self.num_of_half_pod_sw, core_id, pod, agg, core_id))

                core_id += 1
        print("finish setting up links between core switches and aggregation switches.")

        # Add links between aggregation switches and edge switches in each pod
        for pod in range(0, self.k):
            for agg in range(0, self.num_of_half_pod_sw):
                pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                for edge in range(0, self.num_of_half_pod_sw):
                    pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))
                    os.system("sudo ip link add ae-p-{}-a-{}-e-{} type veth peer name ae-p-{}-e-{}-a-{}".format(pod, agg, edge, pod, edge, agg))
                    os.system('sudo ip link set ae-p-{}-a-{}-e-{} netns {}'.format(pod, agg, edge, int(pid_agg)))
                    os.system("sudo ip link set ae-p-{}-e-{}-a-{} netns {}".format(pod, edge, agg, int(pid_edge)))

                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ae-p-{}-a-{}-e-{}'.format(int(pid_agg), 169, pod, agg + self.num_of_half_pod_sw, edge, pod, agg, edge))
                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ae-p-{}-e-{}-a-{}'.format(int(pid_edge), 169, pod, edge, agg+self.num_of_half_pod_sw, pod, edge, agg))

                    os.system('sudo ip -n {} link set dev ae-p-{}-a-{}-e-{} up'.format(int(pid_agg), pod, agg, edge))
                    os.system('sudo ip -n {} link set dev ae-p-{}-e-{}-a-{} up'.format(int(pid_edge), pod, edge, agg))
                    
                    print('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ae-p-{}-a-{}-e-{}'.format(int(pid_agg), 169, pod, agg + self.num_of_half_pod_sw, edge, pod, agg, edge))
                    print('sudo ip -n {} addr add {}.{}.{}.{}/8 dev ae-p-{}-e-{}-a-{}'.format(int(pid_edge), 169, pod, edge, agg+self.num_of_half_pod_sw, pod, edge, agg))

        print("finish setting up links between aggregation switches and edge switches.")

        # Add links between edge switches and hosts in each pod
        for pod in range(0, self.k):
            host_id = 0
            for edge in range(0, self.num_of_half_pod_sw):
                pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))
                for host in range(2, self.num_of_half_pod_sw + 2):
                    pid_host = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(pod, host_id)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_host, pid_host))
                    os.system("sudo ip link add eh-p-{}-e-{}-h-{} type veth peer name eh-p-{}-h-{}-e-{}".format(pod, edge, host_id, pod, host_id, edge))
                    os.system('sudo ip link set eh-p-{}-e-{}-h-{} netns {}'.format(pod, edge, host_id, int(pid_edge)))
                    os.system('sudo ip link set eh-p-{}-h-{}-e-{} netns {}'.format(pod, host_id, edge, int(pid_host)))

                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/8 dev eh-p-{}-e-{}-h-{}'.format(int(pid_edge), 169, pod, edge + self.k, host - 2, pod, edge, host_id))
                    os.system("sudo ip -n {} addr add {}.{}.{}.{}/8 dev eh-p-{}-h-{}-e-{}".format(int(pid_host), 169, pod, edge + self.k + self.num_of_half_pod_sw, host-2, pod, host_id, edge))

                    os.system('sudo ip -n {} link set dev eh-p-{}-e-{}-h-{} up'.format(int(pid_edge), pod, edge, host_id))
                    os.system('sudo ip -n {} link set dev eh-p-{}-h-{}-e-{} up'.format(int(pid_host), pod, host_id, edge))
                    
                    print('sudo ip -n {} addr add {}.{}.{}.{}/8 dev eh-p-{}-e-{}-h-{}'.format(int(pid_edge), 169, pod, edge + self.k, host - 2, pod, edge, host_id))
                    print("sudo ip -n {} addr add {}.{}.{}.{}/8 dev eh-p-{}-h-{}-e-{}".format(int(pid_host), 169, pod, edge + self.k + self.num_of_half_pod_sw, host-2, pod, host_id, edge))
                    host_id += 1

        print("finish setting up links between edge switches and hosts.")
                    