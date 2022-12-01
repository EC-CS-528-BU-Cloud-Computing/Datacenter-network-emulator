from BGP import *
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 main.py fattree_k [unnumbered]")
    unnumbered = False   
    k = int(sys.argv[1])
    if len(sys.argv) == 3 and sys.argv[2] == "unnumbered":
        unnumbered = True

    mgr = BGP(k)
    mgr.distroyContainers()
    mgr.createContainers()

    if not unnumbered:
        mgr.BGPConfig()
    else:
        mgr.unnumberedBGP()
    mgr.startRouter()

    mgr.assignLoIP()
    if not unnumbered:
        mgr.addLinks()
    else:
        mgr.addLinksUnnumbered()

    # mgr.distroyContainers()
    print("Hello FatTree (k = {})!".format(k))
    