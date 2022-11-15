from fastapi import FastAPI
import docker
import json

app = FastAPI()
client = docker.from_env()

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.get("/topology")
async def topology():
    kv = { "nodes" : [], "edges": [] }
    for c in client.containers.list():
        kv["nodes"].append({
            "id": c.name,
            "label": c.name,
            "size": 80
            })

    
    return kv