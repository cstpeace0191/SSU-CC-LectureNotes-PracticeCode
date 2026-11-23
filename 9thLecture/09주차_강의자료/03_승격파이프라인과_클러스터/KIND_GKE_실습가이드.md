# KIND · GKE 실습 가이드 (강의노트 24쪽)

> 검증 환경에서는 Docker Hub · GCP 에 접근할 수 없어 이 단계는 실행하지 못했습니다.
> Argo CD 설치 이후 단계는 02장에서 실제 Argo CD 로 확인한 것과 같습니다 (`../02_ArgoCD_구조와운영/logs/`).

## 0. 준비 (Windows)

- Docker Desktop (KIND 용)
- `kubectl`, `kind`, `argocd` CLI. winget 으로 설치:

```powershell
winget install Kubernetes.kubectl Kubernetes.kind argoproj.argocd
```

- Config 저장소를 본인 GitHub 에 올리고 `argocd/applicationset.yaml` · `argocd/root-app.yaml` 의 `repoURL` 을 본인 주소로 바꿉니다.

## 1-A. KIND (로컬)

```powershell
kind create cluster --name gitops
```

```powershell
kubectl config use-context kind-gitops
```

## 1-B. GKE (클라우드)

`<클러스터>` · `<존>` · `<프로젝트>` 는 본인 값으로 바꿉니다.

```powershell
gcloud container clusters get-credentials <클러스터> --zone <존> --project <프로젝트>
```

## 2. Argo CD 설치 (공통)

```powershell
kubectl create namespace argocd
```

```powershell
kubectl apply -n argocd --server-side --force-conflicts -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.6.1/manifests/install.yaml
```

```powershell
kubectl -n argocd rollout status deploy/argocd-server
```

## 3. 로그인

초기 비밀번호:

```powershell
argocd admin initial-password -n argocd
```

별도 터미널에서 포트 포워드 (계속 실행해 둡니다):

```powershell
kubectl -n argocd port-forward svc/argocd-server 8080:443
```

```powershell
argocd login localhost:8080 --username admin --insecure
```

## 4. Project · ApplicationSet 적용 (Config 저장소 폴더에서)

```powershell
kubectl apply -f argocd/project.yaml -f argocd/applicationset.yaml
```

```powershell
argocd app list
```

`todo-dev` 는 자동 Sync, `todo-prod` 는 수동입니다 (`../02_ArgoCD_구조와운영/logs/log_appset_generated.txt`).

```powershell
argocd app sync todo-prod
```

## 5. 접속 확인

KIND (port-forward):

```powershell
kubectl -n todo-prod port-forward svc/todo-app 8000:80
```

```powershell
curl.exe -s localhost:8000/api/greeting
```

GKE (prod Service = LoadBalancer):

```powershell
kubectl -n todo-prod get svc todo-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

```powershell
curl.exe -s http://<EXTERNAL-IP>/api/greeting
```

기대 결과: `{"greeting":"Hello GitOps!"}` (#10 이후 이미지) 또는 `{"greeting":"Hello world!"}`.

## 6. 비공개 GHCR 이미지인 경우

이미지 pull 은 Argo CD 가 아니라 kubelet 이 합니다 (14쪽). 네임스페이스마다 imagePullSecret 이 필요합니다.

```powershell
kubectl -n todo-dev create secret docker-registry ghcr --docker-server=ghcr.io --docker-username=<GitHub ID> --docker-password=<read:packages 토큰>
```

## 7. 정리

```powershell
kind delete cluster --name gitops
```

GKE 는 LoadBalancer 를 쓰면 비용이 나오므로 실습이 끝나면 `todo-prod` 를 지우거나 클러스터를 정리합니다.
