#!/usr/bin/env bash
# 실습용 kind 클러스터 + metrics-server + Argo CD 설치 (플랫폼 컴포넌트도 Helm 으로 설치)
set -euo pipefail

CLUSTER=${CLUSTER:-my-k8s}

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --name "$CLUSTER"
fi
kubectl cluster-info --context "kind-$CLUSTER"

# HPA 가 CPU 사용률을 읽으려면 metrics-server 가 필요 (kind 는 kubelet 인증서 검증 해제)
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update >/dev/null

helm upgrade --install metrics-server metrics-server/metrics-server \
  -n kube-system --set 'args={--kubelet-insecure-tls}' --wait

if [[ "${WITH_ARGOCD:-1}" == "1" ]]; then
  helm upgrade --install argocd argo/argo-cd \
    -n argocd --create-namespace \
    --set configs.params."server\.insecure"=true \
    --wait --timeout 10m
  echo
  echo "Argo CD 초기 admin 비밀번호:"
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
  echo "UI 접속: kubectl -n argocd port-forward svc/argocd-server 8443:80  →  http://localhost:8443"
fi
