# Kind 클러스터 로컬 포트 매핑 및 배포 워크플로우

본 문서는 Kind(Kubernetes in Docker) 환경에서 로컬 호스트(`http://localhost`)를 통해 애플리케이션에 접근할 수 있도록 포트 매핑(NodePort) 및 `cloud-provider-kind` 기반의 `LoadBalancer` 서비스를 구성하고 배포하는 전체 과정을 정리한 가이드입니다.

---

## 1. 문제 현상 및 원인 분석

### 문제 현상
- Kubernetes 클러스터에 MySQL 및 Todo-Backend 애플리케이션을 정상 배포(Pod 상태 `Running`)하였으나, 브라우저에서 `http://localhost` 접속 시 **"사이트에 연결할 수 없음 (localhost에서 연결을 거부했습니다)"** 오류 발생.

### 원인
- **Kind 아키텍처 특성**: Kind 클러스터의 노드는 Docker 컨테이너(`control-plane`)로 실행됩니다.
- **포트 매핑 누락**: `deployment-kind.yaml`의 Service가 `NodePort: 30080`으로 열려있더라도, 이는 Kind 노드 Docker 컨테이너 내부의 포트입니다. 호스트 PC(Windows)의 포트 80과 Kind 노드의 포트 30080이 도커 레벨에서 포워딩되어 있지 않아 호스트에서 접근이 불가했던 것입니다.

---

## 2. 해결 워크플로우 (방법 1: extraPortMappings NodePort 방식)

### 단계 1: Kind 포트 매핑 설정 파일 작성 (`kind-config.yaml`)
호스트의 `80` 포트를 Kind 노드의 NodePort(`30080`)로 전달하도록 설정합니다.

```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
  extraPortMappings:
  - containerPort: 30080   # deployment-kind.yaml의 Service nodePort
    hostPort: 80           # 호스트 PC의 접속 포트 (http://localhost)
    protocol: TCP
```

---

### 단계 2: Kind 클러스터 생성
기존 클러스터가 있다면 삭제 후, 생성한 설정 파일을 적용하여 새 클러스터를 생성합니다.

```powershell
# 기존 클러스터가 있는 경우 삭제
kind delete cluster --name my-k8s

# 포트 매핑 설정을 적용하여 클러스터 생성
kind create cluster --name my-k8s --config kind-config.yaml
```

---

### 단계 3: 로컬 도커 이미지 Kind 노드로 로드 (필요한 경우)
로컬에 빌드된 이미지를 사용하는 경우(예: `todo-backend:prod`), Kind 클러스터 내부 노드로 이미지를 전달해야 Pod가 이미지를 정상적으로 읽을 수 있습니다.

```powershell
kind load docker-image todo-backend:prod --name my-k8s
```

---

### 단계 4: Kubernetes 리소스 배포 (`deployment-kind.yaml`)
Secret, ConfigMap, PVC, MySQL, Backend Deployment 및 NodePort Service를 배포합니다.

```powershell
kubectl apply -f deployment-kind.yaml
```

> **참고 (Service 설정 요약)**:
> ```yaml
> apiVersion: v1
> kind: Service
> metadata:
>   name: todo-backend
> spec:
>   type: NodePort
>   selector:
>     app: todo-backend
>   ports:
>     - name: http
>       port: 80
>       targetPort: 3000
>       nodePort: 30080
> ```

---

### 단계 5: 배포 상태 확인

```powershell
# 파드 구동 상태 확인 (Running 및 READY 1/1 확인)
kubectl get pods

# 서비스 및 NodePort 확인
kubectl get svc
```

---

### 단계 6: 접속 및 동작 검증
추가적인 포트포워딩 명령어 없이 호스트의 웹 브라우저에서 바로 접속합니다.

- **웹 애플리케이션 접속**: [http://localhost](http://localhost)
- **API 상태 확인**: [http://localhost/api/items](http://localhost/api/items)

---

## 3. 부록: 대안 (임시 포트 포워딩 방식 및 트러블슈팅)

Kind 설정 변경 없이 즉시 특정 서비스나 파드에 접근하고자 할 때는 `kubectl port-forward`를 사용할 수 있습니다.

### 3.1 기본 명령어 및 사용법

```powershell
# 1. Service 대상 포워딩 (권장): <로컬포트>:<서비스포트>
# Service의 port 80이 Pod의 targetPort 3000으로 자동 중계됩니다.
kubectl port-forward svc/todo-backend 1234:80

# 80 포트로 직접 바인딩하는 경우
kubectl port-forward svc/todo-backend 80:80

# 2. Pod 대상 포워딩: <로컬포트>:<컨테이너포트>
# Pod를 직접 지정할 때는 Service 포트(80)가 아닌 Pod 실제 컨테이너 포트(3000)를 지정해야 합니다.
kubectl port-forward <pod-name> 1234:3000
```

---

### 3.2 자주 발생하는 오류와 트러블슈팅

#### ❌ 오류 사례 1: `pods "todo-backend" not found`
```powershell
kubectl port-forward todo-backend 1234:80
# Error from server (NotFound): pods "todo-backend" not found
```
- **원인**: 리소스 타입 접두사를 생략하면 `kubectl`은 기본적으로 **Pod**를 찾습니다. 하지만 `todo-backend`는 Pod 이름이 아니라 Service 이름(또는 Deployment 이름)이므로 Pod를 찾을 수 없다는 에러가 발생합니다.
- **해결책**: Service를 대상으로 지정할 때는 반드시 앞에 `svc/` 접두사를 붙여야 합니다:
  ```powershell
  kubectl port-forward svc/todo-backend 1234:80
  ```

---

#### ❌ 오류 사례 2: `connection refused` (Pod 대상 포트 불일치)
```powershell
kubectl port-forward todo-backend-54986bc7f9-2ksvq 1234:80
# E1008 ... failed to connect to localhost:80 inside namespace ... connection refused
```
- **원인**: Pod를 직접 대상으로 지정할 때 대상 포트를 `80`으로 주었으나, **Pod 내부 컨테이너 애플리케이션(Node.js)은 `3000`번 포트에서 수신(Listen)**하고 있기 때문입니다.
- **해결책**:
  - Pod를 대상으로 할 때는 컨테이너 포트인 **`3000`** 을 명시해야 합니다:
    ```powershell
    kubectl port-forward todo-backend-54986bc7f9-2ksvq 1234:3000
    ```
  - 또는 앞서 설명한 대로 Service(`svc/todo-backend`)를 대상으로 하면 Service가 알아서 `port 80 -> targetPort 3000`으로 매핑해 줍니다.

---

### 3.3 정상 연결 시 출력 예시

```text
Forwarding from 127.0.0.1:1234 -> 3000
Forwarding from [::1]:1234 -> 3000
Handling connection for 1234
Handling connection for 1234
```
- 브라우저 접속: **[http://localhost:1234](http://localhost:1234)**

---

### 3.4 `kubectl port-forward <pod-name> 80:3000`의 내부 동작 원리 및 워크플로우

`kubectl port-forward todo-backend-54986bc7f9-vw99l 80:3000` 명령은 로컬 호스트(개발자 PC)의 80번 포트를 쿠버네티스 클러스터 내부에서 실행 중인 특정 파드의 3000번 포트로 직접 연결하는 **SPDY/WebSocket 기반의 보안 양방향 터널링 메커니즘**입니다.

Service(NodePort, LoadBalancer) 리소스가 없거나 삭제된 상태에서도 파드에 직접 연결하여 동작을 검증할 수 있습니다.

#### 1) 동작 아키텍처 다이어그램

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 호스트 PC (Windows)                                                     │
│                                                                        │
│   [웹 브라우저] ──(HTTP 요청: http://localhost:80)                      │
│        │                                                               │
│        ▼                                                               │
│   [kubectl port-forward] ──(127.0.0.1:80 로컬 포트 Listen 대기)        │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ SPDY / WebSocket 양방향 암호화 스트리밍 터널 (HTTPS 6443)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Kubernetes 클러스터 (Kind Control-Plane)                                │
│                                                                        │
│   [Kube-API-Server] (포트포워딩 API 엔드포인트 수신)                     │
│        │                                                               │
│        │ gRPC / 내부 프록시 전달                                        │
│        ▼                                                               │
│   [Kubelet] (노드 에이전트)                                             │
│        │                                                               │
│        │ containerd / CRI (Pod 네트워크 네임스페이스 진입)              │
│        ▼                                                               │
│   [Pod: todo-backend-54986bc7f9-vw99l]                                 │
│        └── 컨테이너: Node.js 애플리케이션 (Port 3000 Listen)           │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2) 단계별 상세 처리 워크플로우 (Step-by-Step)

1. **로컬 소켓 리스닝 (Local Listening)**:
   - `kubectl` 프로세스가 호스트 PC(Windows)에서 `127.0.0.1:80` 및 `[::1]:80` TCP 소켓을 생성하고 클라이언트 요청을 수신 대기합니다.
   - *출력: `Forwarding from 127.0.0.1:80 -> 3000`*

2. **API Server 스트리밍 터널 수립**:
   - `kubectl`은 클러스터의 마스터 노드에 위치한 **Kube-API-Server**로 `POST /api/v1/namespaces/default/pods/todo-backend-.../portforward` 요청을 보내고 양방향 스트리밍 연결을 유지합니다.

3. **Kubelet으로 프록시 전달**:
   - Kube-API-Server는 대상 파드가 실제로 기동 중인 워커 노드의 **Kubelet**으로 연결을 중계(Proxy)합니다.

4. **파드 네트워크 네임스페이스(Network Namespace) 직접 바인딩**:
   - 노드의 Kubelet은 컨테이너 런타임(containerd)을 통해 해당 파드의 네트워크 네임스페이스 내부로 직접 진입하여, 파드 내부의 `localhost:3000`으로 소켓 연결을 맺습니다.

5. **실시간 트래픽 양방향 포워딩 (Data Transfer)**:
   - 개발자가 브라우저에서 `http://localhost`로 접속하면, 로컬 `kubectl`이 요청을 가로채서 API Server ➔ Kubelet ➔ 파드 컨테이너(3000 포트)로 즉시 전달합니다.
   - *출력: `Handling connection for 80` (브라우저가 80번 포트로 연결을 맺고 데이터를 주고받을 때마다 실시간 로깅)*
   - 컨테이너에서 반환된 HTTP 응답은 역순으로 전달되어 브라우저에 표시됩니다.

#### 3) 주요 특징 및 사용 시 주의사항

* **Service 객체 무관**: Service(NodePort, LoadBalancer)가 없거나 삭제되어도 파드가 `Running` 상태면 1:1로 직접 접근 가능하여 빠른 디버깅에 최적입니다.
* **프로세스 종속성**: `kubectl` 명령어가 실행 중인 동안에만 터널이 유지됩니다. 터미널 창을 닫거나 `Ctrl + C`로 프로세스를 종료하면 포트포워딩이 즉시 해제됩니다.
* **개발/디버그 전용**: 단일 파드로의 임시 터널이므로 부하 분산(Load Balancing)이나 운영 환경 서비스 용도로는 사용할 수 없습니다.

---

### 3.5 `kubectl port-forward svc/<service-name> 1234:80`의 동작 구조 및 워크플로우

`kubectl port-forward svc/todo-backend-cip 1234:80` 명령은 파드 이름을 직접 조회하지 않고, **Service 객체를 거쳐 파드로 연결을 자동 위임하는 가장 권장되는 포트포워딩 방식**입니다.

#### 1) 동작 아키텍처 다이어그램

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 호스트 PC (Windows)                                                     │
│                                                                        │
│   [웹 브라우저] ──(HTTP 요청: http://localhost:1234)                   │
│        │                                                               │
│        ▼                                                               │
│   [kubectl port-forward] ──(127.0.0.1:1234 로컬 TCP 포트 Listen)       │
└────────┬───────────────────────────────────────────────────────────────┘
         │
         │ SPDY / WebSocket 터널 (1234 ➔ 3000)
         ▼
┌────────────────────────────────────────────────────────────────────────┐
│ Kubernetes 클러스터                                                     │
│                                                                        │
│   [1. Kube-API-Server]                                                 │
│        │                                                               │
│        ├─▶ [Service 조회: todo-backend-cip]                             │
│        │    - port: 80 ➔ targetPort: 3000 매핑 확인                    │
│        │    - Endpoints 조회: 준비 완료(Ready)된 Pod 자동 선택           │
│        │                                                               │
│        ▼ (선택된 Pod의 노드로 프록시 전달)                              │
│   [2. Kubelet]                                                         │
│        │                                                               │
│        ▼ (Pod 네트워크 네임스페이스의 3000 포트로 전달)                 │
│   [3. Pod: todo-backend-...] (컨테이너 포트 3000 Listen)                │
└────────────────────────────────────────────────────────────────────────┘
```

#### 2) 세부 동작 워크플로우 (Step-by-Step)

1. **Service 및 포트 유효성 검사**:
   - `kubectl`은 API Server에 `svc/todo-backend-cip`의 명세를 요청합니다.
   - 명령어에 입력한 대상 포트(`80`)가 Service의 `spec.ports[].port`에 실제로 존재하는지 확인합니다.
   - > ⚠️ **주의**: 만약 `svc/todo-backend-cip 1234:3000`을 실행하면, Service의 포트는 80이고 3000은 컨테이너 포트이므로 `error: Service ... does not have a service port 3000` 오류가 발생합니다. 서비스 포워딩 시에는 반드시 **Service의 port(80)**를 지정해야 합니다.

2. **엔드포인트 해석 및 대상 파드 자동 선택 (Pod Selection)**:
   - API Server는 해당 Service의 `Endpoints` 또는 `EndpointSlice`를 확인하여, 라벨 셀렉터(`app: todo-backend`)와 일치하고 `Ready` 상태인 파드 중 하나를 **자동으로 선택**합니다.
   - Service의 포트 매핑(`port 80 ➔ targetPort 3000`)에 따라, 실제 터널 목적지를 대상 파드의 **`3000`번 포트**로 결정합니다.

3. **로컬 소켓 리스닝 및 파드 터널 바인딩**:
   - 로컬 호스트에 `127.0.0.1:1234` 포트를 개방합니다.
   - 이때 화면에 **`Forwarding from 127.0.0.1:1234 -> 3000`**이 출력되는 이유는, `kubectl`이 서비스 정의를 해석하여 최종 목적지인 파드의 `targetPort(3000)`로 터널을 연결했기 때문입니다.

4. **실시간 트래픽 처리**:
   - 사용자가 브라우저에서 `http://localhost:1234`에 접속하면, 로컬의 1234 포트로 들어온 요청이 API Server와 Kubelet을 거쳐 백엔드 파드의 3000번 포트로 실시간 중계됩니다.
   - 연결이 맺어질 때마다 터미널에 **`Handling connection for 1234`** 로그가 출력됩니다.

#### 3) Service 포워딩 vs Pod 직접 포워딩 비교

| 비교 항목 | `svc/todo-backend-cip 1234:80` (Service 대상) | `<pod-name> 1234:3000` (Pod 대상) |
| :--- | :--- | :--- |
| **대상 식별자** | 고정된 Service 이름 사용 (`svc/...`) | 매번 변경되는 난수 파드 이름 조회 필요 |
| **포트 지정 기준** | **Service 포트 (`80`)** 지정 | **컨테이너 실제 포트 (`3000`)** 지정 |
| **타깃 포트 해석** | Service의 `targetPort`를 읽어 3000으로 자동 중계 | 사용자가 컨테이너 포트(3000)를 직접 명시 |
| **파드 장애 대응** | 파드 재시작 시 엔드포인트의 정상 파드로 자동 연결 | 해당 파드가 종료되면 즉시 포워딩 중단 |
| **추천 상황** | **일반적인 개발/테스트 및 디버깅 (강력 권장)** | 특정 특정 파드 단일 인스턴스만 정밀 진단할 때 |

---

## 4. 고급: `cloud-provider-kind`를 활용한 LoadBalancer 기반 외부 노출

### 4.1 `cloud-provider-kind`란 무엇인가?

`cloud-provider-kind`는 **Kubernetes SIGs(Special Interest Groups)**의 공식 서브프로젝트로, **Kind(Kubernetes in Docker) 클러스터에서 `type: LoadBalancer` 서비스를 지원하기 위해 개발된 로컬용 Cloud Controller Manager(CCM)**입니다.

- **배경**: AWS(EKS)의 NLB/ALB, GCP(GKE)의 Cloud Load Balancer와 같은 퍼블릭 클라우드에서는 `type: LoadBalancer` 서비스를 생성하면 클라우드 제공자가 자동으로 External IP를 할당해 줍니다.
- 하지만 로컬 Kind 환경에서는 클라우드 제공자가 없기 때문에 `type: LoadBalancer` 서비스를 생성하면 `EXTERNAL-IP`가 영원히 `<pending>` 상태로 멈추게 됩니다.
- `cloud-provider-kind`는 로컬 머신에서 클라우드 제공자 역할을 에뮬레이션하여 Kind 서비스에 **실제 접속 가능한 External IP를 할당**해 줍니다.

---

### 4.2 주요 역할 및 기능

1. **Service 모니터링 (Watch)**: Kind 클러스터 내에서 생성/수정/삭제되는 `type: LoadBalancer` 서비스를 실시간으로 감지합니다.
2. **External IP 자동 프로비저닝**:
   - `<pending>` 상태로 대기 중인 서비스에 유효한 External IP(Windows/macOS의 경우 `127.0.0.1`, Linux의 경우 Docker 서브넷 IP 등)를 자동 할당합니다.
3. **데이터 플레인(프록시) 자동 생성**:
   - 호스트 머신의 포트에서 Kind 노드로 트래픽을 중계해 주는 전용 프록시 컨테이너(또는 포트 바인딩)를 Docker 상에 자동으로 생성/연결합니다.
4. **수명 주기 관리**: 서비스가 삭제되면 관련 프록시 컨테이너 및 리소스를 자동으로 회수(Cleanup)합니다.

---

### 4.3 내부 동작 구조 (Architecture & Mechanism)

```
[로컬 브라우저 / 외부 클라이언트]
       │  (요청: http://localhost:80 또는 http://127.0.0.1:80)
       ▼
┌────────────────────────────────────────────────────────┐
│ 호스트 PC (Windows / Docker Desktop)                    │
│                                                        │
│  [cloud-provider-kind.exe] (데몬 프로세스)              │
│       │ 1. K8s API 감시 (type: LoadBalancer Service 감지) │
│       │ 2. 서비스 status.loadBalancer.ingress에 IP(127.0.0.1) 주입
│       │ 3. Docker API 호출 -> 프록시 컨테이너 생성/바인딩 │
│       ▼                                                │
│  [Docker 프록시 컨테이너 / 포트 매핑]                   │
│       │                                                │
│       │ (트래픽 전달)                                    │
│       ▼                                                │
│  [Kind Node 컨테이너: my-k8s-control-plane]             │
│       │                                                │
│       │ Kube-Proxy / iptables 라우팅                   │
│       ▼                                                │
│  [Pod: todo-backend (Port 3000)]                       │
└────────────────────────────────────────────────────────┘
```

#### 세부 동작 단계
1. **이벤트 감지**: 사용자가 `kubectl apply`로 `type: LoadBalancer` Service를 등록하면, `cloud-provider-kind`가 쿠버네티스 API 이벤트를 수신합니다.
2. **IP 할당 및 Status 업데이트**: 쿠버네티스 Service 객체의 `status.loadBalancer.ingress` 필드에 접속 가능한 IP(`127.0.0.1` 등)를 기록합니다. 이로써 `kubectl get svc`에서 `<pending>`이 사라지고 IP가 출력됩니다.
3. **Docker 프록시 컨테이너 기동**: `cloud-provider-kind`는 Docker API를 통해 로컬 호스트의 포트(예: 80)를 열고, 트래픽을 Kind 클러스터 내부의 해당 서비스 포트로 포워딩하는 가벼운 프록시 컨테이너를 Docker bridge 네트워크에 동적으로 실행합니다.
4. **MetalLB와의 차이점**:
   - **MetalLB**: ARP/BGP 프로토콜 기반으로 L2 레벨에서 가상 IP를 할당하므로, 가상화 레이어(Hyper-V / WSL2)가 있는 Windows/macOS의 Docker Desktop 환경에서는 호스트에서 해당 IP로 라우팅하기 매우 어렵습니다.
   - **cloud-provider-kind**: Docker API를 직접 제어하여 포트 바인딩 및 프록시를 처리하므로 Windows/macOS Docker Desktop 환경에서도 완벽하고 안정적으로 동작합니다.

---

### 4.4 Windows 환경 설치 방법

#### 방법 A: 공식 바이너리 직접 다운로드 (권장)
1. [GitHub Releases](https://github.com/kubernetes-sigs/cloud-provider-kind/releases)에서 Windows용 최신 바이너리(`cloud-provider-kind_X.X.X_windows_amd64.tar.gz` 또는 `.exe`)를 다운로드합니다.
2. 또는 PowerShell에서 아래 명령어로 다운로드하여 작업 디렉토리 또는 PATH 경로에 배치합니다:
   ```powershell
   # 현재 디렉토리에 다운로드
   curl.exe -Lo cloud-provider-kind.exe https://github.com/kubernetes-sigs/cloud-provider-kind/releases/latest/download/cloud-provider-kind-windows-amd64.exe
   ```
3. 편리한 사용을 위해 `C:\Windows\System32` 또는 사용자 PATH에 등록된 폴더(`C:\Users\<사용자>\AppData\Local\Programs\DockerDesktop\resources\bin` 등)로 이동시키면 어디서든 명령어 실행이 가능합니다.

#### 방법 B: Go 도구를 통한 설치 (Go가 설치된 경우)
```powershell
go install sigs.k8s.io/cloud-provider-kind@latest
```

---

### 4.5 `cloud-provider-kind`를 활용한 배포 및 외부 접속 실습

#### 1단계: `cloud-provider-kind` 데몬 실행
별도의 PowerShell 창을 열고 `cloud-provider-kind`를 실행합니다. (클러스터가 켜져 있는 동안 항상 백그라운드에서 실행 상태를 유지해야 합니다)

```powershell
.\cloud-provider-kind.exe
```
> ※ 실행 시 자동으로 로컬 Docker와 Kind 클러스터(`my-k8s`)를 인식하고 대기 상태가 됩니다.

---

#### 2단계: Service 타입을 `LoadBalancer`로 작성
[deployment-kind.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind.yaml)의 서비스 설정을 `NodePort` 대신 `LoadBalancer`로 설정하거나 별도의 매니페스트를 작성합니다.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: todo-backend-lb
  labels:
    app.kubernetes.io/name: getting-started-todo-app
    app.kubernetes.io/component: backend
spec:
  type: LoadBalancer
  selector:
    app: todo-backend
  ports:
    - name: http
      port: 80
      targetPort: 3000
```

---

#### 3단계: 리소스 적용 및 External IP 확인

```powershell
kubectl apply -f deployment-kind.yaml
```

서비스 목록을 조회하여 `EXTERNAL-IP`가 정상적으로 할당되었는지 확인합니다:

```powershell
kubectl get svc
```

**출력 예시**:
```text
NAME               TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
kubernetes         ClusterIP      10.96.0.1       <none>        443/TCP        15m
mysql              ClusterIP      10.96.214.153   <none>        3306/TCP       10m
todo-backend-lb    LoadBalancer   10.96.180.12    127.0.0.1     80:31234/TCP   12s
```
> 💡 `cloud-provider-kind`가 백그라운드에서 동작 중이면 `EXTERNAL-IP`가 `<pending>`에 머무르지 않고 즉시 `127.0.0.1`로 할당됩니다!

---

#### 4단계: 외부 접속 검증
웹 브라우저를 열고 할당된 External IP 또는 `localhost`로 접속합니다:

- [http://localhost](http://localhost)
- [http://127.0.0.1](http://127.0.0.1)
- API 엔드포인트: [http://localhost/api/items](http://localhost/api/items)

---

## 5. 포트 노출 방식 비교 요약

| 구분 | 1. extraPortMappings (NodePort) | 2. kubectl port-forward | 3. cloud-provider-kind (LoadBalancer) |
| :--- | :--- | :--- | :--- |
| **방식** | Kind 클러스터 생성 시 정적 포트 바인딩 | K8s CLI 디버깅용 터널링 | K8s 공식 Cloud Controller Manager(CCM) 에뮬레이션 |
| **클러스터 재생성** | 필요 (`kind-config.yaml`) | 불필요 | 불필요 (기존 Kind 클러스터 그대로 사용 가능) |
| **K8s Service Type** | `NodePort` | `ClusterIP` / `NodePort` | `LoadBalancer` |
| **External IP 할당** | ❌ (할당 안 됨) | ❌ (CLI 터널링) | ⭕ (`127.0.0.1` 자동 할당) |
| **운영 환경과의 일치도** | 보통 | 낮음 (개발/디버그 전용) | **매우 높음 (실제 클라우드 환경 매니페스트 그대로 사용 가능)** |
| **적합한 사용처** | 단일 포트 고정 로컬 테스트 | 일시적인 문제 진단 및 확인 | **클라우드 배포용 매니페스트 사전 검증 및 멀티 서비스 테스트** |

---

## 6. 내부 아키텍처 분석: MySQL Service 및 ClusterIP의 역할과 필수성

`deployment-kind-pod.yaml`과 같은 매니페스트에서 백엔드 앱과 데이터베이스를 분리 배포할 때, `mysql`에 대한 `Deployment`뿐만 아니라 `Service(ClusterIP)`를 반드시 함께 정의하여 사용해야 합니다.

### 6.1 MySQL Service(`kind: Service`) 삭제 시 발생하는 문제 및 원인

만약 `mysql` Deployment는 유지한 채 `mysql` Service 리소스만 삭제하면, **전체 서비스가 완전히 중단되며 `todo-backend` 파드는 기동조차 되지 못합니다.**

```text
[Service 삭제 시 장애 흐름]
todo-backend Pod 기동
   │
   ▼
[initContainer: wait-for-mysql] ──(nc -z -v -w3 mysql 3306)──▶ CoreDNS에 'mysql' 질의
   │                                                                    │
   │                                                                    ▼
   │                                                            [Service 없음: NXDOMAIN]
   ▼                                                                    │
연결 실패 (Name resolution failure) ◀───────────────────────────────────┘
   │
   ▼
무한 재시도 루프 (sleep 2) ──▶ 메인 컨테이너 실행 불가 (Pod 상태: Init:0/1 영구 고착)
```

1. **클러스터 내부 DNS 도메인 해석(DNS Resolution) 실패**
   - [todo-config ConfigMap](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind-pod.yaml#L14-L26)에 `MYSQL_HOST: "mysql"`로 정의되어 있고, 백엔드는 이 도메인 이름(`mysql:3306`)으로 접속을 시도합니다.
   - 쿠버네티스의 **CoreDNS는 Service 리소스를 기반으로 클러스터 내부 도메인 레코드(`mysql` ➔ Service의 ClusterIP)를 생성**합니다.
   - 따라서 Service를 삭제하면 `mysql`이라는 호스트 이름을 IP로 변환할 수 없게 되어 DNS 조회 실패(`Unknown Host / NXDOMAIN`)가 발생합니다.

2. **`initContainer` 단계에서 무한 대기 (메인 애플리케이션 기동 차단)**
   - [todo-backend Deployment](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind-pod.yaml#L150-L163)에는 메인 컨테이너 기동 전 MySQL 연결 가능 여부를 검사하는 `initContainers`(`wait-for-mysql`)가 포함되어 있습니다:
     ```sh
     until nc -z -v -w3 mysql 3306; do
       echo "MySQL is not ready yet, sleeping 2s..."
       sleep 2
     done
     ```
   - Service가 없으므로 `mysql 3306` 포트로의 연결이 영구히 실패하여 루프를 빠져나오지 못하고, 메인 컨테이너(`todo-backend`)는 시작조차 되지 못한 채 파드 상태가 `Init:0/1`에 멈추게 됩니다.

---

### 6.2 고정된 `ClusterIP`와 `Port`를 반드시 사용해야 하는 이유

쿠버네티스 환경에서 파드 간 통신 시 개별 Pod IP에 직접 연결하지 않고 **Service의 ClusterIP와 포트(3306)**를 거쳐야 하는 핵심 이유는 다음과 같습니다.

| 핵심 이유 | 설명 |
| :--- | :--- |
| **1. Pod IP의 휘발성(Ephemerality) 해결** | 쿠버네티스의 파드는 일시적인(Ephemeral) 객체로, 노드 재배치, 파드 재시작, 롤링 업데이트 시마다 **새로운 Pod IP로 매번 변경**됩니다.<br>반면 **`ClusterIP`는 Service가 삭제되기 전까지 영구히 유지되는 고정 가상 IP(VIP)**이므로, 백엔드는 DB 파드의 IP 변경에 영향받지 않습니다. |
| **2. 서비스 디스커버리 (Service Discovery)** | Service 이름(`mysql`)이 내부 DNS에 자동 등록되어, 애플리케이션 코드나 설정 파일([ConfigMap](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/deployment-kind-pod.yaml#L14-L26))에 IP를 하드코딩할 필요 없이 `mysql:3306`이라는 고정 식별자를 사용할 수 있습니다. |
| **3. 안정적인 포트 라우팅 및 추상화** | Service의 `port: 3306`과 파드의 `targetPort: 3306`을 매핑하고, `kube-proxy`와 `iptables/IPVS` 룰을 통해 클라이언트 요청을 실제 정상 가동 중인 MySQL 파드로 안전하게 포워딩합니다. |
| **4. 헬스체크(Readiness Probe) 기반 트래픽 제어** | MySQL 컨테이너가 시작되더라도 내부 데이터베이스 엔진이 완전히 초기화되기 전까지는 요청을 처리할 수 없습니다.<br>Service는 파드의 `readinessProbe` 검사를 통과하여 준비 완료(`Ready`) 상태가 된 파드의 엔드포인트(Endpoints/EndpointSlice)로만 트래픽을 라우팅하므로 불완전한 연결 시도를 원천 차단합니다. |

---

## 7. 쿠버네티스 서비스 심화: ClusterIP와 NodePort의 'Cluster-IP' 비교 분석

`kubectl get svc`를 조회했을 때 나타나는 `todo-backend-cip(ClusterIP)`와 `todo-backend-np(NodePort)`의 **CLUSTER-IP** 필드 간의 차이점과 동작 관계를 분석합니다.

```text
NAME               TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
todo-backend-cip   ClusterIP   10.96.164.241   <none>        80/TCP         15m
todo-backend-np    NodePort    10.96.125.67    <none>        80:30080/TCP   21s
```

### 7.1 핵심 결론: Cluster-IP 자체의 기능적 차이는 전혀 없음 (100% 동일)

두 서비스에 할당된 **`Cluster-IP` 자체의 성격, 네트워크 라우팅 방식, 기능에는 아무런 차이가 없습니다.**

* 둘 다 쿠버네티스 클러스터 내부 가상 IP 대역(`10.96.0.0/12` 등)에서 자동으로 발급되는 **고정 가상 IP(VIP, Virtual IP)**입니다.
* 둘 다 클러스터 내부(노드 및 파드)에서만 라우팅되며, 외부 인터넷에서는 직접 도달할 수 없습니다.
* 둘 다 `kube-proxy`의 iptables 또는 IPVS 룰을 통해 셀렉터(`app: todo-backend`)를 만족하는 실제 백엔드 파드로 균등하게 트래픽을 분산합니다.

---

### 7.2 왜 NodePort 서비스에도 Cluster-IP가 존재하는가? (계층적 상속 구조)

쿠버네티스의 서비스 타입은 서로 완전히 독립된 프로토콜이 아니라, **아래 단계의 기능을 그대로 포함하면서 기능을 확장하는 계층적 상속(Inheritance) 구조**를 가집니다:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ [ClusterIP Service]                                                    │
│   • 내부 가상 IP(Cluster-IP) 발급                                       │
│   • 클러스터 내부 DNS 도메인(todo-backend-cip) 제공                     │
│   • 클러스터 내부 파드 간 로드밸런싱                                   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (기능 상속 및 확장)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ [NodePort Service]                                                     │
│   • ClusterIP의 모든 기능 100% 포함 (내부용 Cluster-IP 필수 존재!)      │
│   • [추가 기능] 모든 노드의 물리 포트(30080)를 외부에 추가 개방        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (기능 상속 및 확장)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ [LoadBalancer Service]                                                 │
│   • NodePort의 모든 기능 100% 포함 (Cluster-IP + NodePort 둘 다 존재!)  │
│   • [추가 기능] 클라우드 외부 IP(External-IP) 자동 프로비저닝          │
└────────────────────────────────────────────────────────────────────────┘
```

즉, **`NodePort`는 `ClusterIP`를 대체하는 것이 아니라, `ClusterIP` 위에 외부 접근용 관문(NodePort: 30080)을 하나 더 얹은 구조**입니다.

---

### 7.3 외부 트래픽 인입 시의 Kube-proxy 처리 흐름

외부에서 `NodePort(30080)`로 접속했을 때 쿠버네티스 내부 라우팅을 추적해 보면 왜 NodePort 서비스에도 Cluster-IP가 필수적인지 이해할 수 있습니다:

```text
[외부 클라이언트] (http://<NodeIP>:30080 또는 http://localhost:80)
       │
       ▼
[Kind 노드의 물리/도커 포트: 30080 인입]
       │
       ▼ (노드의 Kube-proxy / iptables 체인)
  "30080 포트로 들어온 패킷을 해당 서비스의 Cluster-IP 처리 체인(KUBE-SVC-xxx)으로 전달"
       │
       ▼
[Cluster-IP: 10.96.125.67 라우팅 규칙]
       │
       ▼ (엔드포인트 파드 중 하나로 부하 분산)
[Pod: todo-backend-54986bc7f9-p7wbz (IP: 10.244.0.11, Port: 3000)]
```

외부에서 노드의 30080 포트로 들어온 트래픽은 노드의 `kube-proxy`에 의해 사실상 **서비스의 `Cluster-IP` 라우팅 체인으로 넘겨져서** 파드로 전달됩니다.

---

### 7.4 상세 비교 요약표

| 비교 항목 | `todo-backend-cip` (`ClusterIP`) | `todo-backend-np` (`NodePort`) |
| :--- | :--- | :--- |
| **할당된 Cluster-IP** | `10.96.164.241` | `10.96.125.67` |
| **Cluster-IP 대역** | `10.96.0.0/12` (가상 IP) | `10.96.0.0/12` (가상 IP) **[동일]** |
| **내부 통신 지원** | ⭕ 지원 (`http://10.96.164.241:80` 또는 DNS) | ⭕ 지원 (`http://10.96.125.67:80` 또는 DNS) **[동일]** |
| **외부 노출 포트 (NodePort)** | ❌ 없음 (오직 클러스터 내부 통신만 가능) | ⭕ 노드마다 `30080` 포트 개방 |
| **외부 접속 가능 여부** | ❌ 불가 (`port-forward` 없이는 호스트 접근 불가) | ⭕ 가능 (`http://<NodeIP>:30080` 직접 접속) |
| **주요 활용 목적** | DB, 캐시, 내부 마이크로서비스 등 비공개 백엔드 | 웹 서버, 외부에서 접근해야 하는 진입점 서비스 |

---

## 8. 단독 Pod와 Deployment 간의 환경변수(env / envFrom) 전달 원리 및 비유

### 8.1 문제 의식: 왜 Deployment에서도 env 설정을 다시 적어주어야 하는가?
`kind-pod-docker.yaml`에서 이미 `todo-backend` Pod에 ConfigMap/Secret을 참조하는 `env:` 환경변수들을 정의해 두었는데, 왜 `kind-deployment-docker.yaml`의 Deployment에서도 동일한 `env` (또는 `envFrom`) 설정을 생략하지 않고 반드시 다시 명시해야 할까요?

---

### 8.2 쿠버네티스 내부 동작 메커니즘: 프로세스 격리와 설계도(Template)

```text
┌────────────────────────────────────────────────────────────────────────┐
│ [중앙 저장소 (데이터 원본)]                                            │
│   • ConfigMap: todo-config (MYSQL_HOST, MYSQL_DB, PORT 등)             │
│   • Secret: todo-db-secret (MYSQL_PASSWORD 등)                         │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
         (단독 Pod 스펙 참조)              (Deployment 템플릿 참조)
                   ▼                                 ▼
┌───────────────────────────────────┐ ┌──────────────────────────────────┐
│ [단독 Pod: todo-backend]           │ │ [Deployment: todo-backend]       │
│   • spec.containers.env 주입      │ │   • spec.template.spec           │
│   • 해당 컨테이너 메모리에만 존재   │ │     (새 Pod 생성용 독립 설계도) │
│   • 외부/타 Pod로 공유 절대 불가! │ └────────────────┬─────────────────┘
└───────────────────────────────────┘                  │
                                           (설계도 기반 독립 Pod 2개 생성)
                                                       ▼
                                      ┌──────────────────────────────────┐
                                      │ [Pod 1: todo-backend-xxx-1]      │
                                      │   • template의 env/envFrom 주입  │
                                      ├──────────────────────────────────┤
                                      │ [Pod 2: todo-backend-xxx-2]      │
                                      │   • template의 env/envFrom 주입  │
                                      └──────────────────────────────────┘
```

1. **Pod는 각각 완전히 독립된 격리 프로세스입니다**:
   - `kind-pod-docker.yaml`에서 설정한 `env:`는 해당 단독 Pod(`todo-backend`)의 컨테이너 내부 네임스페이스 및 메모리에만 국소적으로 주입됩니다.
   - 쿠버네티스 클러스터 차원에서 다른 리소스들이 참조할 수 있는 "전역 환경변수"로 공유되는 것이 아닙니다.

2. **Deployment는 기존 Pod를 재사용하지 않고 완전히 새로운 Pod들을 만듭니다**:
   - Deployment는 기존에 이미 떠 있는 단독 Pod를 가져다가 쓰는 것이 아닙니다.
   - Deployment는 자신의 **`spec.template.spec` 설계도**를 바탕으로 완전히 새로운 Pod 2개(`todo-backend-xxx-1`, `todo-backend-xxx-2`)를 백지 상태에서 독립적으로 생성합니다.

3. **환경변수 누락 시의 치명적 오류**:
   - 만약 Deployment의 `template`에 `env` (또는 `envFrom`)가 정의되어 있지 않다면, 새로 생성된 2개의 Pod는 `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD` 값을 전혀 전달받지 못합니다.
   - 그 결과, 백엔드 애플리케이션이 데이터베이스에 접속하지 못해 **`CrashLoopBackOff`** 오류를 내며 무한 재시작에 빠지게 됩니다.

---

### 8.3 일상 비유로 이해하기

* **`ConfigMap` / `Secret`** = **사내 인트라넷 게시판** (중앙에 보관된 공식 데이터 원본)
* **`Pod`** = 회사에 출근하여 일하는 **직원**
* **`env:`** = 출근한 직원의 책상 위에 놓아주는 **개인 업무 지시서**
* **`Deployment`의 `template`** = 신규 입사자 채용 시 전달하는 **표준 업무 매뉴얼**

> **핵심 비유**:  
> 기존에 일하던 직원 A(단독 Pod)의 책상에 업무 지시서(`env`)를 놓아주었다고 해서, 새로 채용한 신입 직원 B, C(Deployment가 관리하는 2개의 Pod) 책상에 그 지시서가 텔레파시처럼 자동으로 복사되지 않습니다.  
> 따라서 **새 직원들의 표준 업무 매뉴얼(`template.spec`)에도 반드시 지시서(`env` 또는 `envFrom`)를 명시**해주어야 모든 직원이 차질 없이 업무를 수행할 수 있습니다.

---

### 8.4 YAML 최적화 기법: `env` 개별 매핑 vs `envFrom` 일괄 주입

쿠버네티스에서는 20여 줄에 걸쳐 환경변수를 하나씩 나열하는 대신, **`envFrom`**을 사용하면 소스코드를 대폭 축약하고 유지보수성을 극대화할 수 있습니다:

#### 1) 기존 방식 (`env` 개별 매핑 - 20여 줄)
```yaml
          env:
            - name: MYSQL_HOST
              valueFrom:
                configMapKeyRef:
                  name: todo-config
                  key: MYSQL_HOST
            - name: MYSQL_USER
              valueFrom:
                configMapKeyRef:
                  name: todo-config
                  key: MYSQL_USER
            - name: MYSQL_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: todo-db-secret
                  key: MYSQL_PASSWORD
            # ... 계속 나열 ...
```

#### 2) 권장 최적화 방식 (`envFrom` 일괄 주입 - 단 5줄)
```yaml
          envFrom:
            - configMapRef:
                name: todo-config       # MYSQL_HOST, MYSQL_USER, MYSQL_DB, PORT 자동 일괄 주입
            - secretRef:
                name: todo-db-secret    # MYSQL_PASSWORD 등 Secret 키-값 자동 일괄 주입
```

* **동작 방식**: ConfigMap과 Secret에 정의된 모든 키 이름이 컨테이너의 환경변수 이름으로 1:1 자동 매핑됩니다.
* **장점**: YAML 파일의 길이가 획기적으로 줄어들며, ConfigMap/Secret에 새로운 설정값을 추가하더라도 Deployment 매니페스트를 매번 수정할 필요가 없습니다.

---

## 9. 로컬 Kind 클러스터와 Google Kubernetes Engine (GKE) 매니페스트 차이점 및 배포 가이드

### 9.1 배경 및 환경 비교

Kind(Kubernetes in Docker)와 GKE(Google Cloud Managed Kubernetes)는 동일한 표준 쿠버네티스 API를 사용하지만, **기반 인프라(스토리지 드라이버, 클라우드 로드밸런서, 네트워크 방화벽, 노드 격리)**가 근본적으로 다릅니다. 따라서 로컬 Kind용 매니페스트를 GKE에 그대로 배포할 경우 스토리지 프로비저닝 오류나 이미지 풀 실패가 발생할 수 있습니다.

| 비교 항목 | Kind (로컬 가상 클러스터) | GKE (구글 클라우드 매니지드 K8s) |
| :--- | :--- | :--- |
| **스토리지 (StorageClass)** | `rancher.io/local-path` (로컬 디스크) | **GCP Persistent Disk CSI (`standard-rwo`)** |
| **PVC 최소 용량** | **`1Gi`** 등 소규모 단위 자유 지원 | GCP Persistent Disk 특성상 **최소 `10Gi` 이상** 요구 |
| **LoadBalancer 서비스** | `cloud-provider-kind` 가상 데몬 필요 (가상 IP `127.0.0.1`) | **GCP Cloud Network Load Balancer** 자동 연동 (공인 IP 부여) |
| **NodePort 서비스** | `extraPortMappings` 포워딩으로 `localhost` 직통 | **GCP VPC 방화벽 규칙(`allow tcp:30080`)** 추가 개방 필수 |
| **컨테이너 이미지** | `kind load`로 로컬 도커 이미지를 노드에 직접 주입 가능 | 원격 VM이므로 **Docker Hub / Artifact Registry** 정규 원격 경로 필수 |
| **배포 전략** | 단발성 테스트 (Recreate 등) | 상용 무중단 배포 (**`RollingUpdate: maxSurge 1, maxUnavailable 0`**) |

---

### 9.2 주요 아키텍처별 상세 차이점

#### 1) 스토리지 (PVC & StorageClass)
* **문제점**: `kind-pod-docker.yaml`의 `todo-mysql-pvc`에 지정된 `1Gi`는 로컬 파일시스템 기반인 Kind에서는 잘 동작하지만, GKE의 기본 영구 디스크(`standard-rwo`)는 1Gi 요청 시 프로비저닝에 실패하거나 성능 제약이 발생합니다.
* **GKE 해결책**: 
  ```yaml
  spec:
    storageClassName: standard-rwo   # GKE 기본 CSI 스토리지 클래스 (pd-balanced) 명시
    resources:
      requests:
        storage: 10Gi                # GKE Persistent Disk 최소 권장 크기 (10Gi)
  ```

#### 2) 서비스 (LoadBalancer & NodePort)
* **LoadBalancer**: GKE에서는 `type: LoadBalancer`를 선언하면 Google Cloud가 외부 통신용 패스스루 네트워크 로드밸런서를 생성하고 고유 공인 IP를 매핑합니다. 이때 클라이언트의 실제 IP를 보존하고 노드 간 불필요한 라우팅 홉을 방지하기 위해 **`externalTrafficPolicy: Local`**을 설정하는 것이 모범 사례입니다.
* **NodePort**: `nodePort: 30080`을 사용할 경우, GCP 콘솔 또는 CLI에서 방화벽 규칙을 추가해야 노드의 외부 IP를 통해 30080 포트로 접속할 수 있습니다:
  ```bash
  gcloud compute firewall-rules create allow-todo-nodeport-30080 \
      --allow tcp:30080 \
      --description="Allow Todo App NodePort 30080"
  ```

#### 3) 이미지 레지스트리 (Local vs Remote)
* **문제점**: `kind-pod-local.yaml`의 `image: todo-backend`는 `kind load`로 로컬 컨테이너 노드에 이미지를 주입했기 때문에 동작한 방식입니다. GKE 노드는 원격 클라우드에 있으므로 로컬 컴퓨터의 이미지를 알지 못해 `ErrImagePull` 에러가 발생합니다.
* **GKE 해결책**: Docker Hub(`ssucloud/getting-started-todo-app:todo-backend`) 또는 Google Artifact Registry(`[REGION]-docker.pkg.dev/[PROJECT_ID]/[REPO]/todo-backend:prod`)의 정규 주소를 사용해야 합니다.

#### 4) 무중단 롤링 업데이트 전략
* GKE 운영 환경에서는 애플리케이션 업데이트 중에도 서비스 다운타임(0초)을 유지하기 위해 Deployment에 롤링 업데이트 전략을 명시합니다:
  ```yaml
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # 업데이트 중 추가 생성 가능한 최대 파드 수
      maxUnavailable: 0    # 업데이트 중 다운될 수 있는 최대 파드 수 (0 = 무중단 보장)
  ```

---

### 9.3 GKE 전용 신규 매니페스트 목록 (`GKE-*.yaml`)

GKE 환경에 즉시 배포할 수 있도록 최적화된 매니페스트 파일 목록입니다:

1. **[GKE-deployment-docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-deployment-docker.yaml)**:
   * `replicas: 2`, `envFrom` 일괄 주입 최적화
   * 무중단 배포를 위한 `RollingUpdate (maxSurge: 1, maxUnavailable: 0)` 전략 적용
2. **[GKE-service-lb.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-lb.yaml)**:
   * GCP Network Load Balancer 연동 및 `externalTrafficPolicy: Local` 적용
3. **[GKE-service-np.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-service-np.yaml)**:
   * GKE 환경의 NodePort `30080` 포트 개방 및 GCP VPC 방화벽 규칙 가이드 명시
4. **[GKE-pod-docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-docker.yaml)**:
   * GKE CSI 영구 디스크 스토리지(`standard-rwo`, 10Gi) 및 `envFrom` 적용
5. **[GKE-pod-local.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-pod-local.yaml)**:
   * 로컬 이미지 대신 원격 Docker Hub 이미지 및 10Gi CSI 스토리지 적용
6. **[GKE-replicaset-docker.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-replicaset-docker.yaml)**:
   * GKE 10Gi 스토리지 및 2개 복제본 ReplicaSet 구성

*(참고: [kind-service-cip.yaml](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/kind-service-cip.yaml)은 순수 내부용 `ClusterIP`이므로 Kind와 GKE에서 완전히 동일하게 동작합니다)*

---

### 9.4 GCP Artifact Registry 생성 및 이미지 푸시 워크플로우

GKE 클러스터에 배포할 컨테이너 이미지를 관리하기 위해 Google Cloud의 표준 컨테이너 저장소인 **Artifact Registry**를 구축하고 이미지를 태깅/푸시하는 상세 가이드는 별도 문서인 **[GKE-Workflow.md](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-Workflow.md)**에 상세히 정리되어 있습니다.

#### 주요 설정 요약:
* **GCP Project**: `ssu-agent-vertex-509708`
* **Region**: `asia-northeast3` (Seoul)
* **Repository**: `my-repo` (Docker 포맷)
* **Target Image Path**: `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod`
* **상세 가이드**: [GKE-Workflow.md](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-Workflow.md) 참고




