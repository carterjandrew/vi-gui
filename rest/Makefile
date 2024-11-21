VERSION=v1
DOCKERUSER=carterjamesandrew

build:
	docker build -f Dockerfile-rest -t vigui-rest .

push:
	docker tag vigui-rest $(DOCKERUSER)/vigui-rest:$(VERSION)
	docker push $(DOCKERUSER)/vigui-rest:$(VERSION)
	docker tag vigui-rest $(DOCKERUSER)/vigui-rest:latest
	docker push $(DOCKERUSER)/vigui-rest:latest
