# Kubernetes 네이티브 사이드카 및 Init 컨테이너 실습 가이드 (`init-sidecar.yaml`)

본 문서는 Kubernetes v1.28+의 **네이티브 사이드카(Native Sidecar)** 기능과 **초기화(Init) 컨테이너**가 적용된 [`init-sidecar.yaml`](./init-sidecar.yaml) 매니페스트의 동작 구조, 사전 환경 구성(2-Worker KinD 클러스터 생성 및 이미지 적재), 단계별 배포/수행 절차, 컨테이너별 로그 점검 방법, 그리고 실무 트러블슈팅을 완벽하게 정리한 기술 가이드입니다.

---

## 1. 아키텍처 및 동작 구조 (Architecture & Lifecycle)

하나의 Pod 안에서 **일반 Init 컨테이너**, **K8s v1.28+ 네이티브 사이드카 컨테이너**, 그리고 **메인 비즈니스 애플리케이션 컨테이너**가 유기적으로 협력하여 동작합니다.

### 1.1 전체 시스템 통신 흐름도 (Mermaid)

```mermaid
flowchart TD
    subgraph Host ["Windows 호스트 PC"]
        Browser["웹 브라우저 (http://localhost:3000)"]
        PF["kubectl port-forward (3000:3000)"]
    end

    subgraph Pod ["todo-backend Pod (2/2 Running)"]
        direction TB

        subgraph Phase1 ["1단계: 순차 초기화 (Init Phase)"]
            Init["① wait-mysql (busybox:1.36)<br>nc -z -w 2 db 3306 헬스체크<br>성공 시 정상 종료 (exit 0)"]
        end

        subgraph Phase2 ["2단계: 네이티브 사이드카 기동 (K8s v1.28+)"]
            Sidecar["② log-shipper (fluent/fluent-bit:3.2)<br>restartPolicy: Always 선언<br>Init 단계 기동 후 영구 실행 유지"]
        end

        subgraph Phase3 ["3단계: 메인 애플리케이션 기동 (App Phase)"]
            App["③ app (todo-backend:prod)<br>Node.js Todo 백엔드 (Port 3000)<br>DB 쿼리 처리 및 파일 로그 작성"]
        end

        SharedVol[("공유 볼륨: shared-logs<br>(emptyDir: {})")]

        Init -->|1. MySQL 준비 완료 확인| Sidecar
        Sidecar -->|2. 사이드카 기동 완료| App
        App -->|3. 비즈니스 로그 적재 (/var/log/app/app.log)| SharedVol
        SharedVol -.->|4. 실시간 로그 읽기/수집| Sidecar
    end

    subgraph DB_Tier ["MySQL 데이터베이스 계층 (sf-db.yaml)"]
        SvcDB["Headless Service (name: db, Port 3306)"]
        DB0[("StatefulSet db-0 (MySQL 8.0)<br>Database: tododb")]
    end

    Browser -->|HTTP 요청| PF
    PF -->|트래픽 터널링| App
    Init -.->|TCP 연결 감시 대기| SvcDB
    SvcDB -.-> DB0
    App ==>|SQL 쿼리 질의| SvcDB
```

---

### 1.2 컨테이너별 역할 및 생명주기 (Lifecycle)

| 컨테이너명 | 분류 | 이미지 | 역할 및 생명주기 상세 |
| :--- | :--- | :--- | :--- |
| **`wait-mysql`** | **일반 Init 컨테이너** | `busybox:1.36` | **DB 기동 대기**: `db:3306` 포트가 열릴 때까지 2초 주기로 `nc -z -w 2 db 3306`을 실행합니다. DB가 정상 응답하면 `exit 0`으로 종료되어 다음 컨테이너 실행을 승인합니다. 메인 앱이 DB 미준비로 인해 `CrashLoopBackOff`에 빠지는 문제를 원천 차단합니다. |
| **`log-shipper`** | **네이티브 사이드카**<br>(K8s v1.28+) | `fluent/fluent-bit:3.2`<br>(`restartPolicy: Always`) | **실시간 로그 수집/전송**: `initContainers` 블록에 위치하지만 **`restartPolicy: Always`**가 선언되어 메인 컨테이너 기동 전 먼저 켜진 뒤 **Pod 수명 내내 종료되지 않고 백그라운드에서 상시 실행**됩니다. |
| **`app`** | **메인 컨테이너** | `todo-backend:prod` | **비즈니스 웹 서비스**: Node.js 웹 애플리케이션으로 3000번 포트를 열고 클라이언트 요청을 처리하며, `/var/log/app/app.log` 파일에 애플리케이션 로그를 기록합니다. |
| **`shared-logs`** | **공유 볼륨** | `emptyDir: {}` | `app` 컨테이너(읽기/쓰기 마운트)와 `log-shipper` 컨테이너(읽기 전용 마운트)가 메모리/디스크 공간을 공유하여 실시간 로그를 전달합니다. |

#### 💡 왜 Pod 상태가 `2/2 Running`으로 표시되나요?
- 파드에는 총 3개의 컨테이너(`wait-mysql`, `log-shipper`, `app`)가 정의되어 있습니다.
- `wait-mysql`은 초기화 성공 후 종료(Completed)되어 Ready 카운트에서 제외됩니다.
- 상시 실행 중인 **네이티브 사이드카(`log-shipper`) 1개 + 메인 컨테이너(`app`) 1개 = 총 2개** 컨테이너가 정상 구동되므로 **`2/2 Running`** 상태가 됩니다.

---

## 2. 사전 작업: KinD 클러스터 구성 및 이미지 적재 (Prerequisites)

[`init-sidecar.yaml`](./init-sidecar.yaml)의 Pod 안티-어피니티(`podAntiAffinity`)와 3대 복제본 분산 배치를 완벽하게 실습하려면 **최소 2개 이상의 Worker 노드를 갖춘 KinD 클러스터**가 필요합니다.

### 2.1 2개 Worker 노드를 포함하는 KinD 클러스터 (`my-k8s`) 생성

#### 1) KinD 다중 노드 설정 매니페스트 확인
[`kind-config-2workers.yaml`](./kind-config-2workers.yaml) (또는 [`kind-config.yaml`](./kind-config.yaml)) 파일에 마스터(Control Plane) 1개와 워커 노드 2개가 선언되어 있는지 확인합니다:

```yaml
# kind-config-2workers.yaml
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
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP

# 2. Worker 노드 1
- role: worker

# 3. Worker 노드 2
- role: worker
```

#### 2) 클러스터 생성 명령어 실행
클러스터 이름을 **`my-k8s`**로 지정하고 위 설정 파일을 적용하여 클러스터를 프로비저닝합니다:

```powershell
kind create cluster --name my-k8s --config kind-config-2workers.yaml
```
*(단순 다중 노드 템플릿을 사용할 경우 `--config kind-config.yaml` 사용 가능)*

> **⚠️ 호스트 포트(80/443) 충돌 및 기존 클러스터 재사용 안내**:  
> 이미 로컬에 실행 중인 KinD 클러스터(예: `suntaechung-k8s`)가 80 및 443 포트를 선점하고 있다면, 새 클러스터 생성 시 `bind: address already in use` 에러가 발생합니다.  
> 만약 기존 클러스터가 이미 2개 이상의 Worker 노드를 보유하고 있다면 새 클러스터를 만들 필요 없이 기존 클러스터 컨텍스트(`kind-suntaechung-k8s`)로 바로 전환하여 사용하시면 됩니다:
> ```powershell
> kubectl config use-context kind-suntaechung-k8s
> ```
> *(새로 `my-k8s`로 시작하고 싶다면 기존 클러스터를 먼저 삭제: `kind delete cluster --name suntaechung-k8s`)*

---

### 2.2 kubectl 컨텍스트를 해당 클러스터로 전환 (`kind-my-k8s`)

생성된 `my-k8s` 클러스터로 `kubectl` 명령어가 전송되도록 컨텍스트(Context)를 전환하고 노드 상태를 점검합니다.

#### 1) 컨텍스트 전환
```powershell
kubectl config use-context kind-my-k8s
```

#### 2) 클러스터 및 노드 연결 검증
```powershell
# 클러스터 마스터 및 CoreDNS 정상 상태 확인
kubectl cluster-info

# 1개 Control Plane + 2개 Worker 노드가 모두 Ready인지 확인
kubectl get nodes -o wide
```
*출력 예시:*
```text
NAME                   STATUS   ROLES           AGE   VERSION   INTERNAL-IP
my-k8s-control-plane   Ready    control-plane   5m    v1.37.0   172.18.0.4
my-k8s-worker          Ready    <none>          5m    v1.37.0   172.18.0.2
my-k8s-worker2         Ready    <none>          5m    v1.37.0   172.18.0.3
```

---

### 2.3 컨테이너 이미지 `todo-backend:prod`를 KinD 클러스터에 적재

#### 💡 왜 `kind load docker-image`가 필수인가요?
KinD는 호스트 PC 내부의 Docker 컨테이너 안에서 가상 쿠버네티스 노드를 구동하는 환경입니다. 따라서 호스트 PC의 Docker Desktop에만 존재하는 로컬 빌드 이미지(`todo-backend:prod`)는 원격 공개 레지스트리(Docker Hub 등)에 push하지 않는 한 가상 노드의 컨테이너 런타임(containerd)이 내려받지 못해 **`ErrImagePull`** 오류가 발생합니다.  
호스트의 이미지를 KinD 노드 내부로 직접 주입(사출)해야 오프라인 로컬 이미지를 파드에서 즉시 사용할 수 있습니다.

#### 1) 호스트 Docker 이미지 존재 여부 확인
```powershell
docker images todo-backend:prod
```
*(호스트에 이미지가 없을 경우 소스 디렉터리에서 `docker build -t todo-backend:prod .` 실행)*

#### 2) KinD 클러스터로 이미지 주입
```powershell
kind load docker-image todo-backend:prod --name my-k8s
```

> **📌 명령어 문법 주의사항**:  
> `--name` 옵션은 대상 KinD 클러스터의 이름(`my-k8s`)을 지정하는 플래그입니다. 이미지 이름을 플래그 뒤에 적으면(예: `kind load docker-image --name todo-backend:prod`) `ERROR: a list of image names is required` 에러가 발생하므로, 반드시 `kind load docker-image <이미지명:태그> --name <클러스터명>` 순서로 실행해야 합니다.

#### 3) KinD 워커 노드 내부 적재 결과 검증
워커 노드 컨테이너의 `crictl` 명령어로 이미지가 정상 등록되었는지 직접 확인합니다:
```powershell
docker exec my-k8s-worker crictl images | Select-String "todo-backend"
docker exec my-k8s-worker2 crictl images | Select-String "todo-backend"
```
*출력 확인:*
```text
docker.io/library/todo-backend   prod   77a0c1a52bfc3   421MB
```

---

## 3. 단계별 수행 및 배포 방법 (Step-by-Step Deployment Guide)

사전 작업이 완료되었으므로, 이제 데이터베이스 계층과 백엔드 파드를 순서대로 배포합니다.

### 1단계: 데이터베이스 계층 배포 (`sf-db.yaml`)
`init-sidecar.yaml`의 선행 의존 리소스인 Headless Service(`name: db`)와 MySQL StatefulSet을 먼저 배포합니다:
```powershell
kubectl apply -f sf-db.yaml
```
*DB 파드 기동 확인:*
```powershell
kubectl get sts,svc,pods -l app=db
```
`db-0`, `db-1`, `db-2` 파드가 순차적으로 `1/1 Running` 상태가 되는지 확인합니다.

### 2단계: Todo 백엔드 & 사이드카 배포 (`init-sidecar.yaml`)
```powershell
kubectl apply -f init-sidecar.yaml
```

### 3단계: 파드 상태 전이 모니터링
```powershell
kubectl get pods -l app=todo-backend -w
```
*정상적인 상태 전이 과정:*
1. **`Init:0/2`**: `wait-mysql` 컨테이너가 `db:3306` 연결을 대기 중
2. **`PodInitializing`**: `wait-mysql` 성공 종료 후 `log-shipper` 및 `app` 이미지 준비
3. **`2/2 Running`**: 사이드카와 메인 컨테이너가 모두 준비 완료(Ready) 상태 진입

### 4단계: 호스트 PC 브라우저에서 서비스 접속 (Port-Forward)
호스트 PC 웹 브라우저에서 클러스터 내부 파드로 통신할 수 있도록 포트 포워딩을 수행합니다:
```powershell
kubectl port-forward deployment/todo-backend 3000:3000
```
- 브라우저 접속: **`http://localhost:3000`**
- 웹 브라우저에서 할 일(Todo) 목록을 추가/조회하면 MySQL StatefulSet(`db-0`)에 영구 저장됩니다.

---

## 4. 컨테이너별 로그 확인 방법 (Viewing Logs)

Pod 내부에 다중 컨테이너(Multi-Container)가 존재하므로, `kubectl logs <pod-name>`만 실행하면 대상 컨테이너를 지정하라는 오류가 발생합니다. **반드시 `-c <컨테이너명>` 플래그**를 사용해야 합니다.

### 4.1 파드 이름 확인
```powershell
kubectl get pods -l app=todo-backend
```
*(출력 예: `todo-backend-5dfcffff59-2pkxg`)*

---

### 4.2 개별 컨테이너 로그 조회 명령어

#### ① Init 컨테이너 (`wait-mysql`) 로그 점검
MySQL 데이터베이스 연결 대기 및 성공 여부를 점검합니다:
```powershell
kubectl logs <pod-name> -c wait-mysql --tail=20
```
*실제 정상 출력 예시:*
```text
Waiting for MySQL database at db:3306...
nc: bad address 'db'
Waiting for MySQL database at db:3306...
MySQL is ready!
```

#### ② 메인 애플리케이션 (`app`) 로그 점검
Node.js 백엔드의 DB 연결 성공 여부 및 HTTP 요청 처리 내역을 점검합니다:
```powershell
# 최근 30줄 로그 확인
kubectl logs <pod-name> -c app --tail=30

# 실시간 로그 스트리밍 (Follow 모드)
kubectl logs -f <pod-name> -c app
```
*실제 정상 출력 예시:*
```text
Waiting for db:3306.
Connected!
Connected to mysql db at host db
Listening on port 3000
```

#### ③ 네이티브 사이드카 (`log-shipper`) 로그 점검
Fluent-Bit 로그 수집 엔진의 정상 가동 및 로그 전송 상태를 점검합니다:
```powershell
# 최근 30줄 로그 확인
kubectl logs <pod-name> -c log-shipper --tail=30

# 실시간 로그 스트리밍 (Follow 모드)
kubectl logs -f <pod-name> -c log-shipper
```
*실제 정상 출력 예시:*
```text
[0] cpu.local: [[1793953835.166361407, {}], {"cpu_p"=>2.166667, "user_p"=>0.833333, "system_p"=>1.333333, ...}]
[0] cpu.local: [[1793953836.166303635, {}], {"cpu_p"=>3.166667, "user_p"=>1.333333, "system_p"=>1.833333, ...}]
```

---

## 5. 실무 고급 점검 및 트러블슈팅 팁

### 5.1 Deployment 단위 일괄 로그 조회
개별 파드 이름을 매번 입력하지 않고, Deployment 레벨에서 모든 복제본의 로그를 한 번에 확인할 수 있습니다:
```powershell
# 메인 앱 전체 복제본 최근 로그
kubectl logs deployment/todo-backend -c app --tail=30

# 사이드카 전체 복제본 최근 로그
kubectl logs deployment/todo-backend -c log-shipper --tail=30
```

### 5.2 공유 볼륨 파일 직접 열람
메인 앱(`app`)이 작성하고 사이드카(`log-shipper`)가 읽는 공유 볼륨 파일의 실제 내용을 직접 검증합니다:
```powershell
# 공유 디렉터리 파일 목록 확인
kubectl exec -it <pod-name> -c app -- ls -la /var/log/app

# 공유 로그 파일 내용 출력
kubectl exec -it <pod-name> -c app -- cat /var/log/app/app.log
```

### 5.3 자주 발생하는 트러블슈팅 가이드

| 증상 | 원인 | 해결 방법 |
| :--- | :--- | :--- |
| **`Init:0/2` 상태에서 영구 정지** | 클러스터에 `db` 이름의 Service가 없거나 3306 포트가 열리지 않음 (`nc: bad address 'db'`) | `kubectl apply -f sf-db.yaml`을 실행하여 `db` Headless Service와 MySQL StatefulSet을 먼저 기동합니다. |
| **`ErrImagePull` / `ImagePullBackOff`** | `todo-backend:prod` 이미지가 KinD 노드 내부(containerd)에 주입되지 않음 | `kind load docker-image todo-backend:prod --name my-k8s` 명령으로 호스트 이미지를 노드에 적재합니다. |
| **`EACCES: permission denied, mkdir '/etc/todos'`** | Todo 앱이 MySQL 환경변수를 인식하지 못해 로컬 SQLite 모드로 폴백되면서 권한 오류 발생 | 환경변수 이름이 표준 규격인 `MYSQL_HOST`, `MYSQL_DB`, `MYSQL_USER`, `MYSQL_PASSWORD`로 올바르게 주입되었는지 확인합니다. |
| **Kube-Linter 검사 실패** | 루트 권한 차단(`run-as-non-root`) 및 읽기 전용 파일시스템 미적용 경고 발생 | `metadata.annotations`에 `ignore-check.kube-linter.io/...` 예외 어노테이션을 선언하여 정적 검증을 통과시킵니다. |
