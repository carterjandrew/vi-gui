VERSION=v1
DOCKERUSER=carterjamesandrew

build:
	docker build -f Dockerfile-rest -t vigui-rest .

push:
	docker tag vigui-rest $(DOCKERUSER)/vigui-rest:$(VERSION)
	docker push $(DOCKERUSER)/vigui-rest:$(VERSION)
	docker tag vigui-rest $(DOCKERUSER)/vigui-rest:latest
	docker push $(DOCKERUSER)/vigui-rest:latest

dep:
	kubectl delete -f rest-deployment.yaml
	make build
	make push
	kubectl apply -f rest-deployment.yaml
