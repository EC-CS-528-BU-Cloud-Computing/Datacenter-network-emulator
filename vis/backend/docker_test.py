import docker
import json
client = docker.from_env()
kv = { "nodes" : [] }
for c in client.containers.list():
    kv["nodes"].append(c.name)

print(json.dumps(kv))