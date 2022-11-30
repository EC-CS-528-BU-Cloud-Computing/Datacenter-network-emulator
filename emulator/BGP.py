from fattree import *

class BGP(FatTree):
    def __init__(self, k) -> None:
        super(BGP, self).__init__(k)
        self.frr_bgp_path = "/etc/frr/"
        self.tmp_file_path = "./bgpd.conf"

    def gen_bgpd_conf(self, asn, ip_lo, neighbor_list):
        with open(self.tmp_file_path, "w") as f:
            f.write("router bgp " + str(asn) + "\n")
            f.write("   bgp router-id " + ip_lo + "\n")
            f.write("   bgp log-neighbor-changes\n")
            f.write("   no bgp ebgp-requires-policy\n")
            f.write("   timers bgp 3 9\n")
            f.write("   neighbor peer-group ISL\n")
            f.write("   neighbor ISL advertisement-interval 0\n")
            f.write("   neighbor ISL timers connect 5\n")
            for i in range(len(neighbor_list)):
                f.write("   neighbor " + neighbor_list[i]["ip"] + " remote-as " + str(neighbor_list[i]["asn"]) + "\n")
                f.write("   neighbor " + neighbor_list[i]["ip"] + " peer-group ISL\n")
            f.write("   bgp bestpath as-path multipath-relax\n")
            f.write("   address-family ipv4 unicast\n")
            f.write("       neighbor ISL activate\n")
            
            if asn == 65534:
                f.write("       network " + ip_lo + "/32\n")
            elif (asn - 65000) % 20 == 0:
                f.write("       network " + ip_lo + "/32\n")
            else:
                f.write("       network " + ip_lo + "/24\n")
            f.write("       maximum-paths 64\n")
            f.write("   exit-address-family\n")

    def genCoreConfig(self, x, y, core_id, asn):
        neighbor_list = []
        agg = x + self.num_of_half_pod_sw - 1
        ip_lo = "15.{}.{}.{}".format(self.k, x, y)
        for pod in range(0, self.k):
            ip = "169.{}.{}.{}".format(self.k + pod, agg, core_id)
            asn_agg = 65000 + pod * 20
            tmp = {"ip": ip, "asn": asn_agg}
            neighbor_list.append(tmp)
        self.gen_bgpd_conf(asn, ip_lo, neighbor_list)
        os.system("docker cp " + self.tmp_file_path + " " + "core-{}".format(core_id) + ":" + self.frr_bgp_path)
    
    def genAggConfig(self, pod, agg, asn):
        neighbor_list = []
        ip_lo = "15.{}.{}.1".format(pod, self.num_of_half_pod_sw + agg)
        for edge in range(0, self.num_of_half_pod_sw):
            ip = "169.{}.{}.{}".format(pod, edge, self.num_of_half_pod_sw + agg)
            asn_edge = 65000 + pod * 20 + edge + 1
            tmp = {"ip": ip, "asn": asn_edge}
            neighbor_list.append(tmp)
        for core_id in range(0, self.num_of_core_sw):
            ip = "169.{}.{}.{}".format(self.k + pod, agg, core_id)
            asn_core = 65534
            tmp = {"ip": ip, "asn": asn_core}
            neighbor_list.append(tmp)
        self.gen_bgpd_conf(asn, ip_lo, neighbor_list)
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-agg-{}".format(pod, agg) + ":" + self.frr_bgp_path)
    
    def genEdgeConfig(self, pod, edge, asn):
        neighbor_list = []
        ip_lo = "15.{}.{}.1".format(pod, edge)
        for agg in range(0, self.num_of_half_pod_sw):
            ip = "169.{}.{}.{}".format(pod, edge, agg+self.num_of_half_pod_sw)
            asn_agg = 65000 + pod * 20
            tmp = {"ip": ip, "asn": asn_agg}
            neighbor_list.append(tmp)
        self.gen_bgpd_conf(asn, ip_lo, neighbor_list)
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-edge-{}".format(pod, edge) + ":" + self.frr_bgp_path)

    def BGPConfig(self):
        
        # Core Switches
        # Core switches have the same ASN 65534
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            for y in range(1, self.num_of_half_pod_sw + 1):
                asn_core = 65534
                self.genCoreConfig(x, y, core_id, asn_core)
                core_id += 1

        for pod in range(0, self.k):
            # Aggregation Switches
            asn_agg = 65000 + pod * 20
            for agg in range(0, self.num_of_half_pod_sw):
                self.genAggConfig(pod, agg, asn_agg)
            
            # Edge Switches
            for edge in range(0, self.num_of_half_pod_sw):
                asn_edge = asn_agg + edge + 1
                self.genEdgeConfig(pod, edge, asn_edge)
        
    def startRouter(self):
        core_id = 0
        for x in range(0, self.num_of_half_pod_sw):
            for y in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it core-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(core_id))
                # print('docker exec -it core-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons'.format(core_id))
                os.system("docker restart core-{}".format(core_id))
                core_id += 1
        for pod in range(0, self.k):
            for agg in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it pod-{}-agg-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(pod, agg))
                os.system("docker restart pod-{}-agg-{}".format(pod, agg))
            for edge in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it pod-{}-edge-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(pod, edge))
                os.system("docker restart pod-{}-edge-{}".format(pod, edge))
