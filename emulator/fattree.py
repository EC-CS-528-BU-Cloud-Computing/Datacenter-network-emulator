from mimetypes import init
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
class ContainerManager:
    def __init__(self, k) -> None:
        assert (k >= 4 and k % 2 == 0)
        self.k =  k
        self.client =  docker.from_env()
        self.num_of_core_sw = int((self.k * self.k) / 4)
        self.num_of_sw_per_pod = int(self.k)
        self.num_of_host_per_pod = int((self.k * self.k) / 4)

    def start(self):
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
                    
    def connect(self):

        # Veth pairs from core switches to pod-agg switches
        # veth links have names of the type CA-C{core_switch_id}-P{pod_id}A{agg_swicth_id} e.g CA0C0-P0A0 and CA0P0A0-C0
        # Prefix CA in names for links between Core switches and Aggregation switches
        # Prefix AE in names for links between Aggregation switches and Edge switches
        # Prefix EH in names for links between Edge switches and Hosts

        for i in range(int(self.k/2)):
            for j in range(int(self.k/2)):
                for m in range(self.k):
                    x = i*(int(self.k/2))
                    os.system("sudo ip link add CA-C{}-P{}A{} type veth peer name CA-P{}A{}-C{}".format(j+x,m,i, m,i, j+x))
                    # set CA-C{}-P{}A{} up in core-{}
                    # set CA-P{}A{}-C{} up in pod-{}-agg-{}
                    pid1 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'core-{}'.format(j+x)]).decode("utf-8").strip()
                    pid2 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(m,i)]).decode("utf-8").strip()
                    os.system('sudo ip link set CA-C{}-P{}A{} netns {}'.format(j+x,m,i,int(pid1)))
                    os.system('sudo ip link set CA-P{}A{}-C{} netns {}'.format(m,i, j+x, int(pid2)))
                    os.system('sudo nsenter -t {} -n ip link set dev CA-C{}-P{}A{} up'.format(int(pid1), j+x,m,i))
                    os.system('sudo nsenter -t {} -n ip link set dev CA-P{}A{}-C{} up'.format(int(pid2), m,i, j+x))
                   
        # Veth pairs from agg switches to edge switches
        
        for i in range(self.k): 
            for j in range(int(self.k/2)): 
                for m in range(int(self.k/2)):
                    os.system("sudo ip link add AE-P{}A{}-P{}E{} type veth peer name AE-P{}E{}-P{}A{}".format(i,j,i,m,i,m,i,j))
                    # set AE-P{}A{}-P{}E{} up in pod-{}-agg-{}
                    # set AE-P{}E{}-P{}A{} up in pod-{}-edge-{}
                    pid1 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-agg-{}'.format(i,j)]).decode("utf-8").strip()
                    pid2 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(i,m)]).decode("utf-8").strip()
                    os.system('sudo ip link set AE-P{}A{}-P{}E{} netns {}'.format(i,j,i,m,int(pid1)))
                    os.system('sudo ip link set AE-P{}E{}-P{}A{} netns {}'.format(i,m,i,j,int(pid2)))
                    os.system('sudo nsenter -t {} -n ip link set dev AE-P{}A{}-P{}E{} up'.format(int(pid1), i,j,i,m))
                    os.system('sudo nsenter -t {} -n ip link set dev AE-P{}E{}-P{}A{} up'.format(int(pid2), i,m,i,j))
                
        # Veth pairs from edge switches to hosts
        
        for i in range(self.k):
            for j in range(int(self.k/2)):
                for m in range(int(self.k/2)):         
                    os.system("sudo ip link add EH-P{}E{}-P{}H{} type veth peer name EH-P{}H{}-P{}E{}".format(i,j,i,m+(j*int(self.k/2)),i,m+(j*int(self.k/2)), i, j ))
                    # set EH-P{}E{}-P{}H{} up in pod-{}-edge-{}
                    # set EH-P{}H{}-P{}E{} up in pod-{}-host-{}
                    pid1 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-edge-{}'.format(i,j)]).decode("utf-8").strip()
                    pid2 = sp.check_output(['docker', 'inspect', '-f', '{{.State.Pid}}', 'pod-{}-host-{}'.format(i,m+(j*int(self.k/2)))]).decode("utf-8").strip()
                    os.system('sudo ip link set EH-P{}E{}-P{}H{} netns {}'.format(i,j,i,m+(j*int(self.k/2)),int(pid1)))
                    os.system('sudo ip link set EH-P{}H{}-P{}E{} netns {}'.format(i,m+(j*int(self.k/2)), i, j, int(pid2)))
                    os.system('sudo nsenter -t {} -n ip link set dev EH-P{}E{}-P{}H{} up'.format(int(pid1), i,j,i,m+(j*int(self.k/2))))
                    os.system('sudo nsenter -t {} -n ip link set dev EH-P{}H{}-P{}E{} up'.format(int(pid2), i,m+(j*int(self.k/2)), i, j))
            
    # WARNING: It will destroy all containers.
    def clean(self):
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
