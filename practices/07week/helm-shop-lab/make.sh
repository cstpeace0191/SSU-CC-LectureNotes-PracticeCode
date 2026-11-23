#!/usr/bin/env bash
# Windows Git Bash 등 make 가 설치되지 않은 환경을 위한 래퍼 스크립트

# Makefile의 설정값을 기본값으로 읽어옴 (Makefile 수정 시 자동 반영)
MAKEFILE_CLUSTER=$(grep -E '^\s*CLUSTER\s*\??=' Makefile 2>/dev/null | awk -F'=' '{print $2}' | tr -d ' \r\t')
MAKEFILE_NS=$(grep -E '^\s*NS\s*\??=' Makefile 2>/dev/null | awk -F'=' '{print $2}' | tr -d ' \r\t')
MAKEFILE_IMAGE=$(grep -E '^\s*IMAGE\s*\??=' Makefile 2>/dev/null | awk -F'=' '{print $2}' | tr -d ' \r\t')

export CLUSTER="${CLUSTER:-${MAKEFILE_CLUSTER:-my-k8s}}"
export NS="${NS:-${MAKEFILE_NS:-shop-dev}}"
export IMAGE="${IMAGE:-${MAKEFILE_IMAGE:-ghcr.io/cstpeace0191/shop-api}}"

# .git이 없는 환경에서도 build 시 생성된 태그를 deploy-dev에서 그대로 사용할 수 있도록 캐시 지원
LAST_TAG=""
if [[ -f .last_tag ]]; then
  LAST_TAG=$(tr -d ' \r\n' < .last_tag)
fi

DEFAULT_TAG=$(git rev-parse --short HEAD 2>/dev/null || echo "")
if [[ -z "$DEFAULT_TAG" ]]; then
  if [[ "$1" == "build" || -z "$LAST_TAG" ]]; then
    DEFAULT_TAG="$(date +%s)"
  else
    DEFAULT_TAG="${LAST_TAG#dev-}"
  fi
fi

TAG="${TAG:-dev-${DEFAULT_TAG}}"
CHART="charts/shop-api"

target="${1:-help}"
shift 2>/dev/null || true

case "$target" in
  cluster)
    ./scripts/kind-setup.sh
    ;;
  build)
    echo "==> Building Docker image: ${IMAGE}:${TAG}"
    docker build -t "${IMAGE}:${TAG}" app
    echo "==> Loading image into kind cluster: ${CLUSTER}"
    kind load docker-image "${IMAGE}:${TAG}" --name "${CLUSTER}"
    echo "${TAG}" > .last_tag
    echo "빌드한 태그: ${TAG}"
    ;;
  db-dev)
    helm upgrade --install shop-db charts/shop-db -n "${NS}" --create-namespace --wait
    ;;
  deploy-dev)
    STATUS=$(helm status shop-api -n "${NS}" 2>/dev/null | grep -E '^STATUS:' | awk '{print $2}')
    if [[ "$STATUS" == "failed" || "$STATUS" == "pending-install" ]]; then
      echo "==> 이전 실패한 shop-api 릴리스 정리 중..."
      helm uninstall shop-api -n "${NS}" 2>/dev/null || true
    fi
    kubectl -n "${NS}" delete job shop-api-migrate --ignore-not-found 2>/dev/null || true

    echo "==> Deploying shop-api (${IMAGE}:${TAG})..."
    helm upgrade --install shop-api "${CHART}" -n "${NS}" \
      -f "${CHART}/values-dev.yaml" \
      --set image.repository="${IMAGE}" \
      --set image.tag="${TAG}" --wait --timeout 3m
    ;;
  status)
    helm list -n "${NS}"
    kubectl -n "${NS}" get deploy,po,svc,job
    ;;
  test)
    helm test shop-api -n "${NS}"
    ;;
  history)
    helm history shop-api -n "${NS}"
    ;;
  rollback)
    REV="${1:?사용법: ./make.sh rollback <REV>}"
    helm rollback shop-api "${REV}" -n "${NS}" --wait
    ;;
  lint)
    helm lint charts/shop-db
    helm lint "${CHART}" -f "${CHART}/values-dev.yaml"
    helm lint "${CHART}" -f "${CHART}/values-prod.yaml"
    ;;
  template)
    ENV="${ENV:-dev}"
    helm template shop-api "${CHART}" -f "${CHART}/values-${ENV}.yaml"
    ;;
  diff)
    helm diff upgrade shop-api "${CHART}" -n "${NS}" -f "${CHART}/values-dev.yaml" --set image.tag="${TAG}"
    ;;
  argocd)
    kubectl apply -f argocd/shop-prod.yaml
    ;;
  clean)
    helm uninstall shop-api -n "${NS}" || true
    helm uninstall shop-db -n "${NS}" || true
    kubectl delete ns "${NS}" || true
    ;;
  help|*)
    echo "사용법: ./make.sh [target]"
    echo ""
    echo "사용 가능한 타깃:"
    echo "  cluster     kind 클러스터 + metrics-server + Argo CD"
    echo "  build       앱 이미지 빌드 후 kind 노드에 적재"
    echo "  db-dev      [Lab 1] 개발용 PostgreSQL 릴리스"
    echo "  deploy-dev  [Lab 1·2] shop-api 설치/업그레이드"
    echo "  status      현재 상태 확인"
    echo "  test        helm test 로 /items 응답 확인"
    echo "  history     배포 이력 확인"
    echo "  rollback    롤백 (예: ./make.sh rollback 2)"
    echo "  lint        차트 문법 검사"
    echo "  template    렌더링 결과 확인 (ENV=dev|prod ./make.sh template)"
    echo "  diff        변경사항 비교"
    echo "  argocd      [Lab 4] 운영 Application 등록"
    echo "  clean       리소스 정리"
    ;;
esac
