CWD := $(shell basename ${PWD})
# Docker image name, based on current working directory
IMAGE := ${CWD}
# Version (tag used with docker push)
VERSION := v0.4.3-20-gaf8f695

# Linux build image name (does not conflict with go build)
LINUX_EXE := ${IMAGE}.exe
# List of docker images
IMAGE_LIST := ${IMAGE}-images.out

##
# build the standalone pingmesh application
##
cmd/${IMAGE}/${IMAGE}: cmd/*/*.go pkg/*/*.go
	cd cmd/${IMAGE} && go build -v 

# build the avgping client 
cmd/avgping/avgping: cmd/*/*.go pkg/*/*.go check-version
	cd cmd/avgping && go build -v 

.PHONY: check-version update-version
check-version: cmd/${IMAGE}/version.go
	@-sh -c "grep ${VERSION} $? >/dev/null 2>/dev/null" 

.PHONY: standalone install
standalone:	cmd/${IMAGE}/${IMAGE} cmd/avgping/avgping
install:	cmd/*/*.go pkg/*/*.go
	cd cmd/${IMAGE} && go install -v
	cd cmd/avgping && go install -v

test:	cmd/${IMAGE}/${IMAGE} test_pingmesh.sh
	./test_pingmesh.sh
