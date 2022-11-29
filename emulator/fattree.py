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
                    os.system("sudo ip link add ca-core-{}-pod-{}-agg-{} type veth peer name ca-pod-{}-agg-{}-core-{}".format(core_id, pod, agg, pod, agg, core_id))
                    os.system("sudo ip link set ca-core-{}-pod-{}-agg-{} netns {}".format(core_id, pod, agg, int(pid_core)))
                    os.system('sudo ip link set ca-pod-{}-agg-{}-core-{} netns {}'.format(pod, agg, core_id, int(pid_agg)))

                    os.system('sudo nsenter -t {} -n ip link set dev ca-core-{}-pod-{}-agg-{} up'.format(int(pid_core), core_id, pod, agg))
                    os.system('sudo nsenter -t {} -n ip link set dev ca-pod-{}-agg-{}-core-{} up'.format(int(pid_agg), pod, agg, core_id))  
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ca-core-{}-pod-{}-agg-{}'.format(int(pid_core), 169, self.k, agg, core_id, core_id, pod, agg))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ca-pod-{}-agg-{}-core-{}'.format(int(pid_agg), 169, self.k, agg + self.k/2, core_id, pod, agg, core_id))

                core_id += 1

        # Add links between aggregation switches and edge switches in each pod
        for pod in range(0, self.k):
            for agg in range(0, self.k / 2):
                pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                for edge in range(0, self.k / 2):
                    pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                    os.system("sudo ip link add ae-pod-{}-agg-{}-edge-{} type veth peer name ae-pod-{}-edge-{}-agg-{}".format(pod, agg, edge, pod, edge, agg))
                    os.system('sudo ip link set ae-pod-{}-agg-{}-edge-{} netns {}'.format(pod, agg, edge, int(pid_agg)))
                    os.system("sudo ip link set ae-pod-{}-edge-{}-agg-{} netns {}".format(pod, edge, agg, int(pid_edge)))

                    os.system('sudo nsenter -t {} -n ip link set dev ae-pod-{}-agg-{}-edge-{} up'.format(int(pid_agg), pod, agg, edge))
                    os.system('sudo nsenter -t {} -n ip link set dev ae-pod-{}-edge-{}-agg-{} up'.format(int(pid_edge), pod, edge, agg))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ae-pod-{}-agg-{}-edge-{}'.format(int(pid_agg), 169, pod, agg + self.k/2, edge, pod, agg, edge))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev ae-pod-{}-edge-{}-agg-{}'.format(int(pid_edge), 169, pod, edge, agg+self.k/2, pod, edge, agg))



        # Add links between edge switches and hosts in each pod
        for pod in range(0, self.k):
            host_id = 0
            for edge in range(0, self.k / 2):
                pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                for host in range(2, self.k/2+2):
                    pid_host = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(pod, host_id)]).decode("utf-8").strip()
                    os.system("sudo ip link add eh-pod-{}-edge-{}-host-{} type veth peer name eh-pod-{}-host-{}-edge-{}".format(pod, edge, host_id, pod, host_id, edge))
                    os.system('sudo ip link set eh-pod-{}-edge-{}-host-{} netns {}'.format(pod, edge, host_id, int(pid_edge)))
                    os.system('sudo ip link set eh-pod-{}-host-{}-edge-{} netns {}'.format(pod, host_id, edge, int(pid_host)))

                    os.system('sudo nsenter -t {} -n ip link set dev eh-pod-{}-edge-{}-host-{} up'.format(int(pid_edge), pod, edge, host_id))
                    os.system('sudo nsenter -t {} -n ip link set dev eh-pod-{}-host-{}-edge-{} up'.format(int(pid_host), pod, host_id, edge))
                    os.system('sudo nsenter -t {} -n ip addr add {}.{}.{}.{}/8 dev eh-pod-{}-edge-{}-host-{}'.format(int(pid_edge), 169, pod, edge, host - 2, pod, edge, host_id))
            
                    host_id += 1
                    