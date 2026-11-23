# getting-started-todo-app for executing in Local Kind Cluster

A Helm chart for getting-started-todo-app

## 사전 준비 (Prerequisites)

로컬 Kind 클러스터 환경에서 차트를 배포하기 전 다음 단계를 순서대로 진행합니다.

### 1. Windows에서 winget으로 필수 도구 설치

Windows 터미널(PowerShell 또는 명령 프롬프트)에서 `winget` 패키지 관리자를 사용하여 필요한 도구들을 설치합니다:

```powershell
# kind (Kubernetes in Docker) 설치
winget install Kubernetes.kind

# kubectl (쿠버네티스 CLI) 설치
winget install Kubernetes.kubectl

# Helm (쿠버네티스 패키지 매니저) 설치
winget install Helm.Helm

# (선택) Docker Desktop이 설치되어 있지 않은 경우
winget install Docker.DockerDesktop
```

> **참고**: 설치 완료 후 환경 변수 적용을 위해 터미널을 재시작하고, Docker Desktop이 정상 실행 중인지 확인합니다.

---

### 2. kind 클러스터 생성 (`my-k8s`, Worker 노드 2개)

my-k8s 이름의 Kind 클러스터가 없으면, 프로젝트 루트 디렉토리에 있는 `kind-config-2workers.yaml` 구성 파일을 사용하여 Control-Plane 1개, Worker 노드 2개로 구성된 `my-k8s` 클러스터를 생성합니다.

```bash
# kind-config-2workers.yaml 설정을 사용하여 my-k8s 클러스터 생성
kind create cluster --name my-k8s --config kind-config-2workers.yaml

# 클러스터 노드 및 상태 확인 (control-plane 1대, worker 2대 확인)
kubectl get nodes
```

---

### 3. 컨테이너 이미지 (`todo-backend:prod`) 빌드 및 kind 클러스터에 로드

`getting-started-todo-app` 프로젝트 루트 디렉토리에서 프로덕션 이미지(`todo-backend:prod`)를 빌드하고, 로컬 kind 클러스터(`my-k8s`)의 각 노드에 이미지를 주입(Load)합니다.

```bash
# 1) getting-started-todo-app 프로젝트 루트 디렉토리로 이동
cd getting-started-todo-app

# 2) 프로덕션용 todo-backend:prod 컨테이너 이미지 빌드
docker build -t todo-backend:prod .
# 또는 명시적 타깃 지정: docker build --target final -t todo-backend:prod .

# 3) my-k8s 클러스터에 이미지 로드
kind load docker-image todo-backend:prod --name my-k8s
```

> **확인**: 노드에 이미지가 성공적으로 로드되었는지 확인하려면 다음 명령어를 실행합니다:
> ```bash
> docker exec -it my-k8s-worker crictl images | grep todo-backend
> ```

---

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
# Standard Helm install
$ helm install  my-release getting-started-todo-app.local_kind

# To use a custom namespace and force the creation of the namespace
$ helm install my-release --namespace my-namespace --create-namespace getting-started-todo-app.local_kind

# To use a custom values file
$ helm install my-release -f my-values.yaml getting-started-todo-app.local_kind
```

### 사용자 정의 설정 파일(`my-values.yaml`) 생성 및 적용

기본 설정 파일(`values.yaml`)을 직접 수정하지 않고 원하는 설정값만 재정의(Override)하려면 별도의 `my-values.yaml` 파일을 생성하여 배포 시 `-f` 옵션으로 지정합니다. 다음 두 가지 방법 중 하나를 선택하여 생성할 수 있습니다:

#### 방법 1. 차트 기본 설정값 전체를 추출하여 생성 (권장)
차트에서 제공하는 기본 `values.yaml` 내용을 파일로 내보낸 후, 변경하고자 하는 항목만 수정합니다:

```bash
# charts 디렉토리 기준 (helm show values 명령어 사용)
helm show values getting-started-todo-app.local_kind > my-values.yaml

# 또는 values.yaml 파일을 직접 복사하여 생성
cp getting-started-todo-app.local_kind/values.yaml my-values.yaml
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
helm install my-release -f my-values.yaml getting-started-todo-app.local_kind
```

See the [Helm documentation](https://helm.sh/docs/intro/using_helm/) for more information on installing and managing the chart.

## Configuration

The following table lists the configurable parameters of the getting-started-todo-app chart and their default values.

| Parameter                                               | Default         |
| ------------------------------------------------------- | --------------- |
| `backend.imagePullPolicy`                               | `IfNotPresent`  |
| `backend.replicas`                                      | `1`             |
| `backend.repository.image`                              | `todo-backend`  |
| `backend.repository.tag`                                | `prod`          |
| `backend.serviceAccount`                                | ``              |
| `mysql.imagePullPolicy`                                 | `IfNotPresent`  |
| `mysql.persistence.todo_mysql_data.accessMode[0].value` | `ReadWriteOnce` |
| `mysql.persistence.todo_mysql_data.enabled`             | `true`          |
| `mysql.persistence.todo_mysql_data.size`                | `1Gi`           |
| `mysql.persistence.todo_mysql_data.storageClass`        | `-`             |
| `mysql.replicas`                                        | `1`             |
| `mysql.repository.image`                                | `mysql`         |
| `mysql.repository.tag`                                  | `9.3`           |
| `mysql.serviceAccount`                                  | ``              |


