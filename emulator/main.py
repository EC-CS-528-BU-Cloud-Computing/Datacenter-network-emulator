from BGP import *

if __name__ == "__main__":
    mgr = BGP(2)
    mgr.distroyContainers()
    mgr.createContainers()
    mgr.BGPConfig()
    mgr.startRouter()

    mgr.assignLoIP()
    mgr.addLinks()
    # mgr.distroyContainers()
    print("Hello FatTree!")
    