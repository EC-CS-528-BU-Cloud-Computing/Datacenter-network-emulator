from fastapi import FastAPI
import docker
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI()
client = docker.from_env()

@app.get("/")
async def root():
    return {"message" : "Hello World"}

@app.get("/topology")
async def topology():
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
    return kv