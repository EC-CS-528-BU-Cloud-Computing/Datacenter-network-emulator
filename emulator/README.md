# Datacenter Network Emulator

### Getting Start

Install Python3 and dependencies using:  

```
pip3 -r requirements.txt
```


### Before You Pull Request

Add dependencies so that other team member can run your program.  

```
pip3 freeze > requirements.txt
```

### Build host base image
```
cd dockerbuild
docker build -t "ubuntu_net:Dockerfile" .
docker images
```

### Run emulator
```
python3 main.py k (2 <= k <= 18)
```