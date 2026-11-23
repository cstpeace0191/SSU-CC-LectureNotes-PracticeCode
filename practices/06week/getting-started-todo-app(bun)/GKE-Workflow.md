# GKE & GCP Artifact Registry 연동 워크플로우 가이드

본 문서는 Google Cloud Platform(GCP) 환경에서 **GKE(Google Kubernetes Engine) 멀티 노드 클러스터(`my-gke-cluster`)를 생성**하고, **Artifact Registry 저장소 구축**, **로컬 컨테이너 이미지 빌드/태깅/푸시**, 그리고 **`kubectl` 연동 및 프로젝트 매니페스트(`GKE-*.yaml`) 배포부터 LoadBalancer/Ingress 노출**까지의 엔드투엔드(End-to-End) 워크플로우를 프로젝트 파일들과 일치하도록 검증·정리한 실무 가이드입니다.

---

## 📋 목차 (Table of Contents)
1. [환경 및 리소스 정보 요약](#1-환경-및-리소스-정보-요약)
2. [사전 준비: gcloud CLI 및 인증 플러그인 설정](#2-사전-준비-gcloud-cli-및-인증-플러그인-설정)
3. [GKE Kubernetes Cluster 생성 및 관리 (`my-gke-cluster`)](#3-gke-kubernetes-cluster-생성-및-관리-my-gke-cluster)
4. [kubectl 컨텍스트 연동 및 클러스터 전환](#4-kubectl-컨텍스트-연동-및-클러스터-전환)
5. [GCP Artifact Registry 저장소 생성 및 Docker 인증](#5-gcp-artifact-registry-저장소-생성-및-docker-인증)
6. [컨테이너 이미지 빌드, 태깅 및 푸시 파이프라인](#6-컨테이너-이미지-빌드-태깅-및-푸시-파이프라인)
7. [프로젝트 `GKE-*.yaml` 매니페스트 체계 총정리](#7-프로젝트-gke-yaml-매니페스트-체계-총정리)
8. [GKE 워크로드 배포 실습 (올인원 vs 컴포넌트별 배포)](#8-gke-워크로드-배포-실습-올인원-vs-컴포넌트별-배포)
9. [아키텍처 분석: Deployment vs Pod 분리 설계 이유](#9-아키텍처-분석-deployment-vs-pod-분리-설계-이유)
10. [GKE 서비스 및 Ingress 외부 노출 실습](#10-gke-서비스-및-ingress-외부-노출-실습)
    - 10.1 [방법 1] LoadBalancer: GCP Network Load Balancer 공인 IP 연동 (`GKE-service-lb.yaml`)
    - 10.2 [방법 2] NodePort: 워커 노드 포트 개방 (`GKE-service-np.yaml`)
    - 10.3 [방법 3] ClusterIP 및 내부 통신 (`GKE-service-cip.yaml`)
    - 10.4 [방법 4] GCE Ingress: L7 글로벌 부하분산기 연동 (`GKE-ingress.yaml`)
    - 10.5 [방법 5] 디버깅 도구: `kubectl port-forward` vs `kubectl proxy`
11. [Windows PowerShell 원클릭 완전 자동화 스크립트](#11-windows-powershell-원클릭-완전-자동화-스크립트)
12. [GKE 핵심 트러블슈팅 가이드](#12-gke-핵심-트러블슈팅-가이드)
13. [프로젝트 연관 파일 링크](#13-프로젝트-연관-파일-링크)

---

## 1. 환경 및 리소스 정보 요약

| 항목 | 설정값 (예시 / 기본값) | 비고 / 설명 |
| :--- | :--- | :--- |
| **GCP Account** | 사용자 GCP 계정 (예: `ssu.cloud.agent@gmail.com`) | 작업 대상 Google Cloud 사용자 계정 |
| **GCP Project ID** | `ssu-agent-vertex-509708` | GCP 활성 프로젝트 ID |
| **GKE Cluster Name** | `my-gke-cluster` | GKE 표준 쿠버네티스 클러스터명 |
| **Location / Region** | `asia-northeast3` (서울 리전) | 컨트롤 플레인 및 리소스 기본 리전 |
| **Compute Zone** | `asia-northeast3-a` | 단일 존(Zone) 클러스터 배치 영역 |
| **Worker Node 수** | 2대 (`--num-nodes=2`) | 실습용 고가용성 워커 노드 대수 |
| **Machine Type** | `e2-medium` (2 vCPU, 4GB RAM) | 실습 비용 최적화 머신 사양 |
| **Artifact Registry**| `my-repo` | Docker 포맷 비공개 컨테이너 저장소 |
| **Registry Host** | `asia-northeast3-docker.pkg.dev` | 서울 리전 전용 Docker 엔드포인트 |
| **Source Image** | `todo-backend:prod` | 로컬 Docker 환경에서 빌드된 소스 이미지 |
| **Target Image URI** | `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod` | Artifact Registry 원격 이미지 정규 URI |
| **Remote Docker Image**| `ssucloud/getting-started-todo-app:todo-backend` | Docker Hub 공인 이미지 (대체용) |
| **StorageClass** | `standard-rwo` (기본, `pd-balanced`, 10Gi) | GCP Persistent Disk CSI 드라이버 자동 연동 |
| **Custom StorageClass**| `fast` ([`GCP-storageclass.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GCP-storageclass.yaml)) | `pd.csi.storage.gke.io` / `pd-balanced` 프로비저너 |

---

## 2. 사전 준비: gcloud CLI 및 인증 플러그인 설정

### 2.1 계정 로그인 및 기본 환경 구성
```bash
# 1. 지정된 GCP 계정으로 로그인 (웹 브라우저 인증)
gcloud auth login ssu.cloud.agent@gmail.com

# 2. 작업 대상 프로젝트 설정
gcloud config set project ssu-agent-vertex-509708

# 3. 기본 영역(Zone)을 asia-northeast3-a로 설정
gcloud config set compute/zone asia-northeast3-a

# 4. 필수 GCP API 활성화 (GKE & Artifact Registry)
gcloud services enable container.googleapis.com artifactregistry.googleapis.com

# 5. 설정 결과 확인
gcloud config list
```

### 2.2 GKE 인증 플러그인 설치 (`gke-gcloud-auth-plugin`)
Kubernetes v1.26 이상부터 GKE 클러스터 제어를 위해 필수적인 보안 인증 플러그인입니다:
```bash
# 플러그인 설치
gcloud components install gke-gcloud-auth-plugin

# 설치 버전 확인
gke-gcloud-auth-plugin --version
```

---

## 3. GKE Kubernetes Cluster 생성 및 관리 (`my-gke-cluster`)

### 3.1 GKE 클러스터 생성 (워커 노드 2대)
실습 요구조건(워커 노드 2대, Zone `asia-northeast3-a`, 머신 타입 `e2-medium`, VPC 네이티브)에 맞춰 클러스터를 생성합니다:

```bash
gcloud container clusters create my-gke-cluster \
    --project=ssu-agent-vertex-509708 \
    --zone=asia-northeast3-a \
    --num-nodes=2 \
    --machine-type=e2-medium \
    --disk-size=50GB \
    --enable-ip-alias \
    --release-channel=regular
```

### 3.2 클러스터 상태 확인
```bash
# 클러스터 목록 및 상태(STATUS: RUNNING) 확인
gcloud container clusters list

# 클러스터 상세 정보 확인
gcloud container clusters describe my-gke-cluster --zone=asia-northeast3-a
```

### 3.3 [실습 종료 후] 클러스터 삭제 (비용 방지)
실습 완료 후 노드 인스턴스 과금을 방지하기 위해 클러스터를 삭제합니다:
```bash
gcloud container clusters delete my-gke-cluster --zone=asia-northeast3-a --quiet
```

---

## 4. kubectl 컨텍스트 연동 및 클러스터 전환

### 4.1 GKE 인증 정보 갱신 (`get-credentials`)
클러스터 생성 후 로컬 `~/.kube/config`에 GKE 엔드포인트와 인증 토큰을 등록합니다:

```bash
gcloud container clusters get-credentials my-gke-cluster \
    --zone=asia-northeast3-a \
    --project=ssu-agent-vertex-509708
```

### 4.2 컨텍스트 조회 및 스위칭
로컬 Kind 클러스터와 GKE 클러스터 간의 작업 대상을 자유롭게 전환합니다:

```bash
# 1. 전체 컨텍스트 목록 조회 (*가 현재 활성 클러스터)
kubectl config get-contexts

# 2. 현재 활성 컨텍스트 확인
kubectl config current-context

# 3. 긴 GKE 컨텍스트명을 짧은 별칭 'gke'로 변경 (선택 사항)
kubectl config rename-context gke_ssu-agent-vertex-509708_asia-northeast3-a_my-gke-cluster gke
kubectl config use-context gke

# 4. 필요 시 로컬 Kind 클러스터로 복귀
kubectl config use-context kind-my-k8s

# 5. GKE 노드 상태 확인 (2대 Ready 확인)
kubectl get nodes -o wide
```

---

## 5. GCP Artifact Registry 저장소 생성 및 Docker 인증

### 5.1 Docker 포맷 저장소(`my-repo`) 생성
서울 리전(`asia-northeast3`)에 비공개 컨테이너 저장소를 생성합니다:

```bash
gcloud artifacts repositories create my-repo \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="Todo backend container image repository"

# 생성 확인
gcloud artifacts repositories list --location=asia-northeast3
```

### 5.2 Docker CLI 인증 헬퍼 등록 (`gcloud configure-docker`)
로컬 Docker 데몬이 GCP Artifact Registry에 로그인 없이 안전하게 푸시할 수 있도록 인증 헬퍼를 설정합니다:

```bash
gcloud auth configure-docker asia-northeast3-docker.pkg.dev --quiet
```

---

## 6. 컨테이너 이미지 빌드, 태깅 및 푸시 파이프라인

로컬 소스 코드를 빌드하고, Artifact Registry 원격 저장소 규격에 맞춰 태깅한 후 푸시합니다.

```powershell
# 1. 로컬 프로덕션 이미지 빌드
docker build -t todo-backend:prod .

# 2. Artifact Registry 경로로 태깅
docker tag todo-backend:prod asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod

# 3. 원격 저장소로 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod

# 4. 업로드된 이미지 확인
gcloud artifacts docker images list asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo
```

---

## 7. 프로젝트 `GKE-*.yaml` 매니페스트 체계 총정리

워크스페이스 내 `GKE-*.yaml` 파일들은 **워크로드 컨트롤러 계층(Pod $\rightarrow$ ReplicaSet $\rightarrow$ Deployment)** 및 **이미지 공급처(GCP Artifact Registry vs Docker Hub)**에 따라 체계적으로 준비되어 있습니다.

### 7.1 워크로드 및 서비스 매니페스트 비교표

| 파일명 | 리소스 타입 | 이미지 공급처 | 포함된 리소스 구성 | 주요 용도 및 특징 |
| :--- | :--- | :--- | :--- | :--- |
| **[`GKE-deployment-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-GCP.yaml)** | **Deployment (올인원)** | **GCP Artifact Registry** | Secret, CM, PVC, MySQL Pod/Svc, Backend Deployment(2개) | **[실무 프로덕션 표준]** 프라이빗 이미지 기반 무중단 롤링 배포 |
| **[`GKE-deployment-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-Docker.yaml)** | **Deployment (올인원)** | Docker Hub | Secret, CM, PVC, MySQL Pod/Svc, Backend Deployment(2개) | Docker Hub 공용 이미지 기반 롤링 배포 검증용 |
| **[`GKE-deployment-only-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-only-GCP.yaml)** | **Deployment (단독)** | **GCP Artifact Registry** | Backend Deployment (복제본 2개, 롤링 업데이트) | 백엔드 디플로이먼트만 단독 갱신할 때 사용 |
| **[`GKE-deployment-only-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-only-Docker.yaml)** | **Deployment (단독)** | Docker Hub | Backend Deployment (복제본 2개, 롤링 업데이트) | 백엔드 디플로이먼트만 단독 갱신할 때 사용 |
| **[`GKE-pod-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-GCP.yaml)** | **Pod (단일)** | **GCP Artifact Registry** | Secret, CM, PVC, MySQL Pod/Svc, Backend Pod(단일) | GCP 스토리지(10Gi) 및 Artifact Registry 이미지 기반 단일 파드 초기 검증용 |
| **[`GKE-pod-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-Docker.yaml)** | **Pod (단일)** | Docker Hub | Secret, CM, PVC, MySQL Pod/Svc, Backend Pod(단일) | Docker Hub 이미지 기반 단일 파드 최초 검증용 |
| **[`GKE-replicaset-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-replicaset-GCP.yaml)** | **ReplicaSet** | **GCP Artifact Registry** | Backend ReplicaSet (복제본 2개 유지) | 레플리카셋 복제본 및 `matchLabels` 검증용 |
| **[`GKE-replicaset-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-replicaset-Docker.yaml)** | **ReplicaSet** | Docker Hub | Backend ReplicaSet (복제본 2개 유지) | 레플리카셋 복제본 및 `matchLabels` 검증용 |
| **[`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-lb.yaml)** | **LoadBalancer** | - | GCP Network Load Balancer 연동 (외부 공인 IP 자동 할당) | **[실무 표준]** 고정 공인 IP를 통한 대외 서비스 공개 |
| **[`GKE-service-np.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-np.yaml)** | **NodePort** | - | 모든 워커 노드의 `30080` 포트 직접 개방 | 로드밸런서 비용 없이 노드 외부 IP로 접속 테스트 |
| **[`GKE-service-cip.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-cip.yaml)** | **ClusterIP** | - | 내부 전용 가상 IP 포트 80 $\rightarrow$ 3000 | 내부 통신 전용 및 `kubectl port-forward` 터널링 검증용 |
| **[`GKE-ingress.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-ingress.yaml)** | **Ingress (GCE)** | - | Google Cloud HTTP(S) L7 부하분산기 연동 (`kubernetes.io/ingress.class: "gce"`) | L7 도메인 기반 스마트 라우팅 |
| **[`GCP-storageclass.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GCP-storageclass.yaml)** | **StorageClass (fast)** | - | GCP CSI 드라이버 (`pd-balanced`, `WaitForFirstConsumer`) | 사용자 정의 고속 스토리지 클래스 |

---

### 7.2 이미지 공급 방식 비교: `GKE-*-GCP.yaml` vs `GKE-*-Docker.yaml`

| 비교 항목 | `GKE-*-GCP.yaml` (실무 프로덕션 표준) | `GKE-*-Docker.yaml` (학습/테스트용) |
| :--- | :--- | :--- |
| **이미지 레지스트리** | **GCP Artifact Registry (Private)**<br>`asia-northeast3-docker.pkg.dev/.../todo-backend:prod` | **Docker Hub (Public)**<br>`ssucloud/getting-started-todo-app:todo-backend` |
| **보안 및 인증** | **GCP IAM 기반 비공개 보안 격리**<br>GKE 노드가 클라우드 내부 서비스 계정으로 자동 인증 | **완전 공개(Public)**<br>인증 없이 누구나 이미지 다운로드 가능 |
| **네트워크 경로** | **Google Cloud 내부 백본 네트워크** 경유 (초고속 전송) | 공용 인터넷 경유 (다운로드 횟수 제한 및 지연 가능) |
| **워크플로우 위치** | 코드 수정 $\rightarrow$ 도커 빌드 $\rightarrow$ Artifact Registry 푸시 $\rightarrow$ 배포 | 사전 빌드된 공용 이미지를 사용하여 즉시 배포 검증 |

> [!NOTE]
> **진위 판정 및 교정**:
> [`GKE-pod-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-GCP.yaml)은 162 라인에 명시된 대로 **GCP Artifact Registry 프라이빗 이미지**(`asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod`)를 사용합니다. Docker Hub 이미지를 참조하는 매니페스트는 [`GKE-pod-Docker.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-Docker.yaml)입니다.

---

## 8. GKE 워크로드 배포 실습 (올인원 vs 컴포넌트별 배포)

### 8.1 [방법 A] 프로덕션 올인원 일괄 배포 ([`GKE-deployment-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-GCP.yaml))
Secret, ConfigMap, PVC, MySQL Pod/Service, Backend Deployment(2개)를 한 번에 일괄 배포하는 가장 권장되는 실무 표준 방식입니다:

```bash
# 전체 스택 일괄 배포
kubectl apply -f GKE-deployment-GCP.yaml

# 배포 롤아웃 상태 모니터링
kubectl rollout status deployment/todo-backend

# 파드 및 서비스 구동 상태 확인
kubectl get pods,svc,pvc -o wide
```

### 8.2 [방법 B] 컴포넌트별 단계적 배포
기존 MySQL DB 인프라가 이미 구동 중인 상태에서 백엔드 디플로이먼트만 독립적으로 배포하거나 교체할 때 사용합니다:

```bash
# 백엔드 Deployment 단독 배포
kubectl apply -f GKE-deployment-only-GCP.yaml
```

---

## 9. 아키텍처 분석: Deployment vs Pod 분리 설계 이유

[`GKE-deployment-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-GCP.yaml)에서 **`todo-backend`는 Deployment**로, **`mysql`은 단일 Pod 및 ClusterIP 서비스**로 구성한 이유입니다:

### 9.1 `todo-backend` $\rightarrow$ `Deployment` (무상태, Stateless)
- **무상태 워크로드**: 데이터를 컨테이너 내부에 영구 저장하지 않고 MySQL에 위임하므로 여러 파드를 자유롭게 띄울 수 있습니다.
- **수평 확장 및 자가 치유**: `replicas: 2`로 구성하여 워커 노드 2대에 각각 분산 배치하고 파드 장애 시 자동 재생성됩니다.
- **무중단 롤링 업데이트**: 새 버전 이미지 배포 시 서비스 중단 없이 순차 교체(`RollingUpdate: maxSurge=1, maxUnavailable=0`)됩니다.

### 9.2 `mysql` $\rightarrow$ 단일 `Pod` 및 `ClusterIP` (상태 유지, Stateful)
- **RWO 볼륨 충돌 원천 방지**: MySQL 데이터 디스크(PVC: `todo-mysql-pvc`, 10Gi)는 **`ReadWriteOnce(RWO)`** 속성으로 오직 1개의 노드/파드만 마운트할 수 있습니다. 만약 Deployment로 배포하여 파드가 2개 이상 뜨거나 롤링 교체가 발생하면 `Multi-Attach error` 또는 데이터 파일 손상이 발생합니다.
- **고정 DNS 통신 보장**: MySQL 파드가 재시작되어 내부 IP가 변경되더라도, 백엔드 파드가 항상 고정된 주소(`mysql:3306`)로 통신할 수 있도록 **`ClusterIP` 서비스**가 엔드포인트를 중계합니다.

---

## 10. GKE 서비스 및 Ingress 외부 노출 실습

[`GKE-deployment-GCP.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-GCP.yaml)에는 애플리케이션 파드와 DB만 포함되어 있으므로, 외부 트래픽을 유입시키기 위해 아래 서비스 또는 Ingress 매니페스트를 추가로 배포해야 합니다.

### 10.1 [방법 1] LoadBalancer: GCP Network Load Balancer 공인 IP 연동 ([`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-lb.yaml))
GKE 프로덕션 환경에서 가장 널리 사용되는 대외 서비스 공개 표준입니다.

```bash
# 1. LoadBalancer 서비스 배포
kubectl apply -f GKE-service-lb.yaml

# 2. 외부 공인 IP(EXTERNAL-IP) 할당 모니터링
kubectl get svc todo-backend-lb -w
```

- **출력 변화**: 배포 초기 약 30~50초간 `<pending>` 상태를 거친 뒤 실제 GCP 외부 공인 IP(예: `34.64.232.11`)가 자동 할당됩니다.
- **웹 브라우저 접속**: `http://<EXTERNAL-IP>` (예: `http://34.64.232.11`)
- **API 엔드포인트**: `http://<EXTERNAL-IP>/api/items`

---

### 10.2 [방법 2] NodePort: 워커 노드 포트 개방 ([`GKE-service-np.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-np.yaml))
클라우드 로드밸런서 과금 없이 모든 워커 노드의 `30080` 포트를 직접 외부에 개방하여 테스트하는 방식입니다.

```bash
# 1. NodePort 서비스 배포
kubectl apply -f GKE-service-np.yaml

# 2. 워커 노드의 외부 공인 IP 확인
kubectl get nodes -o wide
# 예: 34.22.93.43, 34.22.76.251

# 3. GCP VPC 방화벽 규칙 개방 (필수)
gcloud compute firewall-rules create allow-gke-nodeport-30080 --allow tcp:30080

# 4. 브라우저 접속: http://<노드_외부IP>:30080
```

---

### 10.3 [방법 3] ClusterIP 및 내부 통신 ([`GKE-service-cip.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-cip.yaml))
외부에 노출하지 않고 클러스터 내부에서만 접근 가능한 가상 IP(`todo-backend-cip:80`)를 제공합니다. 개발 PC에서 테스트할 때는 `port-forward`를 사용합니다:

```bash
kubectl apply -f GKE-service-cip.yaml
kubectl port-forward svc/todo-backend-cip 8080:80
```
- 브라우저 접속: `http://localhost:8080`

---

### 10.4 [방법 4] GCE Ingress: L7 글로벌 부하분산기 연동 ([`GKE-ingress.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-ingress.yaml))
Google Cloud의 완전관리형 HTTP(S) L7 부하분산기를 프로비저닝하여 지정된 도메인(`www.ssu-cloud-computing.com`)으로 들어오는 트래픽을 백엔드 서비스([`GKE-service-lb.yaml`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-lb.yaml))로 라우팅합니다.

```yaml
# GKE-ingress.yaml 내용
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: todo-backend-ingress
  annotations:
    kubernetes.io/ingress.class: "gce"
spec:
  rules:
  - host: www.ssu-cloud-computing.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: todo-backend-lb
            port:
              number: 80
```

- **배포 및 검증**:
  ```bash
  # 1. 백엔드 서비스(todo-backend-lb) 배포 확인 후 Ingress 적용
  kubectl apply -f GKE-ingress.yaml

  # 2. GCE Ingress IP 프로비저닝 확인 (약 2~5분 소요)
  kubectl get ingress todo-backend-ingress -w

  # 3. 도메인 호스트 헤더 요청 테스트
  curl -H "Host: www.ssu-cloud-computing.com" http://<INGRESS-ADDRESS>/
  ```

---

### 10.5 [방법 5] 디버깅 도구: `kubectl port-forward` vs `kubectl proxy`

| 비교 항목 | `kubectl port-forward` (권장 디버깅 도구) | `kubectl proxy` |
| :--- | :--- | :--- |
| **연결 대상** | 특정 파드(Pod) 또는 서비스(Service) | GKE 마스터 API 서버 (`kube-apiserver`) |
| **인증 방식** | 초기 TCP 터널 수립 후 순수 L4 패킷 전달 | GCP IAM 및 kubeconfig 인증을 프록시가 대리 주입 |
| **접속 주소** | `http://localhost:<로컬포트>` (예: `8080`) | `http://localhost:8001/api/v1/.../proxy/` |
| **정적 웹 서빙**| CSS/JS 상대 경로 문제없이 완벽 서빙 | 서브패스(`/proxy/`)로 인해 웹 앱 UI 깨짐 현상 발생 가능 |
| **주요 사용처** | **웹 UI 브라우저 검증, MySQL DB(3306) 직접 접속** | 쿠버네티스 REST API 원시 데이터 조회, 관리 스크립트 |

---

## 11. Windows PowerShell 원클릭 완전 자동화 스크립트

클러스터 생성, Artifact Registry 설정, 이미지 빌드/푸시, 매니페스트 배포까지 한 번에 수행하는 통합 자동화 스크립트입니다:

```powershell
# ==========================================
# GKE & Artifact Registry 설정 변수
# ==========================================
$ACCOUNT      = "ssu.cloud.agent@gmail.com"
$PROJECT_ID   = "ssu-agent-vertex-509708"
$ZONE         = "asia-northeast3-a"
$LOCATION     = "asia-northeast3"
$CLUSTER_NAME = "my-gke-cluster"
$REPO_NAME    = "my-repo"
$LOCAL_IMG    = "todo-backend:prod"
$REGISTRY     = "$LOCATION-docker.pkg.dev"
$TARGET_IMG   = "$REGISTRY/$PROJECT_ID/$REPO_NAME/$LOCAL_IMG"

Write-Host ">>> [1/7] GCP 계정 및 프로젝트 환경 설정..." -ForegroundColor Cyan
gcloud config set account $ACCOUNT
gcloud config set project $PROJECT_ID
gcloud config set compute/zone $ZONE

Write-Host ">>> [2/7] 필수 GCP API 활성화..." -ForegroundColor Cyan
gcloud services enable container.googleapis.com artifactregistry.googleapis.com

Write-Host ">>> [3/7] GKE 클러스터 생성 ($CLUSTER_NAME, Worker Nodes: 2)..." -ForegroundColor Cyan
gcloud container clusters create $CLUSTER_NAME `
    --project=$PROJECT_ID `
    --zone=$ZONE `
    --num-nodes=2 `
    --machine-type=e2-medium `
    --disk-size=50GB `
    --enable-ip-alias `
    --release-channel=regular 2>$null

Write-Host ">>> [4/7] kubectl 인증 갱신 및 컨텍스트 전환..." -ForegroundColor Cyan
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE --project=$PROJECT_ID
kubectl get nodes -o wide

Write-Host ">>> [5/7] Artifact Registry 생성 및 Docker 인증 헬퍼 설정..." -ForegroundColor Cyan
gcloud artifacts repositories create $REPO_NAME `
    --repository-format=docker `
    --location=$LOCATION `
    --description="Todo backend container image repository" 2>$null
gcloud auth configure-docker $REGISTRY --quiet

Write-Host ">>> [6/7] 이미지 로컬 빌드, 태깅 및 Artifact Registry 푸시..." -ForegroundColor Cyan
docker build -t $LOCAL_IMG .
docker tag $LOCAL_IMG $TARGET_IMG
docker push $TARGET_IMG

Write-Host ">>> [7/7] 프로덕션 올인원 매니페스트 및 LoadBalancer 배포..." -ForegroundColor Green
kubectl apply -f GKE-deployment-GCP.yaml
kubectl apply -f GKE-service-lb.yaml

Write-Host ">>> 배포 완료! 외부 IP가 프로비저닝될 때까지 대기합니다..." -ForegroundColor Green
kubectl rollout status deployment/todo-backend
kubectl get svc todo-backend-lb -w
```

---

## 12. GKE 핵심 트러블슈팅 가이드

| 오류 현상 | 주요 원인 | 해결 방법 |
| :--- | :--- | :--- |
| **`ImagePullBackOff`** / **`denied: Permission "artifactregistry.repositories.downloadArtifacts" denied`** | GKE 노드 서비스 계정에 Artifact Registry 읽기 권한 없음 또는 레지스트리 경로 오타 | 클러스터가 동일 프로젝트에 있는지 확인하고 노드 기본 서비스 계정 권한 확인 |
| **`ImagePullBackOff`** / **`manifest unknown`** | 로컬에서 빌드만 하고 Artifact Registry에 `docker push`를 수행하지 않음 | `docker push asia-northeast3-docker.pkg.dev/.../todo-backend:prod` 실행 |
| **MySQL 파드 `Pending` 지속** | GKE 기본 CSI 스토리지 클래스(`standard-rwo`) 프로비저닝 지연 | `kubectl describe pvc todo-mysql-pvc`로 볼륨 이벤트 확인 |
| **LoadBalancer `EXTERNAL-IP`가 `<pending>` 지속** | GCP Network Load Balancer 생성 진행 중 (보통 30~50초 소요) | `kubectl get svc -w`로 대기하며 잠시 후 공인 IP 할당 확인 |
| **NodePort(`30080`) 접속 불가** | GCP VPC 네트워크 방화벽에서 30080 포트가 차단됨 | `gcloud compute firewall-rules create allow-gke-nodeport-30080 --allow tcp:30080` 실행 |
| **`kubectl` 명령 시 `error: exec plugin "gke-gcloud-auth-plugin" not found`** | GKE 전용 인증 플러그인 미설치 | `gcloud components install gke-gcloud-auth-plugin` 설치 |
| **Kind와 GKE 컨텍스트 혼동** | 현재 `kubectl`이 로컬 Kind 클러스터를 바라보고 있음 | `kubectl config use-context <gke-context-name>`으로 전환 |

---

## 13. 프로젝트 연관 파일 링크

### 1) 워크로드 매니페스트 (`Workloads`)
- **[GKE-deployment-GCP.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-GCP.yaml)**: **[실무 프로덕션 표준]** GCP Artifact Registry 프라이빗 이미지 기반 무중단 롤링 배포 올인원 매니페스트
- **[GKE-deployment-Docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-Docker.yaml)**: Docker Hub 공용 이미지 기반 무중단 롤링 배포 올인원 매니페스트
- **[GKE-deployment-only-GCP.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-only-GCP.yaml)**: Artifact Registry 이미지 백엔드 Deployment 단독 매니페스트
- **[GKE-deployment-only-Docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-only-Docker.yaml)**: Docker Hub 이미지 백엔드 Deployment 단독 매니페스트
- **[GKE-pod-GCP.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-GCP.yaml)**: GCP Artifact Registry 이미지 기반 단일 Pod 배포 매니페스트
- **[GKE-pod-Docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-Docker.yaml)**: Docker Hub 이미지 기반 단일 Pod 배포 매니페스트
- **[GKE-replicaset-GCP.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-replicaset-GCP.yaml)**: Artifact Registry 이미지 기반 ReplicaSet 매니페스트
- **[GKE-replicaset-Docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-replicaset-Docker.yaml)**: Docker Hub 이미지 기반 ReplicaSet 매니페스트

### 2) 서비스 및 Ingress 매니페스트 (`Services & Ingress`)
- **[GKE-service-lb.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-lb.yaml)**: **[실무 표준]** GCP Network Load Balancer 자동 연동 및 공인 IP 제공 LoadBalancer 서비스
- **[GKE-service-np.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-np.yaml)**: GKE NodePort(30080) 개방 서비스
- **[GKE-service-cip.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-cip.yaml)**: 클러스터 내부 전용 통신 및 `kubectl port-forward`용 ClusterIP 서비스
- **[GKE-ingress.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-ingress.yaml)**: Google Cloud HTTP(S) L7 부하분산기 연동 Ingress 매니페스트
- **[GCP-storageclass.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GCP-storageclass.yaml)**: GCP Persistent Disk CSI 기반 사용자 정의 스토리지 클래스 (`fast`)

### 3) 관련 가이드 및 컴포즈 파일
- **[kind-Workflow.md](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-Workflow.md)**: Kind 로컬 클러스터 구축 및 배포 가이드
- **[Kubernetes-Workflow.md](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/Kubernetes-Workflow.md)**: 쿠버네티스 핵심 개념 종합 가이드
- **[compose-prod-GCPRegistry.yml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/compose-prod-GCPRegistry.yml)**: GCP Artifact Registry 이미지 기반 프로덕션 Docker Compose 파일
- **[compose-prod-docker.yml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/compose-prod-docker.yml)**: Docker Hub 이미지 기반 프로덕션 Docker Compose 파일
