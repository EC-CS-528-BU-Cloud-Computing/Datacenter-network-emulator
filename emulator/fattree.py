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
        assert (k >= 2 and k <= 18 and k % 2 == 0)
        self.k = k
        self.client =  docker.from_env()
        self.num_of_core_sw = int((self.k * self.k) / 4)
        self.num_of_sw_per_pod = int(self.k)
        self.num_of_host_per_pod = int((self.k * self.k) / 4)
        self.num_of_half_pod_sw = int(self.k / 2)

    def createContainers(self):
        print("Create containers...")
        # Create host base image


        # Start containers
        # Core
        for i in range(self.num_of_core_sw):
            self.client.containers.run("frrouting/frr:latest" ,detach=True, init=True, name="core-{}".format(i), privileged=True)
       
        for i in range(self.k):
            # Pod Switch
            for j in range(int(self.num_of_sw_per_pod / 2)):
                # Aggregation
                self.client.containers.run("frrouting/frr:latest" ,detach=True, init=True, name="pod-{}-agg-{}".format(i, j), privileged=True)
                # Edge
                self.client.containers.run("frrouting/frr:latest" ,detach=True, init=True, name="pod-{}-edge-{}".format(i, j), privileged=True)
            # Host
            for j in range(self.num_of_host_per_pod):
                self.client.containers.run("ubuntu_net:Dockerfile", detach=True, init=True, tty=True, name="pod-{}-host-{}".format(i, j), privileged=True)
               
        
    # WARNING: It will destroy all containers.
    def distroyContainers(self):
        MAX_K = 4

        print("Clean old bridges and containers...")

        # bridges
        for pod in range(0, MAX_K):
            host_id = 0
            for edge in range(0, self.num_of_half_pod_sw):
                os.system("docker network disconnect br-p-{}-e-{} pod-{}-edge-{}".format(pod, edge, pod, edge))
                for host in range(3, self.num_of_half_pod_sw + 3):
                    os.system("docker network disconnect br-p-{}-e-{} pod-{}-host-{}".format(pod, edge, pod, host_id))
                    host_id += 1
                os.system("docker network rm br-p-{}-e-{}".format(pod, edge))


        for i in range(self.num_of_core_sw):
            try: 
                core_sw = self.client.containers.get("core-{}".format(i))
                core_sw.stop()
                core_sw.remove()
            except: 
                print("didn't find core-{}".format(i))
        
        for i in range(MAX_K):
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
                os.system("docker exec core-{} ip addr add 15.{}.{}.{} dev lo".format(core_id, self.k, j, i))
                print("core-{}".format(core_id), "lo addr:", "15.{}.{}.{}".format(self.k, j, i))
                core_id += 1
        
        for i in range(self.k):
            
            # Pod Switch
            # Aggregation
            for j in range(0, int(self.k / 2)):
                os.system("docker exec pod-{}-agg-{} ip addr add 15.{}.{}.1 dev lo".format(i, j, i, j + int(self.k / 2)))
                print("pod-{}-agg-{}".format(i, j), "lo addr:", "15.{}.{}.1".format(i, j + int(self.k / 2)))
            
        print("finish assigning loopback interface ip addresses.")


    def addLinks(self):
        
        # This function add veth pairs between containers and assign IP addresses to veth interfaces
        # Interface address subnet 169.0.0.0/8
        # Routers and hosts loopback interface address subnet 15.0.0.0/8 -- based on fattree paper

        # Add links between core switches and aggregation switches
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            agg = x - 1
            for y in range(1, self.num_of_half_pod_sw + 1):
                pid_core = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'core-{}'.format(core_id)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_core, pid_core))
                print("core-{}".format(core_id), "pid =", pid_core)
                for pod in range(0, self.k):
                    pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                    print("pod-{}-agg-{}".format(pod, agg), "pid =", pid_agg)
                    
                    os.system("sudo ip link add ca-c-{}-p-{}-a-{} type veth peer name ca-p-{}-a-{}-c-{}".format(core_id, pod, agg, pod, agg, core_id))
                    os.system("sudo ip link set ca-c-{}-p-{}-a-{} netns {}".format(core_id, pod, agg, int(pid_core)))
                    os.system('sudo ip link set ca-p-{}-a-{}-c-{} netns {}'.format(pod, agg, core_id, int(pid_agg)))

                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/24 dev ca-c-{}-p-{}-a-{}'.format(int(pid_core), 169, self.k + core_id, pod, 1, core_id, pod, agg))
                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/24 dev ca-p-{}-a-{}-c-{}'.format(int(pid_agg), 169, self.k + core_id, pod, 2, pod, agg, core_id))

                    os.system('sudo ip -n {} link set dev ca-c-{}-p-{}-a-{} up'.format(int(pid_core), core_id, pod, agg))
                    os.system('sudo ip -n {} link set dev ca-p-{}-a-{}-c-{} up'.format(int(pid_agg), pod, agg, core_id))  

                core_id += 1
        print("finish setting up links between core switches and aggregation switches.")

        # Add links between aggregation switches and edge switches in each pod
        for pod in range(0, self.k):
            port_id = 1
            for agg in range(0, self.num_of_half_pod_sw):
                pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                for edge in range(0, self.num_of_half_pod_sw):
                    pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))
                    os.system("sudo ip link add ae-p-{}-a-{}-e-{} type veth peer name ae-p-{}-e-{}-a-{}".format(pod, agg, edge, pod, edge, agg))
                    os.system('sudo ip link set ae-p-{}-a-{}-e-{} netns {}'.format(pod, agg, edge, int(pid_agg)))
                    os.system("sudo ip link set ae-p-{}-e-{}-a-{} netns {}".format(pod, edge, agg, int(pid_edge)))

                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/24 dev ae-p-{}-a-{}-e-{}'.format(int(pid_agg), 169, pod, port_id, 1, pod, agg, edge))
                    os.system('sudo ip -n {} addr add {}.{}.{}.{}/24 dev ae-p-{}-e-{}-a-{}'.format(int(pid_edge), 169, pod, port_id, 2, pod, edge, agg))

                    os.system('sudo ip -n {} link set dev ae-p-{}-a-{}-e-{} up'.format(int(pid_agg), pod, agg, edge))
                    os.system('sudo ip -n {} link set dev ae-p-{}-e-{}-a-{} up'.format(int(pid_edge), pod, edge, agg))
                    port_id += 1
                    
                 

        print("finish setting up links between aggregation switches and edge switches.")

        # Add links between edge switches and hosts in each pod
        for pod in range(0, self.k):
            host_id = 0
            for edge in range(0, self.num_of_half_pod_sw):
                pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))

                os.system("docker network create --driver bridge --subnet 15.{}.{}.{}/24 br-p-{}-e-{}".format(pod, edge, 0, pod, edge))
                os.system("docker network connect --ip 15.{}.{}.2 br-p-{}-e-{} pod-{}-edge-{}".format(pod, edge, pod, edge, pod, edge))

                for host in range(3, self.num_of_half_pod_sw + 3):
                    pid_host = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(pod, host_id)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_host, pid_host))
                    
                    os.system("docker network connect --ip 15.{}.{}.{} br-p-{}-e-{} pod-{}-host-{}".format(pod, edge, host, pod, edge, pod, host_id))
                    # change default gw to edge sw
                    os.system("docker exec pod-{}-host-{} route add default gw 15.{}.{}.2".format(pod, host_id, pod, edge))
                    os.system("docker exec pod-{}-host-{} route del default gw 15.{}.{}.1".format(pod, host_id, pod, edge))
                    
                    host_id += 1

        print("finish setting up links between edge switches and hosts.")

    def addLinksUnnumbered(self):
        # This function add veth pairs between containers and assign IP addresses to veth interfaces
        # Interface address subnet 169.0.0.0/8
        # Routers and hosts loopback interface address subnet 15.0.0.0/8 -- based on fattree paper

        # Add links between core switches and aggregation switches
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            agg = x - 1
            for y in range(1, self.num_of_half_pod_sw + 1):
                pid_core = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'core-{}'.format(core_id)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_core, pid_core))
                print("core-{}".format(core_id), "pid =", pid_core)
                for pod in range(0, self.k):
                    pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                    print("pod-{}-agg-{}".format(pod, agg), "pid =", pid_agg)
                    
                    os.system("sudo ip link add ca-c-{}-p-{}-a-{} type veth peer name ca-p-{}-a-{}-c-{}".format(core_id, pod, agg, pod, agg, core_id))
                    os.system("sudo ip link set ca-c-{}-p-{}-a-{} netns {}".format(core_id, pod, agg, int(pid_core)))
                    os.system('sudo ip link set ca-p-{}-a-{}-c-{} netns {}'.format(pod, agg, core_id, int(pid_agg)))

                    os.system('sudo ip -n {} link set dev ca-c-{}-p-{}-a-{} up'.format(int(pid_core), core_id, pod, agg))
                    os.system('sudo ip -n {} link set dev ca-p-{}-a-{}-c-{} up'.format(int(pid_agg), pod, agg, core_id))  

                core_id += 1
        print("finish setting up links between core switches and aggregation switches.")

        # Add links between aggregation switches and edge switches in each pod
        for pod in range(0, self.k):
            port_id = 1
            for agg in range(0, self.num_of_half_pod_sw):
                pid_agg = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(pod, agg)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_agg, pid_agg))
                for edge in range(0, self.num_of_half_pod_sw):
                    pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))
                    os.system("sudo ip link add ae-p-{}-a-{}-e-{} type veth peer name ae-p-{}-e-{}-a-{}".format(pod, agg, edge, pod, edge, agg))
                    os.system('sudo ip link set ae-p-{}-a-{}-e-{} netns {}'.format(pod, agg, edge, int(pid_agg)))
                    os.system("sudo ip link set ae-p-{}-e-{}-a-{} netns {}".format(pod, edge, agg, int(pid_edge)))

                    os.system('sudo ip -n {} link set dev ae-p-{}-a-{}-e-{} up'.format(int(pid_agg), pod, agg, edge))
                    os.system('sudo ip -n {} link set dev ae-p-{}-e-{}-a-{} up'.format(int(pid_edge), pod, edge, agg))
                    port_id += 1
                    
                 

        print("finish setting up links between aggregation switches and edge switches.")

        # Add links between edge switches and hosts in each pod
        for pod in range(0, self.k):
            host_id = 0
            for edge in range(0, self.num_of_half_pod_sw):
                pid_edge = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(pod, edge)]).decode("utf-8").strip()
                os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_edge, pid_edge))

                os.system("docker network create --driver bridge --subnet 15.{}.{}.{}/24 br-p-{}-e-{}".format(pod, edge, 0, pod, edge))
                os.system("docker network connect --ip 15.{}.{}.2 br-p-{}-e-{} pod-{}-edge-{}".format(pod, edge, pod, edge, pod, edge))

                for host in range(3, self.num_of_half_pod_sw + 3):
                    pid_host = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(pod, host_id)]).decode("utf-8").strip()
                    os.system("sudo ln -sfT /proc/{}/ns/net /var/run/netns/{}".format(pid_host, pid_host))
                    
                    os.system("docker network connect --ip 15.{}.{}.{} br-p-{}-e-{} pod-{}-host-{}".format(pod, edge, host, pod, edge, pod, host_id))
                    # change default gw to edge sw
                    os.system("docker exec pod-{}-host-{} route add default gw 15.{}.{}.2".format(pod, host_id, pod, edge))
                    os.system("docker exec pod-{}-host-{} route del default gw 15.{}.{}.1".format(pod, host_id, pod, edge))
                    
                    host_id += 1

        print("finish setting up links between edge switches and hosts.")

    def breakCoreAggLink(self):
        core_id = 0
        pod = 0
        agg = 0
        print("Break a link between core-{} sw and pod-{}-agg-{} sw".format(core_id, pod, agg))
        os.system("docker exec core-{} ifconfig ca-c-{}-p-{}-a-{} down".format(core_id, core_id, pod, agg))
    
    def breakAggEdgeLink(self):
        pod = 0
        agg = 0
        edge = 0
        print("Break a link between pod-{}-agg-{} sw and pod-{}-edge-{} sw".format(pod, agg, pod, edge))
        os.system("docker exec pod-{}-agg-{} ifconfig ae-p-{}-a-{}-e{} down".format(pod, agg, pod, agg, edge))
    
    def recoverCoreAggLink(self):
        core_id = 0
        pod = 0
        agg = 0
        print("Recover a link between core-{} sw and pod-{}-agg-{} sw".format(core_id, pod, agg))
        os.system("docker exec core-{} ifconfig ca-c-{}-p-{}-a-{} up".format(core_id, core_id, pod, agg))
    
    def recoverAggEdgeLink(self):
        pod = 0
        agg = 0
        edge = 0
        print("Recover a link between pod-{}-agg-{} sw and pod-{}-edge-{} sw".format(pod, agg, pod, edge))
        os.system("docker exec pod-{}-agg-{} ifconfig ae-p-{}-a-{}-e{} up".format(pod, agg, pod, agg, edge))
