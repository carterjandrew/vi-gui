VERSION=v1
DOCKERUSER=carterjamesandrew

build:
	docker build -f Dockerfile -t vigui-worker .
push:
	docker tag vigui-worker $(DOCKERUSER)/vigui-worker:$(VERSION)
	docker push $(DOCKERUSER)/vigui-worker:$(VERSION)
	docker tag vigui-worker $(DOCKERUSER)/vigui-worker:latest
	docker push $(DOCKERUSER)/vigui-worker:latest
