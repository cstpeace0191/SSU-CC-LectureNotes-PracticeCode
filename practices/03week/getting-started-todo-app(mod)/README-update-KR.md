# Getting Started Todo App (Docker 개발 & 배포 가이드)

이 프로젝트는 Docker의 모범 사례(Best Practices)를 적용한 샘플 Todo 리스트 애플리케이션입니다. 
Dockerfile의 멀티스테이지 빌드(Multi-stage build), 환경별 Docker Compose 파일 분리(`compose-build.yaml`, `compose-prod-build.yml`), Compose Watch를 활용한 실시간 핫 리로드(Hot Reload), Traefik 리버스 프록시 라우팅, 그리고 Vite 개발 서버 설정을 체계적으로 정리한 문서입니다.

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

## 5. Docker Compose 기반 프로덕션 빌드 및 실행 가이드 (`compose-prod-build.yml`)

`compose-prod-build.yml`은 배포용 단일 번들 이미지를 빌드하여 운영 환경과 동일하게 실행합니다.

### 5.1 서비스 구성 요약
* **`backend`**: Dockerfile의 `final` 타깃 빌드 (React 정적 빌드 산출물이 내장된 단일 컨테이너로, 포트 `80:3000` 직접 매핑되어 프록시 없이 즉시 서빙)
* **`mysql`**: MySQL 9.3 데이터베이스 (헬스체크 적용 및 `todo-mysql-data` 볼륨 영속화)
*(프로덕션 환경에서는 불필요한 프록시 오버헤드, 개발 서버 및 phpMyAdmin 컨테이너를 제외하여 보안성과 안정성을 극대화합니다)*

### 5.2 실행 명령어

```bash
# 프로덕션 이미지 빌드 및 백그라운드 실행
docker compose -f compose-prod-build.yml up -d --build
```

### 5.3 접속 및 확인
* **Todo 웹 애플리케이션**: [http://localhost](http://localhost) 또는 [http://127.0.0.1](http://127.0.0.1)
* **실행 로그 실시간 확인**:
  ```bash
  docker compose -f compose-prod-build.yml logs -f
  ```

### 5.4 프로덕션 환경 종료
```bash
docker compose -f compose-prod-build.yml down
```

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

## 7. Compose 파일 환경 비교 요약

| 구분 | 개발 환경 (`compose-build.yaml`) | 프로덕션 환경 (`compose-prod-build.yml`) |
| :--- | :--- | :--- |
| **빌드 타깃** | `backend-dev`, `client-dev` (개별 실행) | `final` (단일 통합 번들) |
| **코드 반영** | Compose Watch를 통한 실시간 핫 리로드 | 빌드 시점에 코드 및 정적 자산 고정 |
| **프론트엔드 서빙** | Vite 개발 서버 (포트 5173) | Node.js Express 정적 파일 (`/src/static`) 서빙 |
| **데이터베이스 도구** | phpMyAdmin 포함 (`http://db.localhost`) | 미포함 (보안 및 경량화) |
| **주요 목적** | 빠른 기능 개발, 테스트, 디버깅 | 배포 검증, 운영 성능 및 보안 최적화 |

---

## 8. 자주 발생하는 문제 및 해결 방법 (Troubleshooting)

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

---

## 9. 주요 유용한 Docker 명령어 모음

```bash
# 현재 실행 중인 컨테이너 상태 및 헬스체크 확인
docker compose -f compose-build.yaml ps

# 캐시 없이 전체 이미지 새로 빌드
docker compose -f compose-build.yaml build --no-cache

# DB 볼륨을 포함하여 완전 초기화 후 재시작
docker compose -f compose-build.yaml down -v
docker compose -f compose-build.yaml up --watch
```
