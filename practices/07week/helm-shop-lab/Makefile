# helm-shop-lab 실습 단축 명령. 각 타깃이 실행하는 helm 명령을 그대로 읽어 보는 것이 실습의 일부이다.
CLUSTER   ?= my-k8s
NS        ?= shop-dev
IMAGE     ?= ghcr.io/cstpeace0191/shop-api
TAG       ?= dev-$(shell git rev-parse --short HEAD 2>/dev/null || date +%s)
CHART     := charts/shop-api

.PHONY: cluster build db-dev deploy-dev status test history rollback lint template diff argocd clean

cluster:            ## kind 클러스터 + metrics-server + Argo CD
	./scripts/kind-setup.sh

build:              ## 앱 이미지 빌드 후 kind 노드에 적재 (레지스트리 불필요)
	docker build -t $(IMAGE):$(TAG) app
	kind load docker-image $(IMAGE):$(TAG) --name $(CLUSTER)
	@echo "빌드한 태그: $(TAG)"

db-dev:             ## [Lab 1] 개발용 PostgreSQL 릴리스
	helm upgrade --install shop-db charts/shop-db -n $(NS) --create-namespace --wait

deploy-dev:         ## [Lab 1·2] shop-api 설치/업그레이드 (마이그레이션 훅 포함)
	helm upgrade --install shop-api $(CHART) -n $(NS) \
	  -f $(CHART)/values-dev.yaml --set image.repository=$(IMAGE) --set image.tag=$(TAG) --wait --timeout 3m

status:
	helm list -n $(NS)
	kubectl -n $(NS) get deploy,po,svc,job

test:               ## helm test 로 /items 응답 확인
	helm test shop-api -n $(NS)

history:
	helm history shop-api -n $(NS)

rollback:           ## make rollback REV=2
	helm rollback shop-api $(REV) -n $(NS) --wait

lint:
	helm lint charts/shop-db
	helm lint $(CHART) -f $(CHART)/values-dev.yaml
	helm lint $(CHART) -f $(CHART)/values-prod.yaml

template:           ## 렌더링 결과만 보기 (ENV=dev|prod)
	helm template shop-api $(CHART) -f $(CHART)/values-$(or $(ENV),dev).yaml

diff:               ## helm-diff 플러그인 필요
	helm diff upgrade shop-api $(CHART) -n $(NS) -f $(CHART)/values-dev.yaml --set image.tag=$(TAG)

argocd:             ## [Lab 4] 운영 Application 등록
	kubectl apply -f argocd/shop-prod.yaml

clean:
	-helm uninstall shop-api -n $(NS)
	-helm uninstall shop-db -n $(NS)
	-kubectl delete ns $(NS)
