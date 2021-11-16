IMAGE=network-golem
CONTAINER=network-golem

.PHONY: build default open stop clean deep-clean gvmi-push image

build: Dockerfile 
	sudo docker build -t $(IMAGE) .

sheepit.gvmi: build
	sudo gvmkit-build $(IMAGE):latest -o $(IMAGE).gvmi

image: sheepit.gvmi

gvmi-push: sheepit.gvmi
	sudo gvmkit-build $(IMAGE):latest -o $(IMAGE).gvmi --push
	

default: build
	sudo docker run -dit --name $(CONTAINER) $(IMAGE)

open: default
	sudo docker exec -ti $(CONTAINER) "/bin/bash"

stop:
	sudo docker stop $(CONTAINER)

clean: stop
	sudo docker rm $(CONTAINER)

deep-clean:
	sudo docker image rm $(IMAGE)