# Getting Started Todo App (Docker 개발 & 배포 가이드)

이 프로젝트는 Docker의 모범 사례(Best Practices)를 적용한 샘플 Todo 리스트 애플리케이션입니다. 
Dockerfile의 멀티스테이지 빌드(Multi-stage build), 환경별 Docker Compose 파일 분리(`compose-build.yml`, `compose-prod-build.yml`, `docker-compose-prod.yml`, `cloudrun-compose.yml`), Compose Watch를 활용한 실시간 핫 리로드(Hot Reload), Traefik 리버스 프록시 라우팅, Vite 개발 서버 설정, 그리고 GCP Cloud Run 서버리스 배포 구성을 체계적으로 정리한 문서입니다.

---

## 1. 애플리케이션 아키텍처

![애플리케이션 아키텍처](https://github.com/docker/getting-started-todo-app/assets/313480/c128b8e4-366f-4b6f-ad73-08e6652b7c4d)

본 애플리케이션은 **React 프론트엔드**, **Node.js 백엔드**, **MySQL 데이터베이스**, 그리고 요청을 각 서비스로 분기하는 **Traefik 리버스 프록시**로 구성됩니다.

* **개발 환경 (Development)**:
  * 프론트엔드([Vite](https://vitejs.dev/))와 백엔드([nodemon](https://nodemon.io/))가 각각 독립된 개발용 컨테이너로 실행됩니다.
  * **Docker Compose Watch**를 통해 호스트의 소스 코드 변경 사항이 컨테이너 내부로 즉시 동기화(Sync & Rebuild)됩니다.
  * **Traefik 프록시**가 `localhost` 및 `127.0.0.1`로 들어오는 요청 중 `/api`는 백엔드(포트 3000)로, 그 외 일반 웹 요청은 클라이언트(포트 5173)로 자동 라우팅합니다.
  * 데이터베이스의 직관적인 관리를 위해 **phpMyAdmin**(`http://db.localhost`)이 함께 제공됩니다.

* **프로덕션 환경 (Production)**:
  * Dockerfile의 멀티스테이지 빌드를 통해 단위 테스트(`test`)를 거친 후, React 프론트엔드를 정적 HTML/CSS/JS 파일로 컴파일하여 백엔드 내부(`src/static`)로 번들링합니다.
  * 단일 백엔드 컨테이너에서 정적 프론트엔드 에셋 서빙과 REST API 처리를 동시에 수행하므로 구성이 단순해지고 리소스 효율이 극대화됩니다.

---

## 2. Windows 로컬 개발 환경 직접 실행 가이드 (Node.js 기반)

Docker 컨테이너를 사용하지 않고 로컬 Windows 머신에서 Node.js 환경으로 백엔드와 프론트엔드를 직접 구동하고 개발/빌드하는 방법입니다.

### 2.1 의존성 패키지 설치
각 폴더로 이동하여 필요한 패키지를 설치합니다:
```bash
# 백엔드 의존성 설치
cd backend
npm install

# 프론트엔드 의존성 설치
cd ../client
npm install
```

---

### 2.2 백엔드 서버 실행 (`backend` ➔ `npm run dev`)
터미널 #1에서 백엔드 서버를 구동합니다:
```bash
cd backend
npm run dev
```
* `nodemon`을 통해 구동되며, 파일 변경 시 자동으로 서버가 재시작됩니다.
* 기본적으로 **포트 3000**(`http://localhost:3000`)에서 REST API 및 정적 파일 서빙 대기 상태가 됩니다.

---

### 2.3 프론트엔드 개발 모드 실행 (`client` ➔ `npm run dev`)

터미널 #2에서 Vite 개발 서버를 구동합니다:
```bash
cd client
npm run dev
```

#### 💡 Vite Development Server의 역할과 Backend Forward (API Proxy)
1. **Vite Development Server의 역할**:
   * 초고속 HMR(Hot Module Replacement)을 제공하여 코드 수정 시 브라우저 새로고침 없이 변경 사항을 즉시 반영합니다.
   * 기본적으로 **포트 5173**(`http://localhost:5173`)에서 프론트엔드 개발 페이지를 서빙합니다.

2. **Backend Forward를 위한 `vite.config.js` 프록시 설정**:
   * 브라우저가 `http://localhost:5173`에서 실행되는 React 앱에서 백엔드 API(`/api/items` 등)를 호출하면 포트가 달라 **CORS(Cross-Origin Resource Sharing)** 문제가 발생할 수 있습니다.
   * 이를 해결하기 위해 Vite 개발 서버에 프록시(Proxy) 규칙을 설정하여, `/api`로 시작하는 모든 요청을 백엔드(`http://localhost:3000`)로 투명하게 포워딩(Forward)해줍니다.

```javascript
// client/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            // '/api'로 시작하는 요청을 백엔드 포트 3000으로 포워딩
            '/api': 'http://localhost:3000'
        }
    }
});
```
* **개발 중 접속 주소**: [http://localhost:5173](http://localhost:5173)

---

### 2.4 프론트엔드 정적 빌드 및 백엔드 통합 서빙 (`client` ➔ `npm run build`)

개발 완료 후 프론트엔드를 빌드하여 백엔드 단일 서버(`3000`)에서 한 번에 서비스할 때 사용하는 방법입니다.

```bash
cd client
npm run build
```

#### 🔄 빌드 및 자동 복사 동작 흐름:
1. **`vite build`**: React 소스 코드를 번들링하여 최적화된 HTML/CSS/JS 정적 에셋을 `client/dist` 디렉토리에 생성합니다.
2. **`postbuild` 자동 트리거**: `client/package.json`의 `postbuild` 라이프사이클 스크립트에 의해 `client/dist`의 내용물이 `backend/src/static` 디렉토리로 자동 복사됩니다.
   ```json
   // client/package.json
   "scripts": {
     "dev": "vite --host=0.0.0.0",
     "build": "vite build",
     "postbuild": "node -e \"require('fs').cpSync('dist', '../backend/src/static', {recursive: true})\"",
     ...
   }
   ```
3. **통합 서빙 확인**: 백엔드 서버(`backend`)가 실행 중인 상태(`npm run dev` 또는 `npm start`)라면, 브라우저에서 [http://localhost:3000](http://localhost:3000)에 접속했을 때 Express가 `/backend/src/static`의 정적 파일을 서빙하므로 별도의 Vite 서버 없이도 완전한 Todo 앱이 동작합니다.

> 💡 **Windows PowerShell 팁**: PowerShell 실행 정책으로 인해 `npm` 명령 실행 시 권한 에러(`PSSecurityException`)가 발생할 경우 `npm.cmd run dev` 또는 `npm.cmd run build`를 사용하세요.

---

## 3. Dockerfile 멀티스테이지 구조

`Dockerfile`은 단계별로 캐싱을 최적화하고 최종 산출물의 크기를 최소화하도록 설계되어 있습니다.

```
base (Node.js 22)
├── client-base
│   ├── client-dev (개발용 Vite 서버 실행: npm run dev)
│   └── client-build (정적 에셋 빌드: npm run build -> dist/)
└── backend-dev (개발용 nodemon 서버 실행: npm run dev)
    └── test (백엔드 단위 테스트 실행: npm run test)
        └── final (프로덕션 최종 이미지: 클라이언트 dist 산출물을 src/static 으로 복사)
```

### 3.1 프로덕션 스테이지(`final`)와 포트 설정: `EXPOSE 3000` ➔ `8080` 변경 이유

`Dockerfile`의 `final` 스테이지(Line 82~90)는 운영 환경에 배포되는 최종 단일 컨테이너 이미지를 생성합니다:

```dockerfile
FROM base AS final
ENV NODE_ENV=production
COPY --from=test /usr/local/app/package.json /usr/local/app/package-lock.json ./
RUN npm ci --production && \
    npm cache clean --force
COPY backend/src ./src
COPY --from=client-build /usr/local/app/dist ./src/static
EXPOSE 8080
CMD ["node", "src/index.js"]
```

기존 로컬 개발 환경에서는 백엔드가 3000번 포트를 사용하여 `EXPOSE 3000`으로 작성되어 있었으나, 이를 **`EXPOSE 8080`으로 변경해야 하는 핵심 이유**는 **GCP Cloud Run의 컨테이너 런타임 규약(Container Runtime Contract)** 때문입니다.

#### 1) GCP Cloud Run의 포트 계약(Port Contract)과 `PORT` 환경 변수
* **기본 수신 포트 `8080` 규약**: GCP Cloud Run은 컨테이너 인스턴스로 유입되는 외부 HTTP 인그레스(Ingress) 요청을 컨테이너 내부의 **`8080` 포트**로 라우팅하는 것을 기본 표준으로 채택하고 있습니다.
* **`PORT` 환경 변수 자동 주입**: Cloud Run 인스턴스가 기동될 때, 플랫폼 내부에서 자동으로 `PORT=8080` 환경 변수를 컨테이너 프로세스에 주입합니다.

#### 2) `const PORT = process.env.PORT || 3000;` 구문의 설계 의도와 필요성
서버 코드([backend/src/index.js](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/03week/getting-started-todo-app/backend/src/index.js))에서 포트를 `app.listen(3000)`으로 하드코딩하지 않고 환경 변수와 기본값 연산자(`||`)를 조합한 이유는 다음과 같습니다:

1. **클라우드-네이티브 및 The Twelve-Factor App (포트 바인딩) 원칙 준수**:
   - 현대 웹 애플리케이션 설계 방법론인 **Twelve-Factor App (III. Config & VII. Port binding)**에 따르면, 애플리케이션은 실행 포트를 소스 코드에 하드코딩하지 않고 **실행 환경(Environment Variable)으로부터 주입받아 자체 포트에 바인딩**해야 합니다.
2. **다양한 클라우드 플랫폼(GCP Cloud Run, Heroku, AWS 등)의 동적 포트 수용**:
   - **GCP Cloud Run**은 인스턴스 시작 시 `PORT=8080`을 자동 주입합니다.
   - **Heroku, AWS Elastic Beanstalk, Azure App Service** 등 다양한 클라우드/PaaS 환경에서도 각 시스템의 라우터가 지정한 포트 번호를 `PORT` 환경 변수로 동적 전달합니다.
   - 만약 코드가 `3000`으로 고정되어 있으면 Cloud Run은 8080 포트에서 응답이 없어 컨테이너를 비정상(Crash/Timeout) 종료 처리하게 됩니다.
3. **로컬 개발 환경의 개발자 경험(DX) 및 Fallback 기본값 제공**:
   - 환경 변수 `PORT`가 지정되지 않은 일반 로컬 개발 환경(`npm run dev`)에서는 논리 OR 연산자(`||`) 뒤의 기본값 `3000`이 적용됩니다.
   - 따라서 로컬 개발자가 매번 번거롭게 `PORT=3000`을 명시하지 않아도 [http://localhost:3000](http://localhost:3000)으로 바로 접속할 수 있습니다.
4. **포트 충돌 회피 및 소스 코드 무수정 배포**:
   - 로컬 머신에서 이미 3000번 포트를 다른 프로그램이 사용 중일 때, 소스 코드를 단 한 줄도 수정하지 않고 `PORT=4000 npm run dev`와 같이 실행하여 즉시 포트 충돌을 회피할 수 있습니다.

#### 3) `EXPOSE 8080` 선언이 필요한 핵심 이유
1. **Cloud Run 배포 도구의 포트 자동 감지 메타데이터**:
   - `gcloud run deploy`, Cloud Build, 또는 GCP 콘솔을 통해 이미지를 배포할 때, 배포 시스템은 Dockerfile의 `EXPOSE` 메타데이터를 검사하여 컨테이너가 수신 대기할 포트를 자동으로 인식합니다.
   - 만약 `EXPOSE 3000`으로 설정된 이미지를 배포하면 Cloud Run이 트래픽을 3000번으로 잘못 전달하거나 포트 불일치로 판단하여, 헬스체크(Startup Probe) 실패 에러(`Container failed to start and listen on the port`)가 발생할 수 있습니다.
2. **컨테이너 이미지의 자체 완결성과 표준화**:
   - `EXPOSE 8080`을 명시적으로 선언함으로써 해당 이미지가 GCP Cloud Run 표준 환경 규약을 완벽히 준수함을 명시하고, 협업 개발자 및 CI/CD 파이프라인에 일관된 포트 계약 정보를 제공합니다.

---

## 4. Docker Compose 개발 환경 가이드 (`compose-build.yml`)

`compose-build.yml`은 빠른 코드 수정과 디버깅을 위한 개발자 전용 Compose 파일입니다.

### 4.1 서비스 구성 요약
* **`proxy` (Traefik v3.6)**: 80번 포트 진입점
  * `localhost`, `127.0.0.1` ➔ 프론트엔드(`client:5173`)
  * `localhost/api`, `127.0.0.1/api` ➔ 백엔드(`backend:3000`)
  * `db.localhost` ➔ phpMyAdmin(`phpmyadmin:80`)
* **`backend`**: `backend-dev` 타깃 빌드, 소스 코드 실시간 동기화(`watch`)
* **`client`**: `client-dev` 타깃 빌드, 소스 코드 실시간 동기화(`watch`)
* **`mysql`**: MySQL 9.3 (헬스체크 및 `todo-mysql-data` 볼륨 영속화)
* **`phpmyadmin`**: 웹 DB 관리 도구

### 4.2 실행 명령어

```bash
# 실시간 파일 감지 및 자동 동기화 모드로 실행 (권장)
docker compose -f compose-build.yml up --watch

# 또는 백그라운드 빌드 및 실행
docker compose -f compose-build.yml up -d --build
```

### 4.3 접속 URL
* **Todo 애플리케이션**: [http://localhost](http://localhost) 또는 [http://127.0.0.1](http://127.0.0.1)
* **phpMyAdmin (DB 관리자)**: [http://db.localhost](http://db.localhost) (계정: `root` / 암호: `secret`)

### 4.4 개발 환경 종료
```bash
docker compose -f compose-build.yaml down
```

---

## 5. Docker Compose 기반 프로덕션 환경 가이드 (`compose-prod-build.yml` & `docker-compose-prod.yml`)

프로덕션(운영) 환경에서는 개발용 실시간 파일 감시(Watch) 및 phpMyAdmin 등의 개발용 컨테이너를 제거하고, React 정적 빌드 산출물이 내장된 단일 백엔드 컨테이너(`final` 타깃)와 Traefik 프록시, MySQL 데이터베이스로 운영합니다.

운영 환경 실행 방식은 크게 두 가지로 나뉩니다:
1. **로컬 소스 기반 빌드 실행 (`compose-prod-build.yml`)**: 로컬 소스 코드를 바탕으로 컨테이너 이미지를 직접 빌드하여 실행
2. **원격 레지스트리 기반 배포 실행 (`docker-compose-prod.yml`)**: Docker Hub, GitHub Container Registry(GHCR), GCP Artifact Registry 등 중앙 저장소에 푸시된 검증된 이미지를 다운로드(`pull`)하여 소스 빌드 없이 즉시 실행

---

### 5.1 로컬 소스 빌드 기반 프로덕션 환경 (`compose-prod-build.yml`)

`compose-prod-build.yml`은 배포용 단일 번들 이미지를 로컬 소스로부터 직접 빌드하여 운영 환경과 동일하게 실행합니다.

#### 1) 서비스 구성 요약
* **`proxy` (Traefik v3.6)**: 80(HTTP), 443(HTTPS) 포트를 수신하여 백엔드 컨테이너(3000 포트)로 트래픽 라우팅
* **`backend`**: Dockerfile의 `final` 타깃 빌드 (`build: { context: ./, target: final }`)
* **`mysql`**: MySQL 9.3 데이터베이스 (헬스체크 적용 및 `todo-mysql-data` 볼륨 영속화)

#### 2) 실행 및 관리 명령어
```powershell
# 프로덕션 이미지 빌드 및 백그라운드 실행
docker compose -f compose-prod-build.yml up -d --build

# 실행 로그 실시간 확인
docker compose -f compose-prod-build.yml logs -f

# 서비스 종료
docker compose -f compose-prod-build.yml down
```

---

### 5.2 원격 레지스트리 기반 프로덕션 배포 가이드 (`docker-compose-prod.yml`)

운영 서버(Production Server)나 온프레미스 VM 환경에서는 소스 코드 노출 방지 및 빌드 리소스 절약을 위해 로컬 소스 빌드를 수행하지 않고, 사전에 빌드되어 검증된 컨테이너 이미지를 원격 레지스트리에서 다운로드하여 배포하는 것이 모범 사례(Best Practice)입니다.

#### 1) 3대 원격 컨테이너 레지스트리 정보 요약

| 레지스트리 | 저장소 형식 / 주소 체계 | 기본 이미지 태그 예시 |
| :--- | :--- | :--- |
| **Docker Hub** | `<DockerHub_계정명>/<이미지명>:<태그>` | `ssucloud/getting-started-todo-app:todo-backend` |
| **GitHub Container Registry (GHCR)** | `ghcr.io/<GitHub_소유자>/<저장소명>/<이미지명>:<태그>` | `ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend` |
| **GCP Artifact Registry** | `<리전>-docker.pkg.dev/<프로젝트ID>/<저장소명>/<이미지명>:<태그>` | `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend` |

---

#### 2) 레지스트리별 이미지 태깅 (`docker tag`)
로컬에서 빌드한 프로덕션 이미지(`todo-backend`)를 각 원격 레지스트리의 주소 체계에 맞춰 태깅합니다:

* **Docker Hub**:
  ```powershell
  docker tag todo-backend ssucloud/getting-started-todo-app:todo-backend
  ```
* **GitHub Container Registry (GHCR)**:
  ```powershell
  docker tag todo-backend ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend
  ```
* **GCP Artifact Registry**:
  ```powershell
  docker tag todo-backend asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend
  ```

---

#### 3) 레지스트리 인증 로그인 및 이미지 푸시 (`docker push`)
각 원격 저장소에 접근할 수 있도록 인증을 수행한 후 이미지를 푸시합니다:

* **Docker Hub**:
  ```powershell
  # 1. 로그인 (Docker Hub ID / 비밀번호 또는 Personal Access Token 입력)
  docker login

  # 2. 푸시
  docker push ssucloud/getting-started-todo-app:todo-backend
  ```

* **GitHub Container Registry (GHCR)**:
  ```powershell
  # 1. 개인 접근 토큰(PAT, write:packages 권한 필수)을 통한 로그인
  echo "<YOUR_GITHUB_PAT>" | docker login ghcr.io -u <GITHUB_USERNAME> --password-stdin

  # 2. 푸시
  docker push ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend
  ```

* **GCP Artifact Registry**:
  ```powershell
  # 1. gcloud CLI를 통한 Docker 인증 헬퍼 등록 (서울 리전: asia-northeast3)
  gcloud auth configure-docker asia-northeast3-docker.pkg.dev

  # 2. 푸시
  docker push asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend
  ```

---

#### 4) 이미지 사전 다운로드 (`docker pull`)
운영 서버나 새로운 배포 머신에서 이미지를 사전 다운로드(Pull)하여 이미지 무결성을 검증하고 배포 시간을 단축할 수 있습니다:

* **Docker Hub**:
  ```powershell
  docker pull ssucloud/getting-started-todo-app:todo-backend
  ```
* **GitHub Container Registry (GHCR)**:
  ```powershell
  # (비공개 패키지일 경우 사전에 docker login ghcr.io 필요)
  docker pull ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend
  ```
* **GCP Artifact Registry**:
  ```powershell
  # (사전 인증 필수: gcloud auth configure-docker asia-northeast3-docker.pkg.dev)
  docker pull asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend
  ```

---

#### 5) `docker-compose-prod.yml` 설정 및 레지스트리 이미지 전환
`docker-compose-prod.yml`의 `backend` 서비스는 `build:` 속성 없이 원격 `image:`만을 지정하여 구동됩니다. 사용하려는 레지스트리에 맞춰 주석을 해제하거나 이미지를 지정할 수 있습니다:

```yaml
services:
  proxy:
    image: traefik:v3.6
    command:
      - --providers.docker=true
      - --providers.docker.exposedbydefault=true
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
    ports:
      - 80:80
      - 443:443
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  backend:
    # [옵션 1] Docker Hub 이미지 사용 시
    # image: ssucloud/getting-started-todo-app:todo-backend

    # [옵션 2] GitHub Container Registry (GHCR) 이미지 사용 시
    # image: ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend  

    # [옵션 3] GCP Artifact Registry 이미지 사용 시
    image: asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: root
      MYSQL_PASSWORD: secret
      MYSQL_DB: todos    
    depends_on:
      mysql:
        condition: service_healthy
    labels:
      traefik.enable: "true"
      traefik.http.routers.backend-http.entrypoints: "web"
      traefik.http.routers.backend-http.rule: "PathPrefix(`/`)"
      traefik.http.routers.backend-http.service: "backend-service"
      traefik.http.routers.backend-https.entrypoints: "websecure"
      traefik.http.routers.backend-https.rule: "PathPrefix(`/`)"
      traefik.http.routers.backend-https.tls: "true"
      traefik.http.routers.backend-https.service: "backend-service"
      traefik.http.services.backend-service.loadbalancer.server.port: "3000"

  mysql:
    image: mysql:9.3
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

volumes:
  todo-mysql-data:
```

---

#### 6) Docker Compose 실행 및 관리 명령어 (`docker compose`)

`docker-compose-prod.yml`을 사용하여 서비스를 배포하고 관리하는 표준 명령어입니다:

```powershell
# 1. Compose 파일에 지정된 원격 이미지 일괄 다운로드
docker compose -f docker-compose-prod.yml pull

# 2. 백그라운드 서비스 시작 (이미지 다운로드 및 컨테이너 기동)
docker compose -f docker-compose-prod.yml up -d

# 3. 서비스 실행 상태 및 컨테이너 헬스체크 확인
docker compose -f docker-compose-prod.yml ps

# 4. 백엔드 서비스 실행 로그 실시간 확인
docker compose -f docker-compose-prod.yml logs -f backend

# 5. 프로덕션 서비스 중지 및 컨테이너 정리
docker compose -f docker-compose-prod.yml down
```

> 💡 **원격 레지스트리 기반 배포의 주요 장점**:
> 1. **소스 코드 보안**: 운영 서버에 Git 저장소를 복제하거나 원본 소스 코드를 올릴 필요가 없어 코드 유출 위험을 방지합니다.
> 2. **빌드 리소스 절약**: 운영 서버의 CPU와 메모리를 소모하는 무거운 빌드 과정 없이, 가벼운 컨테이너 기동만 수행합니다.
> 3. **배포 일관성 (불변 인프라, Immutable Infrastructure)**: CI/CD 파이프라인에서 테스트가 완료된 동일한 이미지 다이제스트(Digest)를 모든 서버에 오차 없이 배포할 수 있습니다.

---

## 6. Docker 볼륨(Volume)과 데이터 영속성

Compose 파일에서 MySQL 서비스에 정의된 볼륨 설정은 다음과 같습니다:

```yaml
services:
  mysql:
    image: mysql:9.3
    volumes:
      - todo-mysql-data:/var/lib/mysql
...
volumes:
  todo-mysql-data:
```

### 6.1 구문 상세 분석 (`todo-mysql-data:/var/lib/mysql`)

$$\underbrace{\text{todo-mysql-data}}_{\text{1. 호스트 볼륨 이름}} \mathbf{:} \underbrace{\text{/var/lib/mysql}}_{\text{2. 컨테이너 내부 데이터 경로}}$$

1. **`todo-mysql-data` (호스트의 명명된 볼륨, Named Volume)**:
   - Docker가 호스트 머신의 스토리지 영역(`/var/lib/docker/volumes/...`)에 생성하고 관리하는 볼륨 이름입니다.
2. **`:` (콜론)**:
   - 호스트의 볼륨과 컨테이너 내부 디렉터리를 연결(Mount)하는 구분자입니다.
3. **`/var/lib/mysql` (컨테이너 내부 데이터 경로)**:
   - MySQL 데이터베이스가 테이블, 인덱스, 레코드 등 실제 데이터를 저장하는 컨테이너 내부의 기본 경로입니다.

### 6.2 볼륨 사용의 목적 및 장점
* **데이터 영속성 (Data Persistence)**: 컨테이너는 기본적으로 휘발성(Stateless)을 가집니다. 볼륨을 마운트하면 컨테이너를 중지하거나 삭제(`down`)하더라도 생성한 Todo 데이터가 호스트에 안전하게 보존됩니다.
* **OS 독립성 및 이식성**: 호스트 머신의 특정 절대 경로를 하드코딩하지 않고 Docker가 볼륨을 관리하므로 Windows, macOS, Linux(GCP VM) 어디서든 동일하게 작동합니다.

### 6.3 수동 생성 볼륨을 컨테이너에 매핑하는 방법 (`docker run`)

`docker volume create todo-mysql-data` 명령어로 미리 생성해 둔 볼륨을 컨테이너 실행 시 마운트하려면 다음과 같이 실행합니다:

#### 방법 A: `-v` 플래그 사용 (표준 단축 문법)
```bash
docker run -d \
  --name mysql-server \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=todos \
  -v todo-mysql-data:/var/lib/mysql \
  -p 3306:3306 \
  mysql:9.3
```

#### 방법 B: `--mount` 플래그 사용 (Docker 공식 권장 문법)
```bash
docker run -d \
  --name mysql-server \
  -e MYSQL_ROOT_PASSWORD=secret \
  -e MYSQL_DATABASE=todos \
  --mount source=todo-mysql-data,target=/var/lib/mysql \
  -p 3306:3306 \
  mysql:9.3
```

> ⚠️ **주의 (동적 마운트 불가)**: Docker의 네임스페이스 격리 원칙상 **이미 실행 중인 컨테이너에 실시간으로 볼륨을 동적 추가할 수는 없습니다.** 볼륨을 새로 매핑하려면 기존 컨테이너를 중지 및 삭제(`docker stop` && `docker rm`) 후 마운트 옵션을 주어 다시 시작해야 합니다.

### 6.4 Docker Compose에서 수동 생성 볼륨 연동 (`external: true`)

수동으로 생성한 볼륨을 Docker Compose에서 그대로 사용하려면 `external: true`를 선언합니다:

```yaml
services:
  mysql:
    image: mysql:9.3
    volumes:
      - todo-mysql-data:/var/lib/mysql
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: todos

# 수동으로 생성한 외부 볼륨을 참조
volumes:
  todo-mysql-data:
    external: true
```
* **장점**: `docker compose down -v`를 실행하더라도 `external: true`로 지정된 볼륨은 자동으로 삭제되지 않고 안전하게 보호됩니다.

### 6.5 마운트 정상 매핑 검증
컨테이너에 볼륨이 정상적으로 연결되었는지 확인하는 명령어:
```bash
docker inspect mysql-server --format '{{ json .Mounts }}'
```
출력 결과에 `"Name":"todo-mysql-data"`와 `"Destination":"/var/lib/mysql"`이 포함되어 있으면 정상 매핑된 상태입니다.

### 6.6 볼륨 관련 핵심 Docker CLI 명령어 모음

```bash
# 1) 명명된 볼륨 수동 생성
docker volume create todo-mysql-data

# 2) 전체 볼륨 목록 확인
docker volume ls

# 3) 볼륨 상세 정보 및 호스트 실제 저장 경로(Mountpoint) 확인
docker volume inspect todo-mysql-data

# 4) 특정 볼륨 삭제 (연결된 컨테이너가 없을 때만 가능)
docker volume rm todo-mysql-data

# 5) 사용하지 않는 미연결 볼륨 일괄 정리
docker volume prune -f

# 6) Compose 실행 시 볼륨까지 함께 삭제하여 DB 완전 초기화
docker compose -f compose-build.yml down -v
```

---

## 7. GCP Cloud Run 배포 가이드 (`gcloud run compose`)

GCP Cloud Run은 인프라 관리 없이 컨테이너를 직접 실행하는 완전 관리형 서버리스(Serverless) 컴퓨팅 플랫폼입니다. 트래픽 유입에 따라 0개부터 N개 인스턴스까지 자동 확장(Scale-to-Zero & Auto-scaling)을 지원합니다.

Google Cloud SDK의 `gcloud run compose` 도구를 활용하면 로컬 Docker Compose 규격을 기반으로 Cloud Run 멀티 컨테이너 서비스를 클라우드에 원클릭으로 직접 배포할 수 있습니다.

---

### 7.1 GCP CLI 환경 구축 및 Artifact Registry 설정 가이드

Cloud Run 배포 및 원격 이미지 관리를 위해 Google Cloud CLI(`gcloud`)를 설치하고, 계정 인증, Artifact Registry API 활성화, Docker 형식의 저장소 생성 및 Docker 자격 증명 헬퍼 연동까지의 전체 절차입니다.

#### 1) Google Cloud CLI (`gcloud`) 설치
* **Windows 설치 방법**:
  * **옵션 A (PowerShell 명령어로 설치)**:
    ```powershell
    (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
    & $env:Temp\GoogleCloudSDKInstaller.exe
    ```
  * **옵션 B (공식 설치 프로그램 다운로드)**:
    [Google Cloud CLI 공식 설치 페이지](https://cloud.google.com/sdk/docs/install?hl=ko)에서 Windows용 설치 프로그램을 다운로드하여 설치를 진행합니다.
* **설치 확인**: 새 터미널 또는 PowerShell을 열고 아래 명령어로 버전이 정상 출력되는지 확인합니다:
  ```powershell
  gcloud --version
  ```

---

#### 2) `gcloud` 로그인 인증 및 기본 설정 (`gcloud auth login`)
Google 계정으로 로그인하여 GCP 프로젝트 및 기본 리전을 설정합니다:

```powershell
# 1. Google 계정 브라우저 로그인 인증
gcloud auth login

# 2. 작업할 기본 GCP 프로젝트 ID 설정
gcloud config set project ssu-agent-vertex-509708

# 3. 기본 리전(Region)을 서울(asia-northeast3)로 설정
gcloud config set run/region asia-northeast3

# 4. 현재 적용된 gcloud 환경 설정 확인
gcloud config list
```

---

#### 3) GCP Artifact Registry 서비스 API 활성화 (`gcloud services enable`)
새로운 GCP 프로젝트에서는 각 클라우드 서비스 API가 기본적으로 비활성화되어 있으므로, Artifact Registry 및 Cloud Run API를 활성화해야 합니다:

```powershell
# 1. Artifact Registry API 서비스 활성화
gcloud services enable artifactregistry.googleapis.com

# 2. Cloud Run 관리 API 서비스 활성화
gcloud services enable run.googleapis.com

# 3. 서비스 활성화 여부 확인
gcloud services list --enabled | findstr "artifactregistry"
```
> 💡 **웹 콘솔에서 활성화하는 방법**:
> GCP 웹 콘솔([https://console.cloud.google.com](https://console.cloud.google.com)) 접속 ➔ 상단 검색창에 **Artifact Registry** 검색 ➔ [사용(Enable)] 버튼 클릭으로도 동일하게 활성화할 수 있습니다.

---

#### 4) Docker 형식의 GCP Artifact Registry 저장소 생성 (`gcloud artifacts repositories create`)
컨테이너 이미지를 저장할 Docker 형식의 Artifact Registry 저장소(`my-docker-repo`)를 서울 리전(`asia-northeast3`)에 생성합니다:

```powershell
# Docker 형식의 레포지토리 생성
gcloud artifacts repositories create my-docker-repo `
  --repository-format=docker `
  --location=asia-northeast3 `
  --description="Getting Started Todo App Docker Repository"
```

* **생성된 저장소 목록 및 상세 정보 확인**:
  ```powershell
  gcloud artifacts repositories list --location=asia-northeast3
  ```

---

#### 5) GCP CLI Docker 자격 증명(Credential Helper) 연동 (`gcloud auth configure-docker`)
로컬 Docker 데몬(`docker.exe`)이 Google Artifact Registry(`asia-northeast3-docker.pkg.dev`)에 별도의 패스워드 입력 없이 안전하게 `push` 및 `pull`할 수 있도록 Google 인증 헬퍼를 등록합니다:

```powershell
# 서울 리전 Artifact Registry에 대한 Docker 인증 헬퍼 등록 (최초 1회 필수)
gcloud auth configure-docker asia-northeast3-docker.pkg.dev
```

* **동작 원리**: 로컬 사용자의 `~/.docker/config.json` 파일에 `asia-northeast3-docker.pkg.dev` 레지스트리에 대한 자격 증명 도우미(`gcloud`)가 자동으로 등록되어, `gcloud`의 유효한 OAuth2 Access Token을 통해 Docker CLI가 안전하게 인증을 처리합니다.

---

#### 6) 로컬 프로덕션 이미지 빌드, 태깅 (`docker tag`) 및 푸시 (`docker push`)
생성된 Artifact Registry 저장소 주소 체계에 맞춰 이미지를 빌드, 태깅하고 클라우드로 업로드합니다:

* **저장소 전체 경로 체계**:
  $$\text{asia-northeast3-docker.pkg.dev} \;/\; \underbrace{\text{ssu-agent-vertex-509708}}_{\text{프로젝트 ID}} \;/\; \underbrace{\text{my-docker-repo}}_{\text{저장소 이름}} \;/\; \underbrace{\text{getting-started-todo-app:todo-backend}}_{\text{이미지명:태그}}$$

```powershell
# 1. 프로덕션 이미지 빌드 (단일 번들 target: final)
docker build -t todo-backend --target final .

# 2. Artifact Registry 경로로 이미지 태깅
docker tag todo-backend asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend

# 3. Artifact Registry로 이미지 푸시
docker push asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend

# 4. 저장소에 정상 업로드된 이미지 및 태그 목록 확인
gcloud artifacts docker images list asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo
```

> 💡 **참고 (다양한 레지스트리 활용)**:
> 필요에 따라 GitHub Container Registry(GHCR) 또는 Docker Hub를 원격 저장소로 사용할 수도 있습니다:
> * **GHCR**: `ghcr.io/ssucloudagent/ssu-cloud-computing/getting-started-todo-app:todo-backend`
> * **Docker Hub**: `ssucloud/getting-started-todo-app:todo-backend`

---

### 7.2 `cloudrun-compose.yml` 전체 구성

GCP Artifact Registry에 푸시된 사전 빌드 이미지를 참조하고, Cloud Run의 멀티 컨테이너 규약에 맞게 작성된 Compose 파일입니다:

```yaml
version: '3.8'

services:
  # 1. 백엔드 애플리케이션
  backend:
    image: asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-docker-repo/getting-started-todo-app:todo-backend
    ports:
      - "8080:3000" # Cloud Run 외부 트래픽 포트(8080) -> 컨테이너 실행 포트(3000)
    environment:
      # PORT는 Cloud Run이 자동으로 주입(예약어)하므로 직접 정의하지 않습니다.
      # 같은 Cloud Run 서비스(인스턴스) 내부에서는 localhost(127.0.0.1)로 사이드카 DB에 접근 가능
      MYSQL_HOST: "127.0.0.1"
      MYSQL_USER: "root"
      MYSQL_PASSWORD: "secret"
      MYSQL_DB: "todos"
    depends_on:
      - mysql
    x-google-cloudrun:
      ingress-container: true # 외부 트래픽을 수신하는 인그레스 컨테이너로 지정

  # 2. MySQL 사이드카 컨테이너 (데이터는 인스턴스 재시작 시 초기화됨)
  mysql:
    image: mysql:9.3
    ports:
      - "3306:3306" # Cloud Run 의존성 검사를 위해 포트 정의 필수
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: todos
```

---

### 7.3 핵심 구성 요소 상세 분석

#### 1) `image:` 선언을 통한 사전 빌드 이미지 직접 배포
* `build:` 섹션 대신 `image: asia-northeast3-docker.pkg.dev/...`를 명시하여, Cloud Build API 의존성을 제거하고 빌드 시간 없이 즉각적인 배포를 수행합니다.

#### 2) 멀티 컨테이너 사이드카(Sidecar) 패턴과 `127.0.0.1` 통신
* **Cloud Run 멀티 컨테이너 아키텍처**: Cloud Run 2세대 런타임은 단일 인스턴스 Pod 내에 여러 컨테이너를 함께 실행하는 사이드카(Sidecar) 패턴을 지원합니다.
* **공유 네트워크 네임스페이스 (Localhost)**: 동일 인스턴스 내부의 컨테이너들은 네트워크 네임스페이스를 공유하므로, 백엔드 앱은 복잡한 내부 DNS 설정 없이 `127.0.0.1:3306`(`localhost`)을 통해 사이드카 MySQL 컨테이너에 즉시 접속할 수 있습니다.

#### 3) `ports: - "8080:3000"` (인그레스 게이트웨이 포트 매핑)
* Cloud Run 외부 인그레스 게이트웨이가 수신하는 기본 포트 `8080`과 백엔드 컨테이너 내부 실행 포트 `3000`을 연결합니다.
* Cloud Run은 이 설정을 바탕으로 컨테이너 내부에 `PORT=3000` 환경 변수를 자동 전달합니다.

#### 4) `x-google-cloudrun: ingress-container: true`
* 멀티 컨테이너 환경에서 외부 인터넷 트래픽(HTTP Ingress)을 직접 수신할 주(Primary) 컨테이너가 `backend`임을 Cloud Run에 지정합니다.

#### 5) 사이드카 DB 데이터의 휘발성 (주의 사항)
> ⚠️ **중요 (Cloud Run 사이드카 DB의 데이터 수명 주기)**:
> Cloud Run은 트래픽 유입이 없으면 인스턴스가 0개로 축소(Scale-to-Zero)되거나, 트래픽에 따라 새 인스턴스가 동적으로 생성 및 소멸합니다. 사이드카 MySQL 컨테이너는 로컬 디스크에 데이터를 기록하므로 **인스턴스가 재기동되거나 스케일 인/아웃될 때마다 데이터가 초기화**됩니다. 따라서 실제 운영 환경에서는 **GCP Cloud SQL for MySQL**과 같은 완전 관리형 영속 DB를 사용해야 합니다.

---

### 7.4 `gcloud run compose` 배포 시 발생한 핵심 오류 및 수정 사항 정리

`gcloud run compose up .\cloudrun-compose.yml` 실행 중 발생할 수 있는 주요 오류와 해결책입니다:

#### 1) Cloud Build API 실행 권한 부족 (`403 PERMISSION_DENIED`)
* **발생 에러**:
  ```text
  X Setting up resources...
    . Building container backend from source...
  Setup failed      
  ERROR: (gcloud.run.compose.up) HttpError accessing <https://cloudbuild.googleapis.com/v1/projects/.../builds?alt=json>:
  status: 403, "The caller does not have permission", "status": "PERMISSION_DENIED"
  ```
* **원인**: `cloudrun-compose.yml`에 `build:` 설정(`context: ./`, `target: final`)이 선언되어 있으면, `gcloud` 도구가 소스 코드를 GCP Cloud Build로 전송하여 원격 빌드를 시도합니다. 이때 사용자 GCP 계정이나 서비스 계정에 Cloud Build 실행 권한이 없으면 403 오류로 배포가 실패합니다.
* **해결**: 로컬 머신에서 이미지를 미리 빌드하여 GCP Artifact Registry에 `docker push`한 후, Compose 파일에서 `build:` 구문을 제거하고 `image: <Artifact Registry 이미지 URL>` 속성을 명시하여 소스 빌드 과정을 생략하고 이미지를 직접 배포하도록 수정합니다.

#### 2) 의존성 컨테이너 `mysql`의 포트 누락 오류
* **발생 에러**:
  ```text
  ERROR: (gcloud.run.compose.up) Error: failed to get container dependencies: container "backend" depends on container "mysql", but it has no ports defined
  ```
* **원인**: Cloud Run 배포 도구는 `depends_on: - mysql` 설정을 읽어 컨테이너 시작 순서(Startup Dependency)를 구성합니다. 이때 Cloud Run이 피의존 컨테이너(`mysql`)의 준비 상태를 추적하려면 해당 컨테이너의 포트 번호를 알아야 합니다.
* **해결**: `mysql` 서비스에 `ports: - "3306:3306"`을 반드시 명시해야 합니다.

#### 3) Cloud Run 시스템 예약 환경 변수 `PORT` 충돌 오류
* **발생 에러**:
  ```text
  ERROR: (gcloud.run.compose.up) spec.template.spec.containers[0].env: The following reserved env names were provided: PORT. These values are automatically set by the system.
  ```
* **원인**: Cloud Run에서 `PORT`는 **시스템 예약어(Reserved Environment Variable)**입니다. `environment:`에 사용자가 `PORT: "3000"`을 직접 정의하면 시스템 예약어와 충돌하여 배포가 거부됩니다.
* **해결**: `environment:` 목록에서 `PORT`를 제거합니다. Cloud Run이 `ports: - "8080:3000"`에 선언된 대상 포트(`3000`)를 기반으로 컨테이너 내부에 `PORT=3000` 환경 변수를 자동으로 주입합니다.

#### 4) `depends_on` 문법 호환성
* **해결**: `gcloud run compose`는 Docker Compose의 `condition: service_healthy` 같은 복합 객체 형식 대신, 단순 문자열 리스트(`depends_on: - mysql`)를 지원하므로 리스트 형식으로 지정해야 합니다.

---

### 7.5 `gcloud run compose up` 배포 실행 및 결과 확인

#### 1) 배포 실행
PowerShell에서 아래 명령어를 실행하여 Cloud Run에 배포합니다:
```powershell
gcloud run compose up .\cloudrun-compose.yml
```

* **리전(Region) 선택**: 프롬프트가 표시되면 서울 리전인 `[6] asia-northeast3`을 선택합니다.
* **외부 비인증 호출 허용 (Public Ingress)**:
  ```text
  Allow unauthenticated invocations to [getting-started-todo-app] (y/N)? y
  ```
  인터넷에서 누구나 웹 서비스에 접속할 수 있도록 `y`를 입력합니다.

#### 2) 배포 성공 결과
배포가 완료되면 전 세계 어디서나 접속 가능한 고유 HTTPS 도메인이 발급됩니다:
```text
✓ Deploying service 'getting-started-todo-app'... Done.
  ✓ Creating Revision...
  ✓ Routing traffic...
  ✓ Setting IAM Policy...
Service 'getting-started-todo-app' has been deployed.
Service URL: https://getting-started-todo-app-oxv4ieiwiq-du.a.run.app
```
* **접속 테스트**: 브라우저에서 `https://getting-started-todo-app-oxv4ieiwiq-du.a.run.app`로 접속하여 Todo 앱 정상 작동을 확인합니다.

---

### 7.6 `compose-prod-build.yml` 배포 시 한계 및 실패 원인
로컬 운영용 파일인 `compose-prod-build.yml`을 `gcloud run compose up .\compose-prod-build.yml`로 직접 배포할 수 **없는** 이유는 다음과 같습니다:
1. **Docker 데몬 소켓 마운트 불가**: `compose-prod-build.yml`의 Traefik 프록시는 `/var/run/docker.sock:/var/run/docker.sock` 볼륨 마운트를 필요로 합니다. 하지만 Cloud Run과 같은 샌드박스형 서버리스 컨테이너 환경에서는 호스트의 Docker 소켓 접근이 보안상 엄격히 차단됩니다.
2. **프록시 레이어의 중복**: Cloud Run은 이미 구글 글로벌 인프라 기반의 L7 인그레스 로드밸런서와 HTTPS 인증서 관리를 기본 제공하므로, 컨테이너 내부에 별도의 Traefik 리버스 프록시를 둘 필요가 없습니다.
3. **호스트 볼륨 마운트 미지원**: `compose-prod-build.yml`에 정의된 `todo-mysql-data:/var/lib/mysql`과 같은 Named Volume은 Cloud Run 환경에서 마운트할 수 없습니다.
* **결론**: Cloud Run 서버리스 배포에는 불필요한 프록시를 걷어내고 사이드카 및 포트 규약을 맞춘 전용 **`cloudrun-compose.yml`**을 반드시 사용해야 합니다.

---

### 7.7 Cloud Run 배포 서비스 정리 및 삭제 방법 (`gcloud run services delete`)

Cloud Run에 배포된 서비스는 사용하지 않더라도 삭제하지 않고 유지하면 불필요한 리소스가 남아있을 수 있습니다. 실습이나 테스트가 끝난 후에는 반드시 서비스를 삭제하여 정리해야 합니다.

Cloud Run에 배포된 서비스는 **`gcloud run services delete`** 명령어를 사용하여 삭제하셔야 합니다.

#### 1) 배포된 Cloud Run 서비스 목록 확인
현재 리전에 배포되어 있는 서비스 목록과 상태를 확인합니다:
```powershell
gcloud run services list --region asia-northeast3
```

#### 2) 배포된 서비스 삭제 방법
PowerShell에서 아래 명령어를 실행하여 Cloud Run에 생성된 서비스를 삭제합니다:
```powershell
gcloud run services delete <서비스_이름> --region asia-northeast3
```

* **실행 예시 (`getting-started-todo-app` 서비스 삭제)**:
  ```powershell
  gcloud run services delete getting-started-todo-app --region asia-northeast3
  ```
* 삭제 확인 프롬프트(`Do you want to continue (Y/n)?`)가 표시되면 `y`를 입력하여 삭제를 완료합니다.

---

## 8. Compose 파일 환경 비교 요약

| 구분 | 개발 환경 (`compose-build.yml`) | 로컬 프로덕션 빌드 (`compose-prod-build.yml`) | 원격 레지스트리 배포 (`docker-compose-prod.yml`) | GCP Cloud Run 배포 (`cloudrun-compose.yml`) |
| :--- | :--- | :--- | :--- | :--- |
| **실행 인프라** | 로컬 Docker Desktop | 로컬 Docker Desktop / 온프레미스 VM | 로컬 Docker / 프로덕션 서버 / VM | GCP Cloud Run (서버리스 컨테이너) |
| **이미지 공급** | 로컬 소스 빌드 (`backend-dev`, `client-dev`) | 로컬 소스 빌드 (`final`) | 원격 레지스트리 (Docker Hub / GHCR / GCP) | 원격 레지스트리 (GCP Artifact Registry) |
| **실행 명령어** | `docker compose -f compose-build.yml up --watch` | `docker compose -f compose-prod-build.yml up -d --build` | `docker compose -f docker-compose-prod.yml up -d` | `gcloud run compose up .\cloudrun-compose.yml` |
| **사전 다운로드** | 불필요 (로컬 빌드) | 불필요 (로컬 빌드) | `docker compose -f docker-compose-prod.yml pull` | 불필요 (Cloud Run 배포 시 자동 풀) |
| **포트 매핑** | 프록시 80 ➔ 5173(Vite) / 3000(API) | 프록시 80/443 ➔ 백엔드 3000 | 프록시 80/443 ➔ 백엔드 3000 | Cloud Run 인그레스 8080 ➔ 컨테이너 3000 |
| **리버스 프록시** | Traefik v3.6 컨테이너 포함 | Traefik v3.6 컨테이너 포함 | Traefik v3.6 컨테이너 포함 | 미포함 (Cloud Run 자체 인그레스 처리) |
| **코드 반영** | Compose Watch를 통한 실시간 핫 리로드 | 빌드 시점에 코드 및 정적 자산 고정 | 레지스트리 태그/버전 관리 (불변 이미지) | Artifact Registry 사전 빌드 이미지 배포 |
| **프론트엔드 서빙** | Vite 개발 서버 (포트 5173) | Express 정적 파일 서빙 (`/src/static`) | Express 정적 파일 서빙 (`/src/static`) | Express 정적 파일 서빙 (`/src/static`) |
| **데이터베이스** | MySQL 9.3 (로컬 볼륨 영속화) | MySQL 9.3 (로컬 볼륨 영속화) | MySQL 9.3 (로컬 볼륨 영속화) | MySQL 9.3 사이드카 컨테이너 (또는 Cloud SQL) |
| **데이터 영속성** | `todo-mysql-data` 호스트 볼륨 | `todo-mysql-data` 호스트 볼륨 | `todo-mysql-data` 호스트 볼륨 | 인스턴스 단위 휘발성 (운영 시 Cloud SQL 권장) |
| **서비스 종료/정리** | `docker compose -f compose-build.yml down` | `docker compose -f compose-prod-build.yml down` | `docker compose -f docker-compose-prod.yml down` | `gcloud run services delete <서비스이름>` |

---

## 9. 자주 발생하는 문제 및 해결 방법 (Troubleshooting)

### Q1. 브라우저 접속 시 `404 page not found` 에러가 발생합니다.
* **원인 1 (클라우드 VM / 외부 IP 접속 시)**: Traefik 라우팅 규칙이 `Host('localhost')`로 제한되어 있는 경우, 브라우저가 전송하는 `Host: 136.119.235.11`(외부 IP) 헤더와 일치하지 않아 라우팅 대상을 찾지 못하고 Traefik 기본 404를 반환합니다.
  * **해결**: 특정 호스트 이름 대신 모든 IP 및 도메인을 수용할 수 있도록 라우팅 규칙을 `PathPrefix('/')`로 설정합니다.
    ```yaml
    labels:
      traefik.http.routers.backend.rule: PathPrefix(`/`)
    ```
* **원인 2 (DB 준비 전 백엔드 기동 실패)**: MySQL 데이터베이스 준비 전에 백엔드가 먼저 기동되어 DB 연결 실패로 백엔드 컨테이너가 종료(`exit`)된 경우
  * **해결**: `backend` 서비스에 `depends_on: mysql: condition: service_healthy`가 적용되어 있는지 확인합니다.

### Q2. GCP VM 방화벽에서 접속이 안 되는 경우
* **확인**: GCP VPC 네트워크 방화벽 규칙에서 **TCP 80 포트(HTTP)** 수신(Ingress) 트래픽이 허용되어 있는지 확인해야 합니다. (대상 태그: `http-server` 등)

### Q3. `gcloud run compose up` 실행 시 `PORT` 예약어 오류가 발생합니다.
* **오류 메시지**: `The following reserved env names were provided: PORT. These values are automatically set by the system.`
* **해결**: `cloudrun-compose.yml`의 `environment:`에서 `PORT` 항목을 삭제합니다. Cloud Run 시스템이 `ports:`의 타깃 포트를 읽어 컨테이너 내부에 `PORT` 환경 변수를 자동 주입합니다.

### Q4. `gcloud run compose up` 실행 시 `mysql has no ports defined` 오류가 발생합니다.
* **오류 메시지**: `failed to get container dependencies: container "backend" depends on container "mysql", but it has no ports defined`
* **해결**: Cloud Run이 의존성 컨테이너의 준비 상태를 추적할 수 있도록 `mysql` 서비스에 `ports: - "3306:3306"`을 명시해야 합니다.

### Q5. Cloud Run 배포 후 컨테이너 기동 실패 (`Container failed to start and listen on the port`)
* **원인**: Cloud Run이 할당한 `PORT`에서 Express 서버가 리슨하지 못했거나, Dockerfile에 잘못된 포트가 명시된 경우.
* **해결**:
  1. 백엔드 코드(`backend/src/index.js`)에서 `const PORT = process.env.PORT || 3000;`와 같이 `process.env.PORT`를 우선 참조하고 있는지 확인합니다.
  2. `cloudrun-compose.yml`의 포트 매핑(`8080:3000`)과 컨테이너 내부 포트가 일치하는지 확인합니다.

### Q6. `gcloud run compose up` 실행 시 Cloud Build 권한 오류 (`403 PERMISSION_DENIED`)
* **오류 메시지**: `ERROR: (gcloud.run.compose.up) HttpError accessing <https://cloudbuild.googleapis.com/...>: status 403, content: "The caller does not have permission", "status": "PERMISSION_DENIED"`
* **원인**: `cloudrun-compose.yml`에 `build:` 섹션이 포함되어 있어 Cloud Build API를 통해 원격 빌드를 시도했으나, 계정에 Cloud Build 실행 권한이 없는 경우.
* **해결**: 로컬에서 이미지를 빌드한 뒤 GCP Artifact Registry로 푸시(`docker push`)하고, `cloudrun-compose.yml`에서 `build:` 섹션을 `image: asia-northeast3-docker.pkg.dev/...`로 교체하여 사전 빌드된 이미지를 직접 배포합니다.

### Q7. `docker compose up` 실행 시 80번 포트 충돌 오류 (`port is already allocated`)
* **오류 메시지**: `Bind for 0.0.0.0:80 failed: port is already allocated`
* **원인**: 이전에 실행한 다른 Docker 컨테이너나 호스트 머신(Windows IIS 등)이 80번 포트를 이미 점유하고 있는 경우.
* **해결**: 
  1. 실행 중인 컨테이너 정리: `docker compose down` 및 `docker compose -f docker-compose-prod.yml down`
  2. Windows 웹 서비스(IIS) 중지: `net stop w3svc /y`
  3. 또는 `docker-compose-prod.yml`의 `proxy` 외부 포트를 `8080:80` 등으로 변경.

### Q8. Docker Compose 실행 시 YAML 들여쓰기 오류 (`did not find expected key`)
* **오류 메시지**: `go-yaml load error in parser (while parsing a block mapping) ... did not find expected key`
* **원인**: YAML 파일 내에서 공백(들여쓰기) 칸 수가 일치하지 않는 경우 (예: 상위 키는 2칸, 하위 속성은 4칸이어야 하나 5칸 등 불일치).
* **해결**: `backend:` 하위의 `image:`, `environment:`, `depends_on:` 등의 들여쓰기 칸 수를 공백 4칸으로 일관되게 정렬합니다.

---

## 10. 주요 유용한 Docker 명령어 모음

```bash
# 현재 실행 중인 컨테이너 상태 및 헬스체크 확인
docker compose -f compose-build.yaml ps

# 캐시 없이 전체 이미지 새로 빌드
docker compose -f compose-build.yaml build --no-cache

# DB 볼륨을 포함하여 완전 초기화 후 재시작
docker compose -f compose-build.yaml down -v
docker compose -f compose-build.yaml up --watch
```
