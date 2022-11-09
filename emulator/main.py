from fattree import ContainerManager

if __name__ == "__main__":
    mgr = Fattree_BGP(4)
    mgr.clean()
    mgr.start()
    mgr.connect()
    # mgr.clean()
    print("Hello FatTree")
    