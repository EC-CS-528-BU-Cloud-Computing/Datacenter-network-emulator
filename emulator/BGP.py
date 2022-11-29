from fattree import *

class BGP(FatTree):
    def __init__(self, k) -> None:
        super(BGP, self).__init__(k)

    def genCoreConfig(x, y, core_id, asn):
        pass
    
    def genAggConfig(pod, agg, asn):
        pass
    
    def genEdgeConfig(pod, edge, asn):
        pass

    def BGPConfig(self):
        
        # Core Switches
        # Core switches have the same ASN 65534
        core_id = 0
        for x in range(0, self.k / 2):
            for y in range(0, self.k / 2):
                asn_core = 65534
                genCoreConfig(x, y, core_id, asn_core)
                core_id += 1

        for pod in range(0, self.k):
            # Aggregation Switches
            asn_agg = 65000 + pod * 20
            for agg in range(0, self.k / 2):
                genAggConfig(pod, agg, asn_agg)
            
            # Edge Switches
            for edge in range(0, self.k / 2):
                asn_edge = asn_agg + edge + 1
                genEdgeConfig(pod, edge, asn_edge)
        

