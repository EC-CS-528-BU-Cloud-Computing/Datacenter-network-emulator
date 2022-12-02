from BGP import *
import sys
import time

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py fattree_k [redistribute] [unnumbered]")
    unnumbered = False  
    redistribute = False 
    k = int(sys.argv[1])
    for op in sys.argv:
        if op == "redistribute":
            redistribute = True
        if op == "unnumbered":
            unnumbered = True

    mgr = BGP(k)
    mgr.distroyContainers()
    
    mgr.createContainers()

    if not unnumbered:
        mgr.BGPConfig(redistribute)
    else:
        mgr.unnumberedBGP()
    mgr.startRouter()

    mgr.assignLoIP()
    if not unnumbered:
        mgr.addLinks()
    else:
        mgr.addLinksUnnumbered()

    print("Hello FatTree (k = {})!".format(k))

    # mgr.breakCoreAggLink()
    # mgr.breakAggEdgeLink()
    # mgr.recoverCoreAggLink()
    # mgr.recoverAggEdgeLink()

    
    