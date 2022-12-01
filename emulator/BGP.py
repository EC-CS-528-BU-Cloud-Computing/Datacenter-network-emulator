from fattree import *

class BGP(FatTree):
    def __init__(self, k) -> None:
        super(BGP, self).__init__(k)
        self.frr_bgp_path = "/etc/frr/"
        self.tmp_file_path = "./bgpd.conf"

    def startRouter(self):
        core_id = 0
        for x in range(0, self.num_of_half_pod_sw):
            for y in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it core-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(core_id))
                os.system("docker restart core-{}".format(core_id))
                core_id += 1
        for pod in range(0, self.k):
            for agg in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it pod-{}-agg-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(pod, agg))
                os.system("docker restart pod-{}-agg-{}".format(pod, agg))
            for edge in range(0, self.num_of_half_pod_sw):
                os.system("docker exec -it pod-{}-edge-{} sed -i \'/bgpd=no/c\\bgpd=yes\' /etc/frr/daemons".format(pod, edge))
                os.system("docker restart pod-{}-edge-{}".format(pod, edge))


    def gen_core_agg_bgpd_conf(self, asn, ip_lo, neighbor_list):
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
            f.write("       network " + ip_lo + "/32\n")
            f.write("       maximum-paths 64\n")
            f.write("   exit-address-family\n")

    def gen_edge_bgpd_conf(self, asn, ip_lo, neighbor_list):
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
            f.write("   address-family ipv4 unicast\n")
            f.write("       neighbor ISL activate\n")
            f.write("       network " + ip_lo + "/24\n")
            f.write("       maximum-paths 64\n")
            f.write("   exit-address-family\n")

    # redistribute route and route map 
    def gen_redistribute_route_bgpd_conf(self, asn, ip_lo, neighbor_list):
        with open(self.tmp_file_path, "w") as f:
            f.write("ip prefix-list DC_LOCAL_SUBNET 5 permit 15.0.0.0/8 le 24\n")
            f.write("ip prefix-list DC_LOCAL_SUBNET 10 permit 15.0.0.0/8 le 32\n")
            f.write("route-map ACCEPT_DC_LOCAL permit 10\n")
            f.write("   match ip-address DC_LOCAL_SUBNET\n")
            f.write("\n")
            f.write("router bgp " + str(asn) + "\n")
            f.write("   bgp router-id " + ip_lo + "\n")
            f.write("   bgp log-neighbor-changes\n")
            f.write("   no bgp ebgp-requires-policy\n")
            f.write("   timers bgp 3 9\n")
            f.write("   neighbor peer-group ISL\n")
            f.write("   neighbor ISL advertisement-interval 0\n")
            f.write("   neighbor ISL timers connect 5\n")
            for i in range(len(neighbor_list)):
                # f.write("   neighbor " + neighbor_list[i]["ip"] + " remote-as " + str(neighbor_list[i]["asn"]) + "\n")
                f.write("   neighbor " + neighbor_list[i]["ip"] + " remote-as external\n")
                f.write("   neighbor " + neighbor_list[i]["ip"] + " peer-group ISL\n")
            f.write("   address-family ipv4 unicast\n")
            f.write("       neighbor ISL activate\n")
            f.write("       redistribute connected route-map ACCEPT_DC_LOCAL\n")
            f.write("       maximum-paths 64\n")
            f.write("   exit-address-family\n")

    def genCoreConfig(self, x, y, core_id, asn, redistribute):
        neighbor_list = []
        agg = x + self.num_of_half_pod_sw - 1
        ip_lo = "15.{}.{}.{}".format(self.k, x, y)
        for pod in range(0, self.k):
            ip = "169.{}.{}.{}".format(self.k + core_id, pod, 2)
            asn_agg = 65000 + pod * 20
            tmp = {"ip": ip, "asn": asn_agg}
            neighbor_list.append(tmp)
        if not redistribute: 
            self.gen_core_agg_bgpd_conf(asn, ip_lo, neighbor_list)
        else:
            self.gen_redistribute_route_bgpd_conf(asn, ip_lo, neighbor_list)
        os.system("docker cp " + self.tmp_file_path + " " + "core-{}".format(core_id) + ":" + self.frr_bgp_path)
    
    def genAggConfig(self, pod, agg, asn, redistribute):
        neighbor_list = []
        ip_lo = "15.{}.{}.1".format(pod, self.num_of_half_pod_sw + agg)
        port_id = self.num_of_half_pod_sw * agg + 1
        for edge in range(0, self.num_of_half_pod_sw):
            ip = "169.{}.{}.{}".format(pod, port_id, 2)
            asn_edge = 65000 + pod * 20 + edge + 1
            tmp = {"ip": ip, "asn": asn_edge}
            neighbor_list.append(tmp)
            port_id += 1

        for core_id in range(0, self.num_of_core_sw):
            ip = "169.{}.{}.{}".format(self.k + core_id, pod, 1)
            asn_core = 65534
            tmp = {"ip": ip, "asn": asn_core}
            neighbor_list.append(tmp)

        if not redistribute:
            self.gen_core_agg_bgpd_conf(asn, ip_lo, neighbor_list)
        else:
            self.gen_redistribute_route_bgpd_conf(asn, ip_lo, neighbor_list)
        
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-agg-{}".format(pod, agg) + ":" + self.frr_bgp_path)
    
    def genEdgeConfig(self, pod, edge, asn, redistribute):
        neighbor_list = []
        ip_lo = "15.{}.{}.2".format(pod, edge)
        port_id = edge + 1
        asn_agg = 65000 + pod * 20
        for agg in range(0, self.num_of_half_pod_sw):
            ip = "169.{}.{}.{}".format(pod, port_id, 1)
            tmp = {"ip": ip, "asn": asn_agg}
            neighbor_list.append(tmp)
            port_id += self.num_of_half_pod_sw
        if not redistribute:
            self.gen_edge_bgpd_conf(asn, ip_lo, neighbor_list)
        else:
            self.gen_redistribute_route_bgpd_conf(asn, ip_lo, neighbor_list)
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-edge-{}".format(pod, edge) + ":" + self.frr_bgp_path)

    def BGPConfig(self, redistribute):
        
        # Core Switches
        # Core switches have the same ASN 65534
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            for y in range(1, self.num_of_half_pod_sw + 1):
                asn_core = 65534
                self.genCoreConfig(x, y, core_id, asn_core, redistribute)
                core_id += 1

        for pod in range(0, self.k):
            # Aggregation Switches
            asn_agg = 65000 + pod * 20
            for agg in range(0, self.num_of_half_pod_sw):
                self.genAggConfig(pod, agg, asn_agg, redistribute)
            
            # Edge Switches
            for edge in range(0, self.num_of_half_pod_sw):
                asn_edge = asn_agg + edge + 1
                self.genEdgeConfig(pod, edge, asn_edge, redistribute)

    # unnumbered BGP
    def gen_unnumbered_bgpd_conf(self, asn, ip_lo, port_list): # doesn't work with docker containers
        with open(self.tmp_file_path, "w") as f:
            f.write("router bgp " + str(asn) + "\n")
            f.write("   bgp router-id " + ip_lo + "\n")
            f.write("   bgp log-neighbor-changes\n")
            f.write("   no bgp ebgp-requires-policy\n")
            f.write("   timers bgp 3 9\n")
            f.write("   neighbor peer-group ISL\n")
            f.write("   neighbor ISL advertisement-interval 0\n")
            f.write("   neighbor ISL timers connect 5\n")
            for i in range(len(port_list)):
                f.write("   neighbor " + port_list[i]["port"] + " interface remote-as " + str(port_list[i]["asn"]) + "\n")
                f.write("   neighbor " + port_list[i]["port"] + " interface peer-group ISL\n")
            f.write("   address-family ipv4 unicast\n")
            f.write("       neighbor ISL activate\n")
            if asn % 20 != 0 and asn != 65534:
                f.write("       network " + ip_lo + "/24\n")
            else:
                f.write("       network " + ip_lo + "/32\n")
            f.write("       maximum-paths 64\n")
            f.write("   exit-address-family\n")

    def genUnnumberedCoreConfig(self, x, y, core_id, asn_core):
        port_list = []
        agg = x + self.num_of_half_pod_sw - 1
        ip_lo = "15.{}.{}.{}".format(self.k, x, y)
        for pod in range(0, self.k):
            asn_agg = 65000 + pod * 20
            tmp = {"port": "ca-c-{}-p-{}-a-{}".format(core_id, pod, agg), "asn": asn_agg}
            port_list.append(tmp)
        self.gen_unnumbered_bgpd_conf(asn_core, ip_lo, port_list)
        os.system("docker cp " + self.tmp_file_path + " " + "core-{}".format(core_id) + ":" + self.frr_bgp_path)
    
    def genUnnumberedAggConfig(self, pod, agg, asn_agg):
        port_list = []
        ip_lo = "15.{}.{}.1".format(pod, self.num_of_half_pod_sw + agg)
        for edge in range(0, self.num_of_half_pod_sw):
            asn_edge = 65000 + pod * 20 + edge + 1
            tmp = {"port": "ae-p-{}-a-{}-e-{}".format(pod, agg, edge), "asn": asn_edge}
            port_list.append(tmp)

        for core_id in range(0, self.num_of_core_sw):
            asn_core = 65534
            tmp = {"port": "ca-p-{}-a-{}-c-{}".format(pod, agg, core_id), "asn": asn_core}
            port_list.append(tmp)
        self.gen_unnumbered_bgpd_conf(asn_agg, ip_lo, port_list)
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-agg-{}".format(pod, agg) + ":" + self.frr_bgp_path)

    def genUnnumberedEdgeConfig(self, pod, edge, asn_edge):
        port_list = []
        ip_lo = "15.{}.{}.2".format(pod, edge)
        for agg in range(0, self.num_of_half_pod_sw):
            asn_agg = 65000 + pod * 20
            tmp = {"port": "ae-p-{}-e-{}-a-{}".format(pod, edge, agg), "asn": asn_agg}
            port_list.append(tmp)
        self.gen_unnumbered_bgpd_conf(asn_edge, ip_lo, port_list)
        os.system("docker cp " + self.tmp_file_path + " " + "pod-{}-edge-{}".format(pod, edge) + ":" + self.frr_bgp_path)


    def unnumberedBGP(self):
        # Core Switches
        # Core switches have the same ASN 65534
        core_id = 0
        for x in range(1, self.num_of_half_pod_sw + 1):
            for y in range(1, self.num_of_half_pod_sw + 1):
                asn_core = 65534
                self.genUnnumberedCoreConfig(x, y, core_id, asn_core)
                core_id += 1

        for pod in range(0, self.k):
            # Aggregation Switches
            asn_agg = 65000 + pod * 20
            for agg in range(0, self.num_of_half_pod_sw):
                self.genUnnumberedAggConfig(pod, agg, asn_agg)
            
            # Edge Switches
            for edge in range(0, self.num_of_half_pod_sw):
                asn_edge = asn_agg + edge + 1
                self.genUnnumberedEdgeConfig(pod, edge, asn_edge)



    