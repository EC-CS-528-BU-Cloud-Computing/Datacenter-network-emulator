from BGP import *

if __name__ == "__main__":
    mgr = BGP(4)
    mgr.distroyContainers()
    mgr.createContainers()
    mgr.addLinks()
    mgr.BGPConfig()
    # mgr.distroyContainers()
    print("Hello FatTree")
    