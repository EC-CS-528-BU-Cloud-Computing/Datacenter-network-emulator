from BGP import *
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py fattree_k")
    k = int(sys.argv[1])
    mgr = BGP(k)
    mgr.distroyContainers()
    mgr.createContainers()

    mgr.BGPConfig()
    mgr.startRouter()

    mgr.assignLoIP()
    mgr.addLinks()

    # mgr.distroyContainers()
    print("Hello FatTree (k = {})!".format(k))
    