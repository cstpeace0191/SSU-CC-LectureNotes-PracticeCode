# Kind(Kubernetes in Docker) 로컬 클러스터 구축 및 배포 워크플로우 가이드

본 문서는 로컬 개발 환경에서 **Kind(Kubernetes in Docker) 멀티 노드 클러스터(`my-k8s`)를 생성**하고, **`kubectl` 컨텍스트 제어**, **이미지 빌드 및 적재(`kind load` / `docker push`)**, 그리고 **워크스페이스 매니페스트(`kind-*.yaml`) 배포 및 서비스/Ingress 노출**까지의 전 과정을 프로젝트 실제 파일들과 100% 일치하도록 검증·정리한 실습 가이드입니다.

---

## 📋 목차 (Table of Contents)
1. [환경 및 리소스 정보 요약](#1-환경-및-리소스-정보-요약)
2. [사전 준비: 필수 소프트웨어 확인](#2-사전-준비-필수-소프트웨어-확인)
3. [Kind 2-Worker 클러스터 구축 실습 (`kind-config-2workers.yaml`)](#3-kind-2-worker-클러스터-구축-실습-kind-config-2workersyaml)
4. [kubectl 컨텍스트 제어 및 포트 매핑 아키텍처](#4-kubectl-컨텍스트-제어-및-포트-매핑-아키텍처)
5. [컨테이너 이미지 준비 및 배포 전략별 사전 작업](#5-컨테이너-이미지-준비-및-배포-전략별-사전-작업)
   - 5.1 로컬 이미지 빌드 (`docker build`)
   - 5.2 [Local 계열] Kind 노드 사전 적재 (`kind load`)
   - 5.3 [Docker 계열] Docker Hub 원격 푸시 (`docker push`)
6. [프로젝트 `kind-*.yaml` 매니페스트 체계 총정리](#6-프로젝트-kind-yaml-매니페스트-체계-총정리)
7. [워크로드 아키텍처: Deployment vs Pod 분리 설계 이유](#7-워크로드-아키텍처-deployment-vs-pod-분리-설계-이유)
8. [서비스 노출 및 외부 접속 실습 (5가지 방식)](#8-서비스-노출-및-외부-접속-실습-5가지-방식)
   - 8.1 [방법 1] ClusterIP: 내부 통신 전용 (`kind-service-cip.yaml`)
   - 8.2 [방법 2] NodePort: 노드 포트 개방 (`kind-service-np.yaml`)
   - 8.3 [방법 3] LoadBalancer 및 `cloud-provider-kind.exe` (`kind-service-lb.yaml`)
   - 8.4 [방법 4] L7 Ingress 및 NGINX Controller 연동 (`kind-ingress.yaml`)
   - 8.5 [방법 5] 디버깅 도구: `kubectl port-forward` vs `kubectl proxy`
9. [단계별 원클릭 실행 시나리오 (PowerShell)](#9-단계별-원클릭-실행-시나리오-powershell)
10. [핵심 트러블슈팅 가이드](#10-핵심-트러블슈팅-가이드)
11. [Kind 로컬 환경 vs GKE 클라우드 환경 비교](#11-kind-로컬-환경-vs-gke-클라우드-환경-비교)
12. [프로젝트 연관 파일 링크](#12-프로젝트-연관-파일-링크)

---

## 1. 환경 및 리소스 정보 요약

| 항목 | 설정값 | 비고 / 설명 |
| :--- | :--- | :--- |
| **Cluster Name** | `my-k8s` | Kind 쿠버네티스 클러스터 식별 이름 |
| **Node Architecture** | 1 Control-Plane + 2 Workers (총 3개 컨테이너) | Docker 컨테이너 기반 멀티 노드 K8s 클러스터 |
| **K8s Node Image** | `kindest/node:v1.31.x` (또는 최신 `v1.37.0`) | Kind 가상 노드 베이스 이미지 |
| **Host Port Mapping** | `80:80/TCP`, `443:443/TCP` | 호스트 PC $\leftrightarrow$ Control-Plane 간 표준 HTTP/HTTPS 매핑 (Ingress 전용) |
| **Local Image Tag** | `todo-backend:prod` | 로컬 빌드 이미지 (`kind load`로 클러스터 노드에 직접 주입 필요) |
| **Docker Hub Image** | `ssucloud/getting-started-todo-app:todo-backend` | 원격 레지스트리 이미지 (`docker push` 선행 필요) |
| **Application Port** | Backend `3000` (Node.js Express), MySQL `3306` | 컨테이너 내부 수신 포트 |
| **StorageClass** | `standard` (`rancher.io/local-path`) | Kind 기본 스토리지 프로비저너 (1Gi 권장, PVC 바인딩) |
| **Custom StorageClass**| `fast` ([`kind-storageclass.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-storageclass.yaml)) | `volumeBindingMode: WaitForFirstConsumer` 적용 |
| **LoadBalancer 도구** | [`cloud-provider-kind.exe`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/cloud-provider-kind.exe) | Docker 브리지 네트워크 가상 외부 IP(`172.19.0.x`) 프로비저너 |

---

## 2. 사전 준비: 필수 소프트웨어 확인

Kind 환경을 구동하기 위해 로컬 PC에 다음 도구들이 설치 및 실행 중이어야 합니다:

1. **Docker Desktop**: 정상 실행 중이어야 함 (WSL2 백엔드 권장).
2. **Kind CLI**:
   ```powershell
   # 설치 여부 확인
   kind version
   ```
3. **Kubectl CLI**:
   ```powershell
   kubectl version --client
   ```
4. **Cloud Provider Kind**:
   - 프로젝트 디렉토리에 위치한 [`cloud-provider-kind.exe`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/cloud-provider-kind.exe) 바이너리를 사용하여 로컬 LoadBalancer 서비스를 에뮬레이션합니다.

---

## 3. Kind 2-Worker 클러스터 구축 실습 (`kind-config-2workers.yaml`)

표준 L7 Ingress 및 HTTP/HTTPS(80/443) 포트를 호스트 PC와 1:1로 직접 연결하고, 실 운영 환경처럼 워커 노드를 2개로 분리하여 고가용성 워크로드를 배치할 수 있도록 구성합니다.

### 3.1 클러스터 설정 파일: [`kind-config-2workers.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-config-2workers.yaml)

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
# 1. Control Plane 마스터 노드 (표준 L7 Ingress 및 HTTP/HTTPS 포트 매핑)
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  # HTTP 표준 포트: 호스트 PC 80번 ➔ NGINX Ingress Controller 수신 포트 80
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  # HTTPS 보안 포트: 호스트 PC 443번 ➔ NGINX Ingress Controller 수신 포트 443
  - containerPort: 443
    hostPort: 443
    protocol: TCP

# 2. Worker 노드 1
- role: worker

# 3. Worker 노드 2
- role: worker
```

> [!NOTE]
> **포트 매핑 진위 판정**:
> 과거 단일 NodePort 전용 방식(`hostPort: 80` $\leftrightarrow$ `containerPort: 30080`)은 특정 서비스 1개만 호스트 80 포트를 점유하므로 확장성이 떨어집니다. 현재 [`kind-config-2workers.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-config-2workers.yaml)은 **호스트 80/443 포트를 Ingress Controller 전용 포트(80/443)로 직결**하여 Ingress를 통해 여러 백엔드로 트래픽을 분기할 수 있도록 설계되어 있습니다.

### 3.2 클러스터 생성 및 노드 검증

기존 클러스터가 있다면 정리 후 새 설정으로 생성합니다:

```powershell
# 1. 기존 클러스터가 있다면 삭제
kind delete cluster --name my-k8s

# 2. 2-Worker 클러스터 새로 생성
kind create cluster --name my-k8s --config ./kind-config-2workers.yaml

# 3. 생성된 노드 3대(Control-Plane 1대 + Worker 2대) 상태 확인
kubectl get nodes -o wide
```

*정상 출력 예시*:
```text
NAME                   STATUS   ROLES           AGE   VERSION   INTERNAL-IP   OS-IMAGE
my-k8s-control-plane   Ready    control-plane   1m    v1.31.0   172.18.0.4    Ubuntu 24.04 LTS
my-k8s-worker          Ready    <none>          1m    v1.31.0   172.18.0.3    Ubuntu 24.04 LTS
my-k8s-worker2         Ready    <none>          1m    v1.31.0   172.18.0.2    Ubuntu 24.04 LTS
```

---

## 4. kubectl 컨텍스트 제어 및 포트 매핑 아키텍처

### 4.1 등록된 컨텍스트 확인 및 스위칭
Kind는 클러스터 생성 시 로컬 `~/.kube/config`에 `kind-my-k8s` 컨텍스트를 자동 등록하고 즉시 활성화합니다:

```powershell
# 1. 등록된 컨텍스트 목록 확인
kubectl config get-contexts

# 2. Kind 클러스터 컨텍스트로 전환
kubectl config use-context kind-my-k8s

# 3. 현재 활성 컨텍스트 확인
kubectl config current-context
# 출력: kind-my-k8s

# 4. 클러스터 API 통신 확인
kubectl cluster-info
```

### 4.2 Docker Desktop의 포트 매핑 구조 이해

`docker port my-k8s-control-plane` 명령을 실행하면 다음 포트 포워딩이 구성되어 있음을 확인할 수 있습니다:

```text
[호스트 PC (Windows)]
   │
   ├─ 웹 브라우저 (http://localhost:80 / 443) ──➔ Docker 포트포워딩 (80:80, 443:443)
   │                                                 │
   │                                                 ▼ [my-k8s-control-plane 노드 컨테이너]
   │                                                 └─ NGINX Ingress Controller (80 / 443)
   │                                                       │
   │                                                       └─ L7 라우팅 ➔ todo-backend 파드 (3000)
   │
   └─ kubectl CLI (https://127.0.0.1:<임의포트>) ──➔ Docker 포트포워딩 (<임의포트>:6443)
                                                     │
                                                     ▼ [my-k8s-control-plane 노드 컨테이너]
                                                     └─ kube-apiserver (6443)
```

1. **`80:80` / `443:443`**: 호스트 브라우저에서 `http://localhost` 접속 시 Control-Plane 노드의 Ingress Controller로 진입하는 통로.
2. **`<임의포트>:6443`**: 호스트의 `kubectl` 명령어가 마스터 API 서버(`kube-apiserver`)와 통신하는 전용 채널.

---

## 5. 컨테이너 이미지 준비 및 배포 전략별 사전 작업

배포할 YAML 매니페스트에 따라 이미지를 공급하는 방식이 다릅니다:
- **`kind-*-Local.yaml`** $\rightarrow$ 로컬 빌드 후 **Kind 클러스터 노드로 직접 적재(`kind load`)**
- **`kind-*-Docker.yaml`** $\rightarrow$ 로컬 빌드 후 **Docker Hub 원격 레지스트리로 푸시(`docker push`)**

```
 [로컬 소스 코드]
        │
        ▼ (docker build -t todo-backend:prod .)
 [로컬 Docker 데몬 캐시]
        │
        ├──▶ [시나리오 A: Local 매니페스트 배포 시]
        │       │
        │       ▼ (kind load docker-image todo-backend:prod --name my-k8s)
        │    [Kind 가상 노드 3대 내부 containerd 캐시] ──▶ kind-*-Local.yaml 적용
        │
        └──▶ [시나리오 B: Docker Hub 매니페스트 배포 시]
                │
                ▼ (docker tag & docker push ssucloud/getting-started-todo-app:todo-backend)
             [Docker Hub 원격 레지스트리] ──────────────▶ kind-*-Docker.yaml 적용
```

### 5.1 로컬 컨테이너 이미지 빌드 (공통)
프로젝트 루트 디렉토리의 [`Dockerfile`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/Dockerfile)을 기반으로 프로덕션 이미지를 빌드합니다:

```powershell
docker build -t todo-backend:prod .
```

### 5.2 [Local 계열] Kind 노드 사전 적재 (`kind load`)
- **적용 대상**:
  - [`kind-deployment-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Local.yaml) (풀 스택 올인원)
  - [`kind-pod-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Local.yaml)
  - [`kind-replicaset-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Local.yaml)
  - [`kind-deployment-only-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Local.yaml)

- **필수 이유**:
  Kind 노드는 호스트의 Docker 데몬과 격리된 독자적인 `containerd` 런타임을 구동합니다. `todo-backend:prod`는 원격 레지스트리 주소가 없는 로컬 이미지이므로, `kind load`로 노드 내부에 주입하지 않으면 파드가 **`ErrImagePull`** / **`ImagePullBackOff`** 오류를 일으킵니다.

- **적재 명령어**:
  ```powershell
  kind load docker-image todo-backend:prod --name my-k8s
  ```

### 5.3 [Docker 계열] Docker Hub 원격 푸시 (`docker push`)
- **적용 대상**:
  - [`kind-deployment-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Docker.yaml) (풀 스택 올인원)
  - [`kind-pod-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Docker.yaml)
  - [`kind-replicaset-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Docker.yaml)
  - [`kind-deployment-only-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Docker.yaml)

- **푸시 절차**:
  ```powershell
  # 1. Docker Hub 로그인
  docker login

  # 2. 이미지 태깅
  docker tag todo-backend:prod ssucloud/getting-started-todo-app:todo-backend

  # 3. Docker Hub 푸시
  docker push ssucloud/getting-started-todo-app:todo-backend
  ```

---

## 6. 프로젝트 `kind-*.yaml` 매니페스트 체계 총정리

프로젝트 폴더 내의 YAML 매니페스트 파일들은 **리소스 컨트롤러 계층(Pod $\rightarrow$ ReplicaSet $\rightarrow$ Deployment)** 및 **이미지 공급처(Local vs Docker Hub)**에 따라 구성되어 있습니다.

### 6.1 워크로드 매니페스트 매트릭스

| 파일명 | 컨트롤러 타입 | 이미지 경로 | 리소스 구성 내역 | 필수 선행 조건 |
| :--- | :--- | :--- | :--- | :--- |
| [`kind-deployment-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Local.yaml) | **Deployment (올인원)** | `todo-backend:prod` | Secret, ConfigMap, PVC, MySQL(Pod/Svc), Backend Deployment(2), ClusterIP | `kind load` 필수 |
| [`kind-deployment-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Docker.yaml) | **Deployment (올인원)** | `ssucloud/...:todo-backend` | Secret, ConfigMap, PVC, MySQL(Pod/Svc), Backend Deployment(2), ClusterIP | `docker push` 필수 |
| [`kind-deployment-only-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Local.yaml) | **Deployment (단독)** | `todo-backend:prod` | Backend Deployment (복제본 2개, 롤링 업데이트) | `kind load` 필수 |
| [`kind-deployment-only-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Docker.yaml) | **Deployment (단독)** | `ssucloud/...:todo-backend` | Backend Deployment (복제본 2개, 롤링 업데이트) | `docker push` 필수 |
| [`kind-pod-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Local.yaml) | **Pod (단일)** | `todo-backend:prod` | Secret, ConfigMap, PVC, MySQL(Pod/Svc), Backend Pod(단일), ClusterIP | `kind load` 필수 |
| [`kind-pod-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Docker.yaml) | **Pod (단일)** | `ssucloud/...:todo-backend` | Secret, ConfigMap, PVC, MySQL(Pod/Svc), Backend Pod(단일), ClusterIP | `docker push` 필수 |
| [`kind-replicaset-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Local.yaml) | **ReplicaSet** | `todo-backend:prod` | Backend ReplicaSet (복제본 2개 관리) | `kind load` 필수 |
| [`kind-replicaset-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Docker.yaml) | **ReplicaSet** | `ssucloud/...:todo-backend` | Backend ReplicaSet (복제본 2개 관리) | `docker push` 필수 |
| [`deployment-kind-all.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind-all.yaml) | **All-in-One** | `todo-backend:prod` | Secret, CM, PVC, MySQL Pod/Svc, Backend Deployment, NodePort Service 통합 | `kind load` 필수 |

### 6.2 서비스 및 네트워크 매니페스트
- [`kind-service-cip.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-cip.yaml): `ClusterIP` - 클러스터 내부 전용 통신 (`todo-backend-cip:80` $\rightarrow$ 3000)
- [`kind-service-np.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-np.yaml): `NodePort` - 모든 노드의 `30080` 포트 개방
- [`kind-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-lb.yaml): `LoadBalancer` - `cloud-provider-kind`를 통한 외부 IP(`172.19.0.x`) 부여
- [`kind-ingress.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-ingress.yaml): `Ingress` - NGINX Controller 기반 L7 도메인/경로 라우팅 (Host: `localhost`, `www.ssu-cloud-computing.com`)
- [`kind-storageclass.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-storageclass.yaml): `StorageClass (fast)` - `rancher.io/local-path` 프로비저너 사용자 정의

---

## 7. 워크로드 아키텍처: Deployment vs Pod 분리 설계 이유

올인원 매니페스트([`kind-deployment-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Local.yaml))에서 두 워크로드는 다음과 같이 서로 다른 리소스 타입으로 설계되었습니다:

### 7.1 Backend $\rightarrow$ `Deployment` (무상태, Stateless)
- **무상태(Stateless)**: 백엔드는 자체 디스크에 상태를 남기지 않고 모든 트랜잭션을 MySQL에 위임합니다.
- **수평 확장(Scale-Out)**: 트래픽에 맞춰 `replicas: 2`로 손쉽게 증설하여 워커 노드(`worker`, `worker2`)에 분산 배치합니다.
- **무중단 롤링 업데이트**: 코드 수정 시 중단 없이 순차 교체(`RollingUpdate`)가 가능합니다.

### 7.2 MySQL $\rightarrow$ 단일 `Pod` 및 `ClusterIP` (상태 유지, Stateful)
- **단일 영구 볼륨(`ReadWriteOnce`) 충돌 방지**: MySQL은 로컬 디스크(`todo-mysql-pvc`, 1Gi)를 사용합니다. 여러 파드가 동시에 쓰면 데이터 파일 손상(Corruption)이 발생하므로 단일 Pod로 격리합니다.
- **고정 DNS 엔드포인트 제공**: 파드 IP가 재기동 시 변경되더라도 `mysql:3306` 고정 주소를 유지하기 위해 `ClusterIP` 서비스가 연결되어 있습니다.

---

## 8. 서비스 노출 및 외부 접속 실습 (5가지 방식)

Kind 클러스터에서 파드를 외부에 노출하고 접근하는 5가지 실습 방식입니다.

### 8.1 [방법 1] ClusterIP: 내부 통신 전용 (`kind-service-cip.yaml`)
- **특징**: 클러스터 내부 전용 가상 IP. 외부에서는 직접 접속할 수 없으며 내부 통신이나 Ingress의 백엔드로 활용됩니다.
- **배포**:
  ```powershell
  kubectl apply -f ./kind-service-cip.yaml
  ```

### 8.2 [방법 2] NodePort: 노드 포트 개방 (`kind-service-np.yaml`)
- **특징**: 모든 노드의 `30080` 포트를 개방합니다.
- **배포 및 확인**:
  ```powershell
  kubectl apply -f ./kind-service-np.yaml
  kubectl get svc todo-backend-np
  ```
- **접근 방법**:
  - 노드의 내부 IP(`kubectl get nodes -o wide`의 INTERNAL-IP, 예: `172.18.0.3:30080`)로 직접 접근하거나,
  - 호스트 PC에서 편리하게 확인하려면 `kubectl port-forward`를 연계합니다:
    ```powershell
    kubectl port-forward svc/todo-backend-np 8080:80
    ```
    이후 브라우저에서 `http://localhost:8080`으로 접속합니다.

### 8.3 [방법 3] LoadBalancer 및 `cloud-provider-kind.exe` (`kind-service-lb.yaml`)
로컬 Kind 환경에서 실제 클라우드(GKE, AWS)와 동일한 `type: LoadBalancer` 서비스를 구동하는 표준 실습입니다.

1. **매니페스트 배포**:
   ```powershell
   kubectl apply -f ./kind-service-lb.yaml
   ```
2. **`cloud-provider-kind.exe` 실행 (필수)**:
   기본 상태에서는 `EXTERNAL-IP`가 `<pending>` 상태로 머뭅니다. 프로젝트 루트에서 **별도의 관리자 권한 PowerShell 창**을 열고 실행합니다:
   ```powershell
   .\cloud-provider-kind.exe
   ```
3. **가상 공인 IP 할당 확인**:
   ```powershell
   kubectl get svc todo-backend-lb
   ```
   *출력 예시*:
   ```text
   NAME              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
   todo-backend-lb   LoadBalancer   10.96.162.154   172.19.0.5    80:31002/TCP
   ```
4. **외부 브라우저 접속**:
   할당된 가상 IP로 직접 접속합니다:
   - 웹 접속: `http://172.19.0.5`
   - REST API: `http://172.19.0.5/api/items`

### 8.4 [방법 4] L7 Ingress 및 NGINX Controller 연동 (`kind-ingress.yaml`)
호스트 PC의 80/443 포트 매핑을 활용하여 단일 진입점에서 도메인 및 경로 기반으로 트래픽을 라우팅하는 실무 표준 방식입니다.

1. **Kind 공식 NGINX Ingress Controller 설치**:
   ```powershell
   kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
   
   # 컨트롤러가 Ready 상태가 될 때까지 대기
   kubectl wait --namespace ingress-nginx `
     --for=condition=ready pod `
     --selector=app.kubernetes.io/component=controller `
     --timeout=90s
   ```
2. **백엔드 서비스 및 Ingress 매니페스트 적용**:
   [`kind-ingress.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-ingress.yaml)은 백엔드로 `todo-backend-cip:80`을 연결하므로 서비스가 먼저 배포되어 있어야 합니다:
   ```powershell
   kubectl apply -f ./kind-service-cip.yaml
   kubectl apply -f ./kind-ingress.yaml
   ```
3. **Ingress 확인 및 호스트 접속 테스트**:
   ```powershell
   kubectl get ingress todo-backend-ingress
   ```
   - **브라우저 기본 접속**: [http://localhost](http://localhost)
   - **호스트 헤더 테스트**:
     ```powershell
     curl.exe -H "Host: www.ssu-cloud-computing.com" http://localhost/
     ```

### 8.5 [방법 5] 디버깅 도구: `kubectl port-forward` vs `kubectl proxy`

| 비교 항목 | `kubectl port-forward` (권장 디버깅 도구) | `kubectl proxy` |
| :--- | :--- | :--- |
| **연결 대상** | 특정 파드(Pod) 또는 서비스(Service) | 쿠버네티스 API 마스터 서버 (`kube-apiserver`) |
| **작동 원리** | L4 TCP 포트 터널링 | L7 HTTP 보안 리버스 프록시 |
| **접속 주소** | `http://localhost:<지정포트>` | `http://localhost:8001/api/v1/.../proxy/` |
| **정적 자원 서빙**| HTML, CSS, JS 파일이 원본 포트와 1:1 매핑되어 완벽 서빙 | 서브패스(`/proxy/`)로 인해 상대경로 자원이 깨질 수 있음 |
| **주요 사용처** | **웹 UI 검증, 백엔드 API 테스트, MySQL DB(3306) 직결** | 쿠버네티스 REST API 원시 데이터 확인, 대시보드 접근 |

- **`kubectl port-forward` 실행 예시**:
  ```powershell
  # 백엔드 Deployment 3000 포트를 로컬 8080으로 포워딩
  kubectl port-forward deployment/todo-backend 8080:3000
  ```

---

## 9. 단계별 원클릭 실행 시나리오 (PowerShell)

### 시나리오 A: 로컬 이미지 기반 빠른 실습 (`Local.yaml`)
```powershell
# 1. Kind 클러스터 생성
kind create cluster --name my-k8s --config ./kind-config-2workers.yaml

# 2. 로컬 이미지 빌드 및 Kind 노드로 주입
docker build -t todo-backend:prod .
kind load docker-image todo-backend:prod --name my-k8s

# 3. 올인원 풀스택 배포
kubectl apply -f ./kind-deployment-Local.yaml

# 4. LoadBalancer 서비스 배포
kubectl apply -f ./kind-service-lb.yaml

# 5. 별도 터미널에서 로드밸런서 구동
# .\cloud-provider-kind.exe

# 6. 배포 상태 모니터링
kubectl rollout status deployment/todo-backend
kubectl get pods,svc -o wide
```

### 시나리오 B: Docker Hub 기반 Ingress 연동 실습 (`Docker.yaml` + Ingress)
```powershell
# 1. Docker Hub로 이미지 빌드 및 푸시
docker build -t todo-backend:prod .
docker tag todo-backend:prod ssucloud/getting-started-todo-app:todo-backend
docker push ssucloud/getting-started-todo-app:todo-backend

# 2. Deployment 및 내부 ClusterIP 배포
kubectl apply -f ./kind-deployment-Docker.yaml

# 3. Ingress Controller 설치 및 Ingress 규칙 적용
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s
kubectl apply -f ./kind-ingress.yaml

# 4. 브라우저에서 http://localhost 접속 확인
```

---

## 10. 핵심 트러블슈팅 가이드

| 오류 현상 | 주요 원인 | 해결 방법 |
| :--- | :--- | :--- |
| **`ErrImagePull`** / **`ImagePullBackOff`** (`Local.yaml`) | 로컬 빌드 이미지를 Kind 노드에 적재하지 않음 | `kind load docker-image todo-backend:prod --name my-k8s` 실행 |
| **`ErrImagePull`** / **`manifest unknown`** (`Docker.yaml`) | Docker Hub에 이미지를 태깅 및 푸시하지 않음 | `docker push ssucloud/getting-started-todo-app:todo-backend` 실행 |
| **MySQL `Pending` 및 백엔드 `Init:0/1` 무한 대기** | Kind에 존재하지 않는 GKE 전용 `storageClassName: standard-rwo` 사용 | Kind 기본 `storageClassName: standard` 및 `1Gi` 적용 확인 |
| **LoadBalancer `EXTERNAL-IP`가 `<pending>` 지속** | 로컬 클라우드 프로바이더 미실행 | 별도 관리자 권한 터미널에서 `.\cloud-provider-kind.exe` 실행 유지 |
| **브라우저 `localhost` 접속 시 `ERR_EMPTY_RESPONSE`** | 80 포트는 열려 있으나 Ingress Controller나 백엔드 파드가 미구동됨 | Ingress Controller 파드 상태 및 `todo-backend` 파드 `Running` 상태 확인 |
| **`connectex: target machine actively refused it`** | Kind 클러스터가 생성되지 않았거나 Docker Desktop이 중지됨 | Docker Desktop 실행 후 `kind create cluster` 수행 |

---

## 11. Kind 로컬 환경 vs GKE 클라우드 환경 비교

| 비교 항목 | Kind (Kubernetes in Docker) | GKE (Google Kubernetes Engine) |
| :--- | :--- | :--- |
| **실행 인프라** | 로컬 PC (Docker 컨테이너 가상 노드) | Google Cloud 완전관리형 Compute Engine VM |
| **비용** | 완전 무료 (로컬 자원 소비) | GCP 노드 및 인프라 비용 발생 |
| **노드 구성** | 1 Control-Plane + 2 Workers | Control-Plane (GCP 관리) + 2 Workers (`--num-nodes=2`) |
| **이미지 공급처** | 로컬 캐시 주입(`kind load`) 또는 Docker Hub | GCP 비공개 **Artifact Registry** (`*.pkg.dev`) |
| **기본 스토리지** | `standard` (`rancher.io/local-path`, 1Gi) | `standard-rwo` (GCP Persistent Disk CSI, 10Gi) |
| **LoadBalancer** | [`cloud-provider-kind.exe`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/cloud-provider-kind.exe) 에뮬레이션 | GCP Network Load Balancer 자동 프로비저닝 (공인 IP) |
| **L7 Ingress** | NGINX Ingress Controller 설치 (`ingress-ready`) | GCP HTTP(S) Load Balancer 자동 연동 (`gce` Ingress) |
| **주요 목적** | 로컬 개발, 신속한 YAML 문법 검증, 비용 없는 실습 | 실무 운영 환경, 글로벌 고가용성 서비스 배포 |

---

## 12. 프로젝트 연관 파일 링크

### 1) 클러스터 및 스토리지 설정
- [`kind-config-2workers.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-config-2workers.yaml): Control-Plane 1대 + Worker 2대 포트 매핑(80/443) 클러스터 설정
- [`kind-storageclass.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-storageclass.yaml): 사용자 정의 스토리지 클래스 (`fast`)

### 2) 워크로드 매니페스트 (`Workloads`)
- [`kind-deployment-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Local.yaml): 로컬 이미지 기반 전체 풀스택 올인원 배포 매니페스트
- [`kind-deployment-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-Docker.yaml): Docker Hub 이미지 기반 전체 풀스택 올인원 배포 매니페스트
- [`kind-deployment-only-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Local.yaml): 로컬 이미지 Backend Deployment 단독 배포 매니페스트
- [`kind-deployment-only-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-deployment-only-Docker.yaml): Docker Hub 이미지 Backend Deployment 단독 배포 매니페스트
- [`kind-pod-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Local.yaml): 로컬 이미지 기반 Pod 단위 배포 매니페스트
- [`kind-pod-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-pod-Docker.yaml): Docker Hub 이미지 기반 Pod 단위 배포 매니페스트
- [`kind-replicaset-Local.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Local.yaml): 로컬 이미지 Backend ReplicaSet 배포 매니페스트
- [`kind-replicaset-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-replicaset-Docker.yaml): Docker Hub 이미지 Backend ReplicaSet 배포 매니페스트
- [`deployment-kind-all.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind-all.yaml): 백엔드 Deployment와 NodePort 서비스를 통합한 올인원 매니페스트

### 3) 서비스 및 Ingress 매니페스트 (`Services & Ingress`)
- [`kind-service-cip.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-cip.yaml): ClusterIP 서비스 매니페스트
- [`kind-service-np.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-np.yaml): NodePort 서비스 매니페스트 (30080 포트)
- [`kind-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-lb.yaml): LoadBalancer 서비스 매니페스트
- [`kind-ingress.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-ingress.yaml): NGINX Ingress Controller 연동 L7 라우팅 규칙 매니페스트

### 4) 관련 가이드 및 실행 파일
- [`cloud-provider-kind.exe`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/cloud-provider-kind.exe): 로컬 Kind LoadBalancer IP 할당용 실행 파일
- [`GKE-Workflow.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-Workflow.md): GCP GKE 및 Artifact Registry 연동 가이드
- [`Kubernetes-Workflow.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/Kubernetes-Workflow.md): 쿠버네티스 핵심 개념 및 기본 워크플로우 가이드
