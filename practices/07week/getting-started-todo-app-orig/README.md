# Getting Started Todo App

This project provides a sample todo list application. It demonstrates all of
the current Docker best practices, ranging from the Compose file, to the
Dockerfile, to CI (using GitHub Actions), and running tests. It's intended to 
be well-documented to ensure anyone can come in and easily learn.

## Application architecture

![image](https://github.com/docker/getting-started-todo-app/assets/313480/c128b8e4-366f-4b6f-ad73-08e6652b7c4d)


This sample application is a simple React frontend that receives data from a
Node.js backend. 

When the application is packaged and shipped, the frontend is compiled into
static HTML, CSS, and JS and then bundled with the backend where it is then
served as static assets. So no... there is no server-side rendering going on
with this sample app.

During development, since the backend and frontend need different dev tools, 
they are split into two separate services. This allows [Vite](https://vitejs.dev/) 
to manage the React app while [nodemon](https://nodemon.io/) works with the 
backend. With containers, it's easy to separate the development needs!

## Development

To spin up the project, simply install Docker Desktop and then run the following 
commands:

```
git clone https://github.com/docker/getting-started-todo-app
cd getting-started-todo-app
docker compose up --watch
```

You'll see several container images get downloaded from Docker Hub and, after a
moment, the application will be up and running! No need to install or configure
anything on your machine!

Simply open to [http://localhost](http://localhost) to see the app up and running!

Any changes made to either the backend or frontend should be seen immediately
without needing to rebuild or restart the containers.

To help with the database, the development stack also includes phpMyAdmin, which
can be accessed at [http://db.localhost](http://db.localhost) (most browsers will 
resolve `*.localhost` correctly, so no hosts file changes should be required).

### Tearing it down

When you're done, simply remove the containers by running the following command:

```
docker compose down
```

---

## Kubernetes & Helm Chart (Katenary 기반 개발 및 배포)

이 프로젝트는 [Katenary](https://github.com/Katenary/katenary) 도구를 활용하여 환경별 Docker Compose 설정을 쿠버네티스용 **Helm Chart**로 자동 변환하고 배포할 수 있습니다. (Katenary 상세 사용법 및 라벨 레퍼런스는 [Katenary-README-KR.md](Katenary-README-KR.md) 참조)

### 📌 환경별 프로젝트 구성 요약

| 환경 (Environment) | 소스 Compose 파일 | 생성된 Helm Chart 폴더 | 대상 클러스터 및 이미지 | 상세 배포 가이드 |
|---|---|---|---|---|
| **로컬 KIND (Local)** | `compose-local_kind.yaml` | `charts/getting-started-todo-app.local_kind` | 로컬 KIND (`todo-backend:prod`) | [README-local_kind.md](charts/getting-started-todo-app.local_kind/README-local_kind.md) |
| **GitHub Packages (GHCR)** | `compose-github_kind.yaml` | `charts/getting-started-todo-app.github_kind` | KIND / 원격 GHCR (`ghcr.io/...`) | [README-github_kind.md](charts/getting-started-todo-app.github_kind/README-github_kind.md) |
| **GCP Artifact Registry / GKE** | `compose-gcp_gke.yaml` | `charts/getting-started-todo-app.gcp_gke` | GKE / GCP Artifact Registry (`asia-northeast3-docker.pkg.dev/...`) | [README-gcp_gke.md](charts/getting-started-todo-app.gcp_gke/README-gcp_gke.md) |

```text
+------------------------------------+        katenary convert        +-----------------------------------------------+
|  환경별 Docker Compose 파일        |  ===========================>  |  charts/                                      |
|  - compose-local_kind.yaml (로컬)  |                                |  ├── getting-started-todo-app.local_kind      |
|  - compose-github_kind.yaml (GHCR) |                                |  ├── getting-started-todo-app.github_kind     |
|  - compose-gcp_gke.yaml (GCP/GKE)  |                                |  └── getting-started-todo-app.gcp_gke         |
+------------------------------------+                                +-----------------------------------------------+
                                                                              ||
                                                                              || helm install / upgrade
                                                                              \/
                                                              +-----------------------------------------------+
                                                              |  Kubernetes (KIND / GKE 클러스터)             |
                                                              |  - backend (Pod / Service)                    |
                                                              |  - mysql (Pod / SVC / PVC)                    |
                                                              +-----------------------------------------------+
```

---

### 1. 사전 준비 (Prerequisites)

1. **Katenary 설치 및 경로 설정 (Windows)**:
   - 프로젝트 루트 디렉터리에 `katenary.exe`가 포함되어 있거나, 설치 디렉터리(예: `C:\Users\<USER>\AppData\Local\Katenary`)를 시스템 환경 변수 `Path`에 추가합니다.
   - 현재 열려 있는 터미널에서 즉시 적용할 경우:
     - **PowerShell**:
       ```powershell
       $env:Path += ";$env:LOCALAPPDATA\Katenary"
       katenary version
       ```
     - **Git Bash**:
       ```bash
       export PATH="$PATH:/c/Users/$USER/AppData/Local/Katenary"
       katenary version
       ```

2. **Compose 파일 내 백엔드 및 서비스 상세 설정 (핵심 분석)**:

   `compose-local_kind.yaml`에서 Katenary 변환 및 쿠버네티스 운영을 위해 적용된 핵심 설정 내역입니다:

   ```yaml
   services:
     # 1) 로컬 개발용 프록시: 쿠버네티스 변환 제외
     proxy:
       image: traefik:v3.6
       command:
         - "--providers.docker=true"
         - "--entrypoints.web.address=:80"
         - "--entrypoints.websecure.address=:443"
       ports:
         - 80:80
         - 443:443
       volumes:
         - /var/run/docker.sock:/var/run/docker.sock
       labels:
         katenary.v3/ignore: "true"   # Katenary 변환 시 차트 생성 제외

     # 2) 백엔드 프로덕션 서비스: 프론트엔드 번들 + API
     backend:
       image: todo-backend:prod       # 빌드 및 쿠버네티스 로드 시 사용할 이미지 태그
       build:
         context: ./
         target: final                # React 프론트엔드 정적 빌드와 Express API가 번들링된 최종 스테이지
       ports:
         - 3000:3000                  # 쿠버네티스 Service(ClusterIP) 생성을 위한 필수 포트 선언
       expose:
         - 3000
       environment:
         MYSQL_HOST: mysql            # 로컬 Compose 통신용 기본 DB 호스트명
         MYSQL_USER: root
         MYSQL_PASSWORD: secret
         MYSQL_DB: todos    
       depends_on:
         mysql:
           condition: service_healthy # Katenary가 이를 분석하여 wait-for-mysql InitContainer 자동 구성
       labels:
         # [Katenary 환경변수 동적 매핑]
         # 쿠버네티스에서는 Helm 릴리스명에 따라 MySQL 서비스명이 동적으로 결정되므로
         # ConfigMap 내 MYSQL_HOST 값을 Helm 템플릿 문법으로 치환하여 서비스 간 DNS 통신을 보장합니다.
         katenary.v3/map-env: |-
           MYSQL_HOST: '{{ include "__APP__.fullname" . }}-mysql'

         # [Docker Compose 로컬 전용 Traefik 라우팅 라벨]
         # Katenary 변환 시에는 무시되며, 로컬 docker compose up 실행 시 HTTP(80)/HTTPS(443) 프록시 라우팅을 지원합니다.
         traefik.enable: "true"
         traefik.http.routers.backend-http.entrypoints: "web"
         traefik.http.routers.backend-http.rule: "PathPrefix(`/`)"
         traefik.http.routers.backend-http.service: "backend-service"
         traefik.http.routers.backend-https.entrypoints: "websecure"
         traefik.http.routers.backend-https.rule: "PathPrefix(`/`)"
         traefik.http.routers.backend-https.tls: "true"
         traefik.http.routers.backend-https.service: "backend-service"
         traefik.http.services.backend-service.loadbalancer.server.port: "3000"

     # 3) MySQL 데이터베이스 서비스
     mysql:
       image: mysql:9.3
       ports:
         - 3306:3306
       expose:
         - 3306
       volumes:
         - todo-mysql-data:/var/lib/mysql
       environment: 
         MYSQL_ROOT_PASSWORD: secret
         MYSQL_DATABASE: todos
       healthcheck:
         test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
         interval: 5s
         timeout: 5s
         retries: 5
   ```

   #### 🔍 설정 세부 해설:
   - **`target: final` & `image: todo-backend:prod`**:
     - `Dockerfile`의 멀티스테이지 빌드를 통해 React 빌드 산출물(`dist`)을 Express 백엔드의 정적 경로(`src/static`)로 복사한 단일 프로덕션 이미지입니다.
     - `image:` 속성을 명시하여 `kind load docker-image todo-backend:prod --name my-k8s` 시 일치하는 태그로 원활하게 클러스터에 주입할 수 있습니다.
   - **`ports` / `expose: 3000` (쿠버네티스 Service 생성)**:
     - Katenary는 Compose 서비스에 명시적인 포트가 정의되어 있지 않으면 쿠버네티스 `Service` 매니페스트를 생성하지 않습니다.
     - `ports: - 3000:3000` 선언을 통해 Helm 변환 시 `templates/backend/service.yaml` (ClusterIP, port 3000)이 정상 생성되어 외부 포트포워딩 및 파드 간 연결이 가능해집니다.
   - **`katenary.v3/map-env` (쿠버네티스 서비스 DNS 동적 바인딩)**:
     - Docker Compose 환경에서는 `MYSQL_HOST: mysql`로 통신하지만, 쿠버네티스에서는 Helm 릴리스 이름에 따라 MySQL 서비스의 실제 FQDN이 `<ReleaseName>-getting-started-todo-app-mysql` 형태로 지정됩니다.
     - `map-env` 라벨을 적용하면 Katenary가 생성하는 `backend` ConfigMap 내 `MYSQL_HOST` 값이 Helm 템플릿(`'{{ include "<chart>.fullname" . }}-mysql'`)으로 변환되어 DB 연결 실패(`ECONNREFUSED`)를 완벽히 예방합니다.
   - **`depends_on` 과 InitContainer**:
     - `mysql` 서비스의 `condition: service_healthy` 의존성을 인식하여, Katenary가 백엔드 Deployment 템플릿에 `busybox` 기반의 `wait-for-mysql` InitContainer를 자동 생성합니다. 이를 통해 MySQL 포트(3306)가 정상 응답할 때까지 대기 후 백엔드 메인 컨테이너가 안전하게 기동됩니다.
   - **`katenary.v3/ignore: "true"` (`proxy` 배포 제외)**:
     - 로컬 개발 시에는 프론트엔드 Vite 서버와 백엔드 API를 묶어주기 위해 Traefik 프록시가 필요했지만, 프로덕션에서는 백엔드가 단독으로 프론트엔드를 서빙합니다.
     - 또한 Traefik의 도커 소켓(`/var/run/docker.sock`)은 일반 쿠버네티스 파드에 마운트할 수 없으므로, `ignore` 라벨을 붙여 불필요한 매니페스트 생성을 방지합니다.

---

### 2. Helm 차트 생성 (Katenary Convert)

아래 명령어를 실행하여 로컬용 Docker Compose 설정을 Helm 차트로 변환합니다:

```bash
katenary convert -c compose-local_kind.yaml -o charts/getting-started-todo-app.local_kind -a 1.0.0 -v 0.1.0 -f
```

- **옵션 설명**:
  - `-c compose-local_kind.yaml`: 변환할 소스 Compose 파일 지정
  - `-o charts/getting-started-todo-app.local_kind`: 생성될 Helm Chart 출력 경로
  - `-a 1.0.0`: `Chart.yaml` 내 `appVersion` (애플리케이션 버전)
  - `-v 0.1.0`: `Chart.yaml` 내 `version` (차트 버전)
  - `-f`: 기존 출력 디렉터리 덮어쓰기 강제

#### 생성되는 차트 디렉터리 구조:
```text
charts/getting-started-todo-app.local_kind/
├── Chart.yaml              # 차트 메타데이터 (이름, 버전, appVersion)
├── README-local_kind.md    # 로컬 Kind 클러스터 배포 안내 문서
├── values.yaml             # 서비스별 기본 구성 값 (레플리카, 이미지 등)
└── templates/              # 쿠버네티스 리소스 매니페스트 템플릿
    ├── _helpers.tpl        # 네이밍 헬퍼 템플릿
    ├── backend/            # Express + Frontend 번들 서비스 (Deployment, Service, ConfigMap)
    └── mysql/              # MySQL DB (Deployment, Service, PVC, ConfigMap)
```

---

### 3. 차트 검증 및 시뮬레이션 (Dry-Run)

실제 배포 전 템플릿 구문 및 렌더링을 사전에 검증합니다.

1. **차트 문법 검사 (Lint)**:
   ```bash
   helm lint charts/getting-started-todo-app.local_kind
   ```
   *(출력 결과 `0 chart(s) failed` 확인)*

2. **렌더링된 매니페스트 확인 (Template)**:
   ```bash
   helm template todo-app charts/getting-started-todo-app.local_kind
   ```

3. **클러스터 가상 배포 시뮬레이션 (Dry-Run)**:
   ```bash
   helm install todo-app charts/getting-started-todo-app.local_kind --dry-run
   ```

---

### 4. KIND 클러스터에 배포 (Install)

로컬 Kubernetes(KIND) 클러스터에 애플리케이션을 배포합니다. 프로젝트 루트의 `kind-config-2workers.yaml`을 사용하여 Control-Plane 1대와 Worker 노드 2대로 구성된 `my-k8s` 클러스터를 준비합니다:

```bash
# KIND 클러스터 생성 (Worker 노드 2개 구성)
kind create cluster --name my-k8s --config kind-config-2workers.yaml

# 클러스터 노드 확인
kubectl get nodes
```

1. **로컬 이미지 빌드 및 KIND 클러스터로 로드**:
   - `backend` 서비스는 프로덕션 타깃(`final`) 이미지를 사용합니다:
     ```bash
     # 1. 프로덕션 이미지 빌드
     docker build -t todo-backend:prod --target final .

     # 2. KIND 클러스터(my-k8s)로 이미지 전달
     kind load docker-image todo-backend:prod --name my-k8s
     ```

2. **Helm 차트 배포 실행**:
   ```bash
   # 기본 values.yaml을 사용하여 배포
   helm install todo-app charts/getting-started-todo-app.local_kind

   # (선택) 사용자 정의 my-values.yaml을 적용하여 배포하는 경우
   helm install todo-app charts/getting-started-todo-app.local_kind -f my-values.yaml
   ```

3. **배포 상태 확인**:
   ```bash
   # Helm 릴리스 목록 확인
   helm list

   # Pod, Service, PVC 기동 상태 확인
   kubectl get pods,svc,pvc
   ```
   > **Note**: `backend` 파드는 `wait-for-mysql` 초기화 컨테이너(InitContainer)가 포함되어 있어, MySQL 데이터베이스가 완전히 준비된 후 자동으로 메인 컨테이너가 시작됩니다.

---

### 5. 웹 애플리케이션 접속 (접속 URL 확인 방법)

기본적으로 Helm 차트가 생성한 백엔드 Service는 클러스터 내부용인 **`ClusterIP`** 타입이므로, 접속 URL을 얻는 방법은 환경에 따라 두 가지가 있습니다:

#### 방법 A. 로컬 포트포워딩(Port-forward)으로 접속 (KIND / 로컬 개발 권장)
클러스터 내부의 백엔드 서비스를 로컬 PC의 포트로 포워딩합니다:

```bash
kubectl port-forward svc/todo-app-getting-started-todo-app-backend 8080:3000
```

- **접속 URL**: **[http://localhost:8080](http://localhost:8080)**  
  *(임의의 로컬 포트를 지정할 경우 예: `kubectl port-forward svc/... 3456:3000` 실행 시 `http://localhost:3456`)*

#### 방법 B. GKE 외부 공인 IP(LoadBalancer External IP) 발급 (클라우드 환경)
클라우드 쿠버네티스인 **GKE(Google Kubernetes Engine)** 환경에서는 서비스 타입을 **`LoadBalancer`** 로 변경하여 GCP의 외부 공인 IP를 발급받을 수 있습니다:

1. **서비스 타입을 LoadBalancer로 변경**:
   ```bash
   kubectl patch svc todo-app-getting-started-todo-app-backend -p '{"spec": {"type": "LoadBalancer"}}'
   ```
2. **할당된 공인 IP(EXTERNAL-IP) 확인**:
   ```bash
   kubectl get svc todo-app-getting-started-todo-app-backend -w
   ```
   *(처음 1~2분간 `<pending>` 상태를 거쳐 GCP 로드밸런서가 생성되면 `34.xxx.xxx.xxx` 형태의 공인 IP가 부여됩니다.)*
3. **접속 URL**: **`http://<EXTERNAL-IP>:3000`** (예: `http://34.64.123.45:3000`)

---

### 6. 차트 업데이트 및 정리 (Lifecycle)

- **설정 변경 후 차트 업그레이드**:
  ```bash
  helm upgrade todo-app charts/getting-started-todo-app.local_kind
  ```

- **배포 릴리스 삭제 (Uninstall)**:
  ```bash
  helm uninstall todo-app
  ```

- **KIND 클러스터에 로드된 이미지 삭제 (`kind load docker-image` 정리)**:
  `kind` CLI 자체에는 이미지를 언로드(`kind unload`)하는 별도 명령어가 제공되지 않습니다. KIND 노드는 내부적으로 `containerd` 런타임을 사용하므로, `docker exec`를 통해 노드 내부의 `crictl rmi` 명령어로 삭제합니다.

  ```bash
  # 1. KIND 노드 컨테이너 내부 이미지 확인
  docker exec -it my-k8s-control-plane crictl images

  # 2. 업로드된 로컬 이미지 삭제 (containerd 접두사 docker.io/library/ 포함 또는 Image ID 사용)
  docker exec -it my-k8s-control-plane crictl rmi docker.io/library/todo-backend:prod
  docker exec -it my-k8s-worker crictl rmi docker.io/library/todo-backend:prod
  docker exec -it my-k8s-worker2 crictl rmi docker.io/library/todo-backend:prod

  # 3. (선택) 로컬 호스트의 도커 이미지도 함께 정리할 경우
  docker rmi todo-backend:prod
  ```

- **(트러블슈팅) LoadBalancer 서비스 삭제 시 무한 대기할 경우**:
  - 외부 IP 정리 컨트롤러 미동작으로 Finalizer가 남아있을 경우 아래 명령어로 강제 정리:
    ```bash
    kubectl patch svc <서비스명> -p '{"metadata":{"finalizers":null}}' --type=merge
    ```

---

### 7. 원격 GitHub Registry(GHCR) 이미지 사용 시 Chart 생성 및 배포

로컬에서 백엔드 도커 이미지를 직접 빌드(`docker build`)하지 않고, GitHub Container Registry(GHCR) 등에 미리 빌드 및 푸시되어 있는 원격 이미지(`ghcr.io/cstpeace0191/ssu-cloud-computing/todo-backend:prod`)를 다운로드하여 배포하는 절차 및 실전 트러블슈팅 가이드입니다.

#### 1) Compose 파일 설정 (`compose-github_kind.yaml`)
`backend` 서비스에서 `build:` 섹션을 완전히 제거하고, `image:` 속성에 원격 레지스트리 경로와 태그를 직접 지정합니다:

```yaml
services:
  proxy:
    image: traefik:v3.6
    command: --providers.docker
    ports:
      - 80:80
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      katenary.v3/ignore: "true"

  backend:
    # 원격 GitHub Container Registry(GHCR) 이미지 지정 (build 블록 제거)
    image: ghcr.io/cstpeace0191/ssu-cloud-computing/todo-backend:prod
    ports:
      - 3000:3000
    expose:
      - 3000
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: root
      MYSQL_PASSWORD: secret
      MYSQL_DB: todos    
    depends_on:
      mysql:
        condition: service_healthy
    labels:
      katenary.v3/map-env: |-
        MYSQL_HOST: '{{ include "__APP__.fullname" . }}-mysql'
```

#### 2) Katenary를 통한 Helm Chart 생성 및 덮어쓰기

Katenary를 실행하여 Helm Chart를 생성(또는 갱신)합니다:

```powershell
# (선택) 기존 차트 폴더 백업
Copy-Item -Recurse charts/getting-started-todo-app.github_kind charts/getting-started-todo-app.github_kind.bak

# Katenary 차트 변환 실행 (-f 옵션으로 기존 차트 덮어쓰기)
katenary convert -c compose-github_kind.yaml -o charts/getting-started-todo-app.github_kind -a 1.0.0 -v 0.1.0 -f
```

> [!NOTE]
> **변환 시 출력되는 안내 메시지 설명**:
> ```text
> ❕ Port name not found for port 3000 in service backend. Using port number instead
> ```
> 이 메시지는 에러가 아닙니다. 포트 3306(MySQL)과 달리 3000번 포트는 IANA 표준 포트 사전에 등록된 공식 명칭이 없으므로, Katenary가 쿠버네티스 표준 포트 이름인 `name: port-3000`을 자동으로 안전하게 부여했다는 정상 안내입니다.

#### 3) 생성되는 Helm Chart 결과 분석 (`values.yaml` & `deployment.yaml`)
Katenary는 이미지 주소를 레지스트리/저장소 경로와 태그로 자동 분리 매핑합니다:

- **`charts/getting-started-todo-app.github_kind/values.yaml`**:
  ```yaml
  backend:
    repository:
      image: ghcr.io/cstpeace0191/ssu-cloud-computing/todo-backend
      tag: prod
    replicas: 1
    imagePullPolicy: IfNotPresent
  ```
- **`charts/getting-started-todo-app.github_kind/templates/backend/deployment.yaml`**:
  ```yaml
  containers:
  - name: backend
    image: '{{ tpl .Values.backend.repository.image $ }}:{{ tpl .Values.backend.repository.tag $ | default "latest" }}'
    imagePullPolicy: {{ .Values.backend.imagePullPolicy }}
    ports:
    - containerPort: 3000
      name: port-3000
  ```

#### 4) 쿠버네티스 배포 실행
원격 이미지를 사용하므로 `docker build` 및 `kind load docker-image` 과정이 생략되며, 쿠버네티스 노드가 인터넷을 통해 이미지를 직접 다운로드합니다:

```bash
helm install todo-app charts/getting-started-todo-app.github_kind
```
*(기존 릴리스가 이미 설치되어 있는 경우: `helm upgrade todo-app charts/getting-started-todo-app.github_kind`)*

---

#### 5) 트러블슈팅: 백엔드 Pod가 `ImagePullBackOff` 상태가 되는 경우

배포 후 `kubectl get pods`를 실행했을 때 백엔드 파드가 `ImagePullBackOff` 또는 `ErrImagePull` 상태가 되는 경우의 원인 및 해결 방법입니다:

```bash
# 상세 에러 원인 확인
kubectl describe pod -l katenary.v3/component=backend
```

##### 원인 1: GitHub Packages가 비공개(Private) 상태인 경우 (401 Unauthorized / 403 Forbidden)
GitHub Packages(GHCR)는 최초 생성 시 기본값이 **Private(비공개)** 로 설정되어, 인증 없는 쿠버네티스 노드의 다운로드가 차단됩니다.

* **해결 방법 A: GitHub 웹에서 패키지를 "Public(공개)"으로 전환 (가장 간단하고 권장)**
  1. GitHub 웹 브라우저에서 본인의 Packages 탭으로 이동:  
     `https://github.com/cstpeace0191?tab=packages` (또는 해당 저장소 우측의 Packages 메뉴)
  2. `getting-started-todo-app` 패키지 클릭
  3. 오른쪽 하단의 **Package settings** 클릭
  4. 맨 아래 **Danger Zone**의 **Change package visibility** 클릭 → **`Public`** 선택 후 저장
  5. 변경 후 기존 파드를 재시작하면 정상적으로 이미지를 다운로드합니다:
     ```bash
     kubectl delete pod -l katenary.v3/component=backend
     ```

* **해결 방법 B: 패키지를 Private으로 유지하고 쿠버네티스 Secret 사용**
  1. GitHub에서 `read:packages` 권한을 가진 Personal Access Token (Classic) 생성
  2. 클러스터에 도커 레지스트리 Secret 생성:
     ```powershell
     kubectl create secret docker-registry ghcr-secret `
       --docker-server=ghcr.io `
       --docker-username=cstpeace0191 `
       --docker-password=<발급받은_GITHUB_PAT_토큰>
     ```
  3. Helm 차트에 Secret을 주입하여 업그레이드:
     ```bash
     helm upgrade todo-app charts/getting-started-todo-app.github_kind --set "pullSecrets[0].name=ghcr-secret"
     ```

##### 원인 2: 이미지 경로 또는 태그명 불일치 (Not Found / Manifest Unknown)
- `compose-github_kind.yaml`에 작성된 이미지 경로가 실제 GitHub Packages에 푸시된 경로와 정확히 일치하는지 확인합니다.

---

#### 6) 배포 완료 후 애플리케이션 접속

파드가 `Running` 상태가 되면 로컬 포트포워딩을 실행합니다:

```bash
# 1. 파드 상태 확인 (1/1 Running 확인)
kubectl get pods

# 2. 포트 포워딩 실행 (로컬 1234 또는 8080 포트와 연결)
kubectl port-forward svc/todo-app-getting-started-todo-app-backend 1234:3000
```

- 웹 브라우저에서 **[http://localhost:1234](http://localhost:1234)** 로 접속하여 Todo 앱이 정상 작동하는지 확인합니다.

---

### 8. 원격 GCP Artifact Registry 이미지 사용 시 Chart 생성 및 배포

Google Cloud Platform(GCP)의 Artifact Registry에 저장된 원격 이미지(`asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod`)를 다운로드하여 Helm Chart로 배포하는 절차입니다. (상세 클러스터 생성 및 GCP 인증 가이드는 [README-gcp_gke.md](charts/getting-started-todo-app.gcp_gke/README-gcp_gke.md) 참조)

#### 1) Compose 파일 설정 (`compose-gcp_gke.yaml`)
`backend` 서비스에서 `build:` 섹션을 생략하고, GCP Artifact Registry의 전체 이미지 경로를 지정합니다:

```yaml
services:
  proxy:
    image: traefik:v3.6
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - 80:80
      - 443:443
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    labels:
      katenary.v3/ignore: "true"

  backend:
    # GCP Artifact Registry 원격 이미지 지정
    image: asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod
    ports:
      - 3000:3000
    expose:
      - 3000
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: root
      MYSQL_PASSWORD: secret
      MYSQL_DB: todos    
    depends_on:
      mysql:
        condition: service_healthy
    labels:
      katenary.v3/map-env: |-
        MYSQL_HOST: '{{ include "__APP__.fullname" . }}-mysql'
```

* **이미지 URI 구조 분석**:
  * `asia-northeast3-docker.pkg.dev`: 서울 리전 Docker 호스트 엔드포인트
  * `ssu-agent-vertex-509708`: GCP 프로젝트 ID
  * `my-repo`: Artifact Registry 표준 Docker 저장소명
  * `todo-backend`: 이미지 패키지명
  * `prod`: 이미지 태그

#### 2) Katenary를 통한 Helm Chart 변환

```powershell
# (선택) 이전 차트 백업
Copy-Item -Recurse charts/getting-started-todo-app.gcp_gke charts/getting-started-todo-app.gcp_gke.bak

# Katenary 변환 실행 (-f 옵션으로 덮어쓰기)
katenary convert -c compose-gcp_gke.yaml -o charts/getting-started-todo-app.gcp_gke -a 1.0.0 -v 0.1.0 -f
```

* **생성된 `charts/getting-started-todo-app.gcp_gke/values.yaml` 확인**:
  ```yaml
  backend:
    repository:
      # GCP 저장소 경로가 자동으로 매핑됨
      image: asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend
      # 태그 분리
      tag: prod
    replicas: 1
    imagePullPolicy: IfNotPresent
  ```

#### 3) KIND 클러스터 배포 시 GCP 인증 Secret 설정

GCP Artifact Registry는 기본적으로 **프라이빗(Private)** 이므로, 외부 쿠버네티스(KIND) 클러스터가 이미지를 가져오려면 인증 Secret이 필요합니다.

##### [방법 1] GCP 서비스 계정 키(JSON)를 이용한 Secret 생성 (권장, 영구적)
1. GCP IAM 콘솔에서 `Artifact Registry 읽기 권한(roles/artifactregistry.reader)`을 가진 서비스 계정을 생성하고 키 파일(`key.json`)을 다운로드합니다.
2. 쿠버네티스에 도커 레지스트리 Secret을 생성합니다 (`_json_key` 사용자명 사용):
   * **PowerShell**:
     ```powershell
     kubectl create secret docker-registry gcp-ar-secret `
       --docker-server=asia-northeast3-docker.pkg.dev `
       --docker-username=_json_key `
       --docker-password=(Get-Content key.json -Raw)
     ```
   * **Bash (Git Bash / Linux)**:
     ```bash
     kubectl create secret docker-registry gcp-ar-secret \
       --docker-server=asia-northeast3-docker.pkg.dev \
       --docker-username=_json_key \
       --docker-password="$(cat key.json)"
     ```

##### [방법 2] gcloud Access Token을 이용한 임시 Secret 생성 (테스트용, 1시간 유효)
`gcloud` CLI 로그인이 되어 있다면 임시 액세스 토큰으로 Secret을 즉시 생성할 수 있습니다:
```powershell
kubectl create secret docker-registry gcp-ar-secret `
  --docker-server=asia-northeast3-docker.pkg.dev `
  --docker-username=oauth2accesstoken `
  --docker-password=(gcloud auth print-access-token)
```

##### [방법 3] GCP 저장소를 Public으로 개방하는 방법 (Secret 설정 불필요)

GCP Artifact Registry의 IAM 권한에서 **`allUsers`** 에게 **`Artifact Registry 읽기 권한자(Artifact Registry Reader)`** 역할을 부여하면, 인증 Secret 없이 누구나 익명으로 이미지를 다운로드할 수 있는 Public 저장소가 됩니다.

* **A. GCP 웹 콘솔(Cloud Console)에서 설정하는 단계**:
  1. **저장소 목록 페이지로 이동**:
     - 개별 이미지 상세 화면(`Images for my-repo`)에서는 권한 설정 메뉴가 보이지 않으므로, 화면 왼쪽 메뉴의 **`Repositories`** 를 클릭하거나 중앙의 뒤로가기 화살표(**`←`**)를 눌러 저장소 목록 페이지로 이동합니다.
  2. **저장소 선택 및 권한 패널 열기**:
     - 저장소 목록 테이블에서 **`my-repo` 왼쪽의 체크박스(☐)** 를 체크합니다.
     - 화면 오른쪽에 **[권한 (Permissions)]** / **[정보 패널]** 이 자동으로 열립니다. (열리지 않을 경우 우측 상단 **[정보 패널 표시]** 아이콘 클릭)
  3. **`allUsers` 주 구성원 추가**:
     - **[주 구성원 추가 (Add Principal)]** 버튼 클릭
     - **새 주 구성원 (New principals)**: `allUsers` 입력
     - **역할 (Select a role)**: `Artifact Registry` → **`Artifact Registry 읽기 권한자 (Artifact Registry Reader)`** 선택
     - **[저장 (Save)]** 클릭 (공개 리소스 경고 팝업이 뜨면 **[공개 액세스 허용]** 선택)

* **B. `gcloud` CLI 명령어로 즉시 설정하는 방법**:
  ```powershell
  gcloud artifacts repositories add-iam-policy-binding my-repo `
      --location=asia-northeast3 `
      --project=ssu-agent-vertex-509708 `
      --member="allUsers" `
      --role="roles/artifactregistry.reader"
  ```

#### 4) Helm 배포 및 확인

저장소 상태(Private vs Public)에 따라 배포 명령을 실행합니다:

```bash
# 1. Private 저장소인 경우 (Secret 주입)
helm upgrade --install todo-app charts/getting-started-todo-app.gcp_gke --set "pullSecrets[0].name=gcp-ar-secret"

# 2. Public 저장소로 개방한 경우 (Secret 없이 즉시 배포 가능)
helm upgrade --install todo-app charts/getting-started-todo-app.gcp_gke

# 3. 파드 기동 및 이미지 Pull 상태 확인
kubectl get pods -w
```

#### 5) 웹 애플리케이션 접속 (http://<URL> 확인 방법)

GCP/GKE 또는 로컬 KIND 환경에서 웹 브라우저로 접속하는 URL 확인 방법입니다:

* **방법 1: 로컬 포트포워딩 접속 (비용 없음 / 빠른 테스트)**:
  ```bash
  kubectl port-forward svc/todo-app-getting-started-todo-app-backend 8080:3000
  ```
  - **접속 URL**: **[http://localhost:8080](http://localhost:8080)**  
    *(또는 `... 3456:3000` 등 원하는 로컬 포트로 지정 가능)*

* **방법 2: GKE 외부 공인 IP(External IP) 발급 (인터넷 공용 URL)**:
  GKE 클러스터에 배포한 경우 서비스를 `LoadBalancer`로 변경하여 GCP 공인 IP를 발급받을 수 있습니다:
  ```bash
  # 서비스 타입 LoadBalancer로 변경
  kubectl patch svc todo-app-getting-started-todo-app-backend -p '{"spec": {"type": "LoadBalancer"}}'

  # 외부 IP 확인
  kubectl get svc todo-app-getting-started-todo-app-backend -w
  ```
  - **접속 URL**: **`http://<EXTERNAL-IP>:3000`**  
    *(주의: 실습 종료 후에는 로드밸런서 요금 방지를 위해 `helm uninstall todo-app`으로 삭제를 권장합니다.)*
