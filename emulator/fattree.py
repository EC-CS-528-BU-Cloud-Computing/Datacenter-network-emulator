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
        assert (k >= 4 and k % 2 == 0)
        self.k = k
        self.client =  docker.from_env()
        self.num_of_core_sw = int((self.k * self.k) / 4)
        self.num_of_sw_per_pod = int(self.k)
        self.num_of_host_per_pod = int((self.k * self.k) / 4)

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
        # Assign loopback IPs
        # Core
        core_id = 0
        for i in range(1, int(self.k / 2) + 1):
            for j in range(1, int(self.k / 2) + 1):
                os.system("docker exec core-{} ip addr add 10.{}.{}.{} dev lo".format(core_id, self.k, j, i))
                core_id += 1
        
        for i in range(self.k):
            
            # Pod Switch
            # Aggregation
            for j in range(0, int(self.k / 2)):
                os.system("docker exec pod-{}-agg-{} ip addr add 10.{}.{}.1 dev lo".format(i, j, i, j + int(self.k / 2)))
            # Edge
            for j in range(0, int(self.k / 2)):
                os.system("docker exec pod-{}-edge-{} ip addr add 10.{}.{}.1 dev lo".format(i, j, i, j))
            
            # Host
            
            host_id = 0
            for j in range(int(self.k / 2)):
                for h in range(2, int(self.k / 2) + 2):
                #  os.system("docker exec -it pod-{}-host-{} echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections".format(i, host_id))
                    os.system("docker exec -it pod-{}-host-{} apt update".format(i, host_id))
                    os.system("docker exec -it pod-{}-host-{} apt install dialog apt-utils -y".format(i, host_id))
                    os.system("docker exec -it pod-{}-host-{} apt install -y -q net-tools".format(i, host_id))
                    os.system("docker exec -it pod-{}-host-{} apt install -y -q iproute2".format(i, host_id))
                    os.system("docker exec -it pod-{}-host-{} ip addr add 10.{}.{}.{} dev lo".format(i, host_id, i, j, h))
                    host_id += 1

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

    def addLinks(self):
        
        # This function add veth pairs between containers and assign IP addresses to veth interfaces
        # Interface address subnet 169.0.0.0/8
        # Routers and hosts loopback interface address subnet 10.0.0.0/8 -- based on fattree paper

        # Add links between core switches and aggregation switches
        core_id = 0
        for x in range(1, self.k / 2 + 1):
            agg = x + self.k / 2 - 1
            for y in range(1, self.k / 2 + 1):
                pid_core = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'core-{}'.format(core_id)]).decode("utf-8").strip()
                for pod in range(0, self.k):
                    pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                    os.system("sudo ip link add ca-core-{} type veth peer name ca-pod-{}-agg-{}".format(core_id, pod, agg))
                    os.system("sudo ip link set ca-core-{} netns {}".format(core_id, int(pid_core)))
                    os.system('sudo ip link set ca-pod-{}-agg-{} netns {}'.format(pod, agg, int(pid_agg)))

                    os.system('sudo nsenter -t {} -n ip link set dev ca-core-{} up'.format(int(pid_core), core_id))
                    os.system('sudo nsenter -t {} -n ip link set dev ca-pod-{}-agg-{} up'.format(int(pid_agg), pod, agg))  
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ca-core-{}'.format(int(pid_core), 169, self.k, agg, core_id, core_id))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ca-pod-{}-agg-{}'.format(int(pid_agg), 169, self.k, agg + self.k/2, core_id, pod, agg))

                core_id += 1

        # Add links between aggregation switches and edge switches in each pod
        for pod in range(0, self.k):
            for agg in range(0, self.k / 2):
                pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                for edge in range(0, self.k / 2):
                    pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                    os.system("sudo ip link add ae-pod-{}-agg-{} type veth peer name ae-pod-{}-edge-{}".format(pod, agg, pod, edge))
                    os.system('sudo ip link set ae-pod-{}-agg-{} netns {}'.format(pod, agg, int(pid_agg)))
                    os.system("sudo ip link set ae-pod-{}-edge-{} netns {}".format(pod, edge, int(pid_edge)))

                    os.system('sudo nsenter -t {} -n ip link set dev ae-pod-{}-agg-{} up'.format(int(pid_agg), pod, agg))
                    os.system('sudo nsenter -t {} -n ip link set dev ae-pod-{}-edge-{} up'.format(int(pid_edge), pod, edge))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ae-pod-{}-agg-{}'.format(int(pid_agg), 169, pod, agg + self.k/2, edge, pod, agg))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ae-pod-{}-edge-{}'.format(int(pid_edge), 169, pod, edge, agg+self.k/2, pod, edge))



        # Add links between edge switches and hosts in each pod
        for pod in range(0, self.k):
            host_id = 0
            for edge in range(0, self.k / 2):
                pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                for host in range(2, self.k/2+2):
                    pid_host = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(pod, host_id)]).decode("utf-8").strip()
                    os.system("sudo ip link add eh-pod-{}-edge-{} type veth peer name eh-pod-{}-host-{}".format(pod, edge, pod, host_id))
                    os.system('sudo ip link set eh-pod-{}-edge-{} netns {}'.format(pod, edge, int(pid_edge)))
                    os.system('sudo ip link set eh-pod-{}-host-{} netns {}'.format(pod, host_id, int(pid_host)))

                    os.system('sudo nsenter -t {} -n ip link set dev eh-pod-{}-edge-{} up'.format(int(pid_edge), pod, edge))
                    os.system('sudo nsenter -t {} -n ip link set dev eh-pod-{}-host-{} up'.format(int(pid_host), pod, host_id))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev eh-pod-{}-edge-{}'.format(int(pid_edge), 169, pod, edge, host-2, pod, edge))
            
                    host_id += 1
                    