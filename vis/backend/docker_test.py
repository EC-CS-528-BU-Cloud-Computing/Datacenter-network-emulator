import docker
import json
import subprocess as sp
client = docker.from_env()
kv = { "nodes" : [], "edges": [] }

for c in client.containers.list():
    node_type = "circle"
    size = 80
    if "host" not in c.name:
        node_type = "rect"
        size = [80, 60]
    kv["nodes"].append({
        "id": c.name,
        "label": c.name,
        "size": 80,
        "type": node_type
        })
    links_output = sp.check_output("sudo docker exec " + c.name + 
                            " ip link show | grep UP | grep -v eth0 | grep -v lo | awk -F: '{print $2}' | awk -F@ '{print $1}' | tr -d ' '", shell=True).decode("utf-8")
    links = links_output.split('\n')[:-1]
    edge = {
        "source": "",
        "target": ""
    }
    for l in links:
        edge = {
            "source": "",
            "target": ""
        }
        
        if "CA" in l:
            print(l)
            splits = l.split('-')
            cid = ''
            pid = ''
            aid = ''
            if 'A' in splits[1]:
                cid = splits[2][1:]
                pid = splits[1].split('A')[0][1:]
                aid = splits[1].split('A')[1]
                edge = {
                    "source": "pod-{}-agg-{}".format(pid, aid),
                    "target": "core-{}".format(cid)
                }
                print("Core and aggregation: pod-{}-agg-{} to core-{}".format(pid, aid, cid))
            else:
                cid = splits[1][1:]
                pid = splits[2].split('A')[0][1:]
                aid = splits[2].split('A')[1]
                edge = {
                    "source": "core-{}".format(cid),
                    "target": "pod-{}-agg-{}".format(pid, aid)
                }
            
                print("Core and aggregation: core-{} to pod-{}-agg-{}".format(cid, pid, aid))
        
        if "EH" in l:
            print(l)
            splits = l.split('-')
            pid0 = ''
            hid0 = ''
            pid1 = ''
            eid1 = ''
            if 'H' in splits[1]:
                pid0 = splits[1].split('H')[0][1:]
                hid0 = splits[1].split('H')[1]
                pid1 = splits[2].split('E')[0][1:]
                eid1 = splits[2].split('E')[1]
                edge = {
                    "source": "pod-{}-host-{}".format(pid0, hid0),
                    "target": "pod-{}-edge-{}".format(pid1, eid1)
                }
                print("Edge and host: pod-{}-host-{} to pod-{}-edge-{}".format(pid0, hid0, pid1, eid1))
            else:
                pid1 = splits[1].split('E')[0][1:]
                eid1 = splits[1].split('E')[1]
                pid0 = splits[2].split('H')[0][1:]
                hid0 = splits[2].split('H')[1]
                edge = {
                    "source": "pod-{}-edge-{}".format(pid1, eid1),
                    "target": "pod-{}-host-{}".format(pid0, hid0),
                }
                print("Edge and host: pod-{}-edge-{} to pod-{}-host-{}".format(pid1, eid1, pid0, hid0))
        if "AE" in l:
            print(l)
            splits = l.split('-')
            pid0 = ''
            aid0 = ''
            pid1 = ''
            eid1 = ''
            if 'A' in splits[1]:
                pid0 = splits[1].split('A')[0][1:]
                aid0 = splits[1].split('A')[1]
                pid1 = splits[2].split('E')[0][1:]
                eid1 = splits[2].split('E')[1]
                edge = {
                    "source": "pod-{}-agg-{}".format(pid0, aid0),
                    "target": "pod-{}-edge-{}".format(pid1, eid1),
                }
                print("Edge and host: pod-{}-agg-{} to pod-{}-edge-{}".format(pid0, aid0, pid1, eid1))
            else:
                pid1 = splits[1].split('E')[0][1:]
                eid1 = splits[1].split('E')[1]
                pid0 = splits[2].split('A')[0][1:]
                aid0 = splits[2].split('A')[1]
                edge = {
                    "source": "pod-{}-edge-{}".format(pid1, eid1),
                    "target": "pod-{}-agg-{}".format(pid0, aid0),
                }
                print("Edge and host: pod-{}-edge-{} to pod-{}-agg-{}".format(pid1, eid1, pid0, aid0))
        kv["edges"].append(edge)
    
print(kv['edges'])