from mimetypes import init
import docker

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
        assert (k >= 4)
        self.k =  k
        self.client =  docker.from_env()
        self.num_of_core_sw = int((self.k * self.k) / 4)
        self.num_of_sw_per_pod = int(self.k)
        self.num_of_host_per_pod = int((self.k * self.k) / 4)

    def start(self):
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
                self.client.containers.run("ubuntu", detach=True, init=True, tty=True, name="pod-{}-host-{}".format(i, j))

    # WARNING: It will destroy all containers.
    def clean(self):
        for i in range(self.num_of_core_sw):
            core_sw = self.client.containers.get("core-{}".format(i))
            core_sw.stop()
            core_sw.remove()
        
        for i in range(self.k):
            # Pod Switch
            for j in range(int(self.num_of_sw_per_pod / 2)):
                # Aggregation
                agg_sw = self.client.containers.get(name="pod-{}-agg-{}".format(i, j))
                agg_sw.stop()
                agg_sw.remove()
                # Edge
                edge_sw = self.client.containers.get(name="pod-{}-edge-{}".format(i, j))
                edge_sw.stop()
                edge_sw.remove()
            # Host
            for j in range(self.num_of_host_per_pod):
                host = self.client.containers.get(name="pod-{}-host-{}".format(i, j))
                host.stop()
                host.remove()