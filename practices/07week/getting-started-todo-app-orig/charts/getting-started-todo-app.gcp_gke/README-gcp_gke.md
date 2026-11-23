# getting-started-todo-app for Google Cloud Platform (GCP) GKE

A Helm chart for getting-started-todo-app deployed on Google Kubernetes Engine (GKE) with Google Artifact Registry.

## 사전 준비 (Prerequisites)

GCP GKE 클러스터 및 Artifact Registry 환경에서 Helm 차트를 배포하기 전 다음 단계를 순서대로 진행합니다.

---

### 1. Google Cloud CLI 및 필수 도구 설치

Windows 터미널(PowerShell 또는 명령 프롬프트)에서 `winget` 패키지 관리자를 사용하여 Google Cloud SDK 및 필수 도구들을 설치합니다:

```powershell
# Google Cloud SDK (gcloud CLI) 설치
winget install Google.CloudSDK

# kubectl (쿠버네티스 CLI) 설치
winget install Kubernetes.kubectl

# Helm (쿠버네티스 패키지 매니저) 설치
winget install Helm.Helm

# Docker Desktop 설치 (이미지 빌드 및 푸시용)
winget install Docker.DockerDesktop
```

> **참고**:
> 1. 설치 완료 후 터미널을 재시작하여 환경 변수를 적용합니다.
> 2. GKE 클러스터에 `kubectl`로 인증 및 접속하기 위해 `gke-gcloud-auth-plugin` 구성요소가 필요합니다. 다음 명령어로 설치합니다:
>    ```bash
>    gcloud components install gke-gcloud-auth-plugin
>    ```

---

### 2. GCP 인증 및 기본 설정

GCP 계정으로 로그인하고, 실습에 사용할 GCP 프로젝트 및 리전을 설정합니다:

```bash
# 1) GCP 계정 로그인 (웹 브라우저를 통한 Google 계정 인증)
gcloud auth login

# 2) 기본 프로젝트 ID 설정 (예: ssu-agent-vertex-509708)
gcloud config set project ssu-agent-vertex-509708

# 3) 기본 리전 설정 (서울 리전: asia-northeast3)
gcloud config set compute/region asia-northeast3

# 4) 설정 정보 확인
gcloud config list
```

---

### 3. GCP 필수 API 활성화

GKE 클러스터 운영 및 Artifact Registry 사용을 위해 필요한 GCP 서비스 API를 활성화합니다:

```bash
# 1) Kubernetes Engine API 활성화 (GKE 클러스터 사용)
gcloud services enable container.googleapis.com

# 2) Artifact Registry API 활성화 (컨테이너 이미지 저장소 사용)
gcloud services enable artifactregistry.googleapis.com

# 활성화된 API 확인
gcloud services list --enabled | grep -E "container|artifactregistry"
```

---

### 4. GCP Artifact Registry 인증 및 이미지 푸시

GCP Artifact Registry에 도커 이미지를 업로드할 수 있도록 Docker 인증을 구성하고 이미지를 빌드/푸시합니다.

#### 1) Artifact Registry 저장소 생성 (저장소가 없는 경우)
```bash
gcloud artifacts repositories create my-repo \
    --repository-format=docker \
    --location=asia-northeast3 \
    --description="Docker repository for todo-app"
```

#### 2) Docker CLI에 Artifact Registry 인증 등록
Docker가 GCP Artifact Registry(`asia-northeast3-docker.pkg.dev`)에 안전하게 인증할 수 있도록 자격 증명 도우미를 구성합니다:
```bash
gcloud auth configure-docker asia-northeast3-docker.pkg.dev
```

#### 3) 컨테이너 이미지 빌드 및 Artifact Registry 푸시
프로젝트 루트 디렉토리(`getting-started-todo-app`)에서 이미지를 빌드하고 태그를 지정하여 푸시합니다:
```bash
# 1) 프로덕션용 컨테이너 이미지 빌드
docker build -t asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod .

# 2) Artifact Registry로 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod
```

> **참고 (이미지 Pull 권한)**:  
> 동일한 GCP 프로젝트 내에서 생성된 GKE 클러스터는 노드의 서비스 계정을 통해 Artifact Registry의 이미지에 기본적으로 접근할 수 있습니다. 별도의 `imagePullSecrets` 설정 없이도 배포가 가능합니다.

---

### 5. GCP GKE 인증 및 클러스터 Context 확인/설정

GKE 클러스터 접속 자격증명(Credentials)을 가져오고 `kubectl` 컨텍스트를 GKE 클러스터로 설정합니다.

#### 1) GKE 클러스터 생성 (클러스터가 없는 경우)
```bash
# GKE Autopilot 클러스터 생성 (권장)
gcloud container clusters create-auto my-gke-cluster --region=asia-northeast3

# 또는 GKE Standard 클러스터 생성
# gcloud container clusters create my-gke-cluster --region=asia-northeast3 --num-nodes=2
```

#### 2) GKE 클러스터 자격증명(Credentials) 가져오기
`gcloud container clusters get-credentials` 명령을 실행하면 로컬 `kubeconfig`에 클러스터 접속 정보가 등록되고 context가 자동으로 설정됩니다:
```bash
gcloud container clusters get-credentials my-gke-cluster \
    --region=asia-northeast3 \
    --project=ssu-agent-vertex-509708
```

#### 3) 클러스터 Context 확인 및 설정
여러 클러스터(Kind, Minikube, GKE 등)를 사용하는 환경에서는 현재 `kubectl` 컨텍스트가 GKE 클러스터인지 확인하고 전환합니다:

1. **현재 cluster 상태(context) 확인**:
   ```bash
   kubectl config current-context
   # 출력 예: gke_ssu-agent-vertex-509708_asia-northeast3_my-gke-cluster
   ```

2. **Context 목록 조회**:
   만일 현재 context가 GKE가 아니면, 전체 context 목록을 확인합니다:
   ```bash
   kubectl config get-contexts
   ```

3. **GKE cluster context로 전환**:
   GKE 컨텍스트 이름으로 활성 context를 설정합니다:
   ```bash
   kubectl config use-context gke_ssu-agent-vertex-509708_asia-northeast3_my-gke-cluster
   ```

4. **클러스터 노드 및 연결 상태 확인**:
   ```bash
   kubectl get nodes
   ```

---

### 6. 사용자 정의 설정 파일(`my-values.yaml`) 생성 및 추출 방법

기본 설정 파일(`values.yaml`)을 직접 수정하지 않고 원하는 설정값만 재정의(Override)하려면 별도의 `my-values.yaml` 파일을 생성하여 배포 시 `-f` 옵션으로 지정합니다.

#### 방법 1. 차트 기본 설정값 전체를 추출하여 생성 (권장)
차트에서 제공하는 기본 `values.yaml` 내용을 파일로 내보낸 후, 변경하고자 하는 항목만 수정합니다:

```bash
# charts 디렉토리 기준 (helm show values 명령어 사용)
helm show values getting-started-todo-app.gcp_gke > my-values.yaml

# 또는 values.yaml 파일을 직접 복사하여 생성
cp getting-started-todo-app.gcp_gke/values.yaml my-values.yaml
```

#### 방법 2. 재정의할 항목만 포함하여 직접 작성
기본 설정값을 모두 복사할 필요 없이, 변경하려는 필드만 최소한으로 작성할 수도 있습니다.  
예를 들어 `backend` 복제본(replicas) 수를 2개로 늘리고 리소스 제한(requests/limits)을 설정하려는 경우 다음과 같이 작성합니다:

```yaml
# my-values.yaml
backend:
  replicas: 2
  resources:
    requests:
      cpu: "100m"
      memory: "128Mi"
    limits:
      cpu: "500m"
      memory: "256Mi"
```

생성된 `my-values.yaml`을 적용하여 배포:
```bash
helm install my-release -f my-values.yaml getting-started-todo-app.gcp_gke
```

---

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
# Standard Helm install
$ helm install my-release getting-started-todo-app.gcp_gke

# To use a custom namespace and force the creation of the namespace
$ helm install my-release --namespace my-namespace --create-namespace getting-started-todo-app.gcp_gke

# To use a custom values file
$ helm install my-release -f my-values.yaml getting-started-todo-app.gcp_gke
```

### 배포 확인 및 웹 애플리케이션 접속

1. **파드 기동 상태 확인**:
   ```bash
   kubectl get pods -w
   ```

2. **웹 애플리케이션 접속**:
   * **로컬 포트포워딩 접속 (테스트용)**:
     ```bash
     kubectl port-forward svc/my-release-getting-started-todo-app-backend 8080:3000
     ```
     브라우저에서 `http://localhost:8080` 접속

   * **GKE 외부 공인 IP(External IP) 발급 (LoadBalancer)**:
     ```bash
     # 서비스 타입을 LoadBalancer로 변경
     kubectl patch svc my-release-getting-started-todo-app-backend -p '{"spec": {"type": "LoadBalancer"}}'

     # 외부 IP 확인
     kubectl get svc my-release-getting-started-todo-app-backend -w
     ```
     발급된 `<EXTERNAL-IP>:3000`으로 브라우저 접속

3. **실습 종료 후 리소스 정리 (비용 방지)**:
   ```bash
   helm uninstall my-release
   ```

See the [Helm documentation](https://helm.sh/docs/intro/using_helm/) for more information on installing and managing the chart.

---

## Configuration

The following table lists the configurable parameters of the getting-started-todo-app chart and their default values.

| Parameter                                               | Default                                                                       |
| ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `backend.imagePullPolicy`                               | `IfNotPresent`                                                                |
| `backend.replicas`                                      | `1`                                                                           |
| `backend.repository.image`                              | `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend` |
| `backend.repository.tag`                                | `prod`                                                                        |
| `backend.serviceAccount`                                | ``                                                                            |
| `mysql.imagePullPolicy`                                 | `IfNotPresent`                                                                |
| `mysql.persistence.todo_mysql_data.accessMode[0].value` | `ReadWriteOnce`                                                               |
| `mysql.persistence.todo_mysql_data.enabled`             | `true`                                                                        |
| `mysql.persistence.todo_mysql_data.size`                | `1Gi`                                                                         |
| `mysql.persistence.todo_mysql_data.storageClass`        | `-`                                                                           |
| `mysql.replicas`                                        | `1`                                                                           |
| `mysql.repository.image`                                | `mysql`                                                                       |
| `mysql.repository.tag`                                  | `9.3`                                                                         |
| `mysql.serviceAccount`                                  | ``                                                                            |
