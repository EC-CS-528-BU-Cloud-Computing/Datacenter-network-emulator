from fastapi import FastAPI
import docker
import json
import subprocess as sp
from fastapi.middleware.cors import CORSMiddleware
import os
import json
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]
client = docker.from_env()
kv = { "nodes" : [], "edges": [] }
    
for c in client.containers.list():
    print(c)
    node_type = "circle"
    size = 80
    #if "host" not in c.name:
    #    node_type = "rect"
    #    size = [80, 60]
    weight = 1
    if "core" in c.name:
        weight = 200
    if "agg" in c.name:
        weight = 150
    if "edge" in c.name:
        weight = 80
    kv["nodes"].append({
        "id": c.name,
        "label": c.name,
        "size": 80,
        "type": node_type,
        "weight": weight
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
        
        if "ca" in l:
            print(l)
            splits = l.split('-')
            cid = ''
            pid = ''
            aid = ''
            if 'c' in splits[1]:
                cid = splits[2]
                pid = splits[-3]
                aid = splits[-1]
                edge = {
                    "source": "core-{}".format(cid),
                    "target":  "pod-{}-agg-{}".format(pid, aid),
                }
                print("Core and aggregation: pod-{}-agg-{} to core-{}".format(pid, aid, cid))
            else:
                cid = splits[-1]
                pid = splits[2]
                aid = splits[4]
                edge = {
                    "source": "core-{}".format(cid),
                    "target": "pod-{}-agg-{}".format(pid, aid)
                }
            
                print("Core and aggregation: core-{} to pod-{}-agg-{}".format(cid, pid, aid))
        if "ae" in l:
            print(l)
            splits = l.split('-')
            pid0 = ''
            aid0 = ''
            pid1 = ''
            eid1 = ''
            if 'a' in splits[3]:
                pid0 = splits[2]
                aid0 = splits[4]
                pid1 = splits[2]
                eid1 = splits[-1]
                edge = {
                    "source": "pod-{}-agg-{}".format(pid0, aid0),
                    "target": "pod-{}-edge-{}".format(pid1, eid1),
                }
                print("Edge and host: pod-{}-agg-{} to pod-{}-edge-{}".format(pid0, aid0, pid1, eid1))
            else:
                pid1 = splits[2]
                eid1 = splits[4]
                pid0 = splits[2]
                aid0 = splits[-1]
                edge = {
                    "source": "pod-{}-edge-{}".format(pid1, eid1),
                    "target": "pod-{}-agg-{}".format(pid0, aid0),
                }
                print("Edge and host: pod-{}-edge-{} to pod-{}-agg-{}".format(pid1, eid1, pid0, aid0))
        kv["edges"].append(edge)
for l in client.networks.list():
    if "br-" in l.name: 
        output = sp.check_output(["docker", "inspect", l.name]).decode('utf-8')
        js_object = json.loads(output)[0]
        edge_name = ""
        print("-------------")
        print(js_object["Containers"])
        for k, v in js_object["Containers"].items():
            if "edge" in v["Name"]:
                edge_name = v["Name"]
                print(edge_name)
        for k, v in js_object["Containers"].items():
            if "edge" not in v["Name"]:
                edge = {
                    "source": edge_name,
                    "target": v["Name"]
                }
                print(edge)
                kv["edges"].append(edge)
                edge = {
                    "source": v["Name"],
                    "target": edge_name,
                }
                print(edge)
                kv["edges"].append(edge)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()


@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.get("/topology")
async def topology():
    
    return kv