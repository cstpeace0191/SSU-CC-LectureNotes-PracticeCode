# Getting Started Todo App
윈도우즈 환경에서 동작 시키기 위해,
'node.js' 설치 필요
'node.js' 설치시에 ('npm' 은 자동 설치됨)

필요시에, vscode 설치 (반드시 필요한 것은 아님)
이후 아래와 같이 backend 서버 프로그램 환경 설치  및 기동 시작 , client 프로그램 환경 설치 , CORS 문제 해결을 위해, client 폴더에 있는
'vite.config.js' 아래 지시대로 수정 및 기동 시작


## Backend 서버 프로그램 환경 설치 및 기동 시작

cd getting-started-todo-app/backend
npm install 
npm run dev

### 서버는 http://localhost:3000 에서 동작 시작

## Client 개발 모드 수행
### 프로그램 환경 설치, 'vite.config.js' 수정 및 기동 시작
cd getting-started-todo-app/client

### 주어진 'vite.config.js' 을 열어 다음을 아래와 같이 수정한 후에 저장
 ' export default defineConfig({
    plugins: [react()],
  
  });' 
====>

export default defineConfig({
    plugins: [react()],
    server: {
    proxy: {
      '/api': 'http://localhost:3000'
    }
  }});

### 다음과 같이 수행
npm install 
npm run dev

#### 웹브라우저에서
 http://localhost:5173/

## Client 프로덕션 모드 수행

### 1. Client 빌드 및 Backend 정적 폴더 자동 복사
```bash
cd getting-started-todo-app/client
npm install // 이미 'npm install' 수행한 경우에는 수행할 필요 없음
npm run build
```
> **참고**: `client/package.json`의 `build` 스크립트에 `vite build && node -e "require('fs').cpSync('dist', '../backend/src/static', {recursive: true})"` 가 설정되어 있어, 빌드 완료 시 `dist` 폴더의 내용이 `backend/src/static` 폴더로 자동 복사됩니다.

---

### 실행 방법 1: Backend(Express)에서 직접 서빙하기 (간편 실행)
`backend/src/index.js`에 이미 `app.use(express.static(__dirname + '/static'))` 설정이 되어 있으므로, `npm run build` 후 백엔드 서버만 실행해도 프론트엔드와 백엔드가 함께 동작합니다.

```bash
cd getting-started-todo-app/backend
npm run dev # 또는 node src/index.js
```
- **웹브라우저 접속**: `http://localhost:3000/`

---

### 실행 방법 2: 실제 운영 서버 Nginx 기반으로 수행하기 (Reverse Proxy)
1. Nginx 다운로드(https://nginx.org/en/download.html) 및 압축 해제(설치).
2. `client/dist` (또는 `backend/src/static`) 폴더의 내용물을 Nginx 설치 폴더의 `html` 폴더(`.../nginx-x.xx.x/html`)에 복사.
3. 프로젝트 루트의 `nginx-GettingStarted-App-todo.conf` 파일명을 `nginx.conf`로 변경하여 `.../nginx-x.xx.x/conf/nginx.conf` 파일로 대체.
4. 백엔드 서버 실행 (`cd getting-started-todo-app/backend` 후 `npm run dev`)
5. Nginx 실행 (`nginx.exe` 실행)
6. **웹브라우저 접속**: `http://localhost/` (기본 80 포트)

### 사실, 'nginx-GettingStarted-App-todo.conf' 는 '.../nginx-x.xx.x/conf/nginx.conf' 을 다음과 같이 수정한 것입니다. 

#### 왜 수정이 필요한가

`client/src`의 프론트엔드 코드(`fetch('/api/items')` 등)는 절대 URL이 아니라 `/api/...` **상대 경로**로 백엔드를 호출한다. 개발 모드에서는 이 문제를 `vite.config.js`의 `server.proxy`(위에서 설정한 `'/api': 'http://localhost:3000'`)가 해결해줬다 — Vite Dev Server가 `/api` 요청만 골라 Express 백엔드(`:3000`)로 포워딩해주는 **Reverse Proxy** 역할을 했기 때문이다.

`npm run build`로 만든 정적 파일(`dist/`)을 Nginx의 `html` 폴더에 두고 서비스하면, 이번엔 Nginx가 그 역할을 대신해야 한다. 기본 `nginx.conf`는 **정적 파일만** 서빙할 뿐 `/api`가 뭔지 전혀 모르기 때문에, 아무 설정 없이 그대로 쓰면 브라우저가 `fetch('/api/items')`를 호출할 때 Nginx가 `/api/items`라는 파일을 `html` 폴더에서 찾다가 없으니 404를 반환한다. 즉, 개발 모드의 Vite proxy와 정확히 같은 이유로, 프로덕션에서는 Nginx가 `/api`로 오는 요청을 백엔드(`http://localhost:3000`)로 포워딩하도록 **reverse proxy 설정을 추가**해야 한다.

#### 어떻게 수정했는가 (핵심 변경 부분)

기본 `nginx.conf`의 `server { ... }` 블록 안에 다음 `location /api { ... }` 블록을 추가한 것이 핵심이다('nginx -GettingStarted-App-todo.conf' 참조).

```nginx
location /api {
    # If backend is another container: use its Docker DNS name and port
    proxy_pass http://localhost:3000;   # note the trailing slash!
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_read_timeout 60s;
}
```


각 지시어의 의미는 다음과 같다.

- `location /api { ... }` : 요청 경로가 `/api`로 시작하는 요청만 이 블록의 규칙을 적용한다(그 외 요청은 `location /`이 처리해 `html` 폴더의 정적 파일을 서빙).
- `proxy_pass http://localhost:3000;` : 이 위치로 들어온 요청을 백엔드 Express 서버(`backend/src/index.js`, `app.listen(3000)`)로 그대로 전달한다. Vite의 `server.proxy` 설정과 동일한 역할이다.
- `proxy_set_header Host $host;` : 백엔드로 요청을 전달할 때 원래 브라우저가 요청했던 `Host` 헤더(예: `localhost`)를 그대로 유지해서 넘겨준다(백엔드가 `Host` 헤더를 검사하는 경우를 대비).
- `proxy_set_header X-Forwarded-For $remote_addr;` : 실제 클라이언트(브라우저)의 IP를 `X-Forwarded-For` 헤더에 담아 백엔드로 전달한다. Nginx를 거치면 백엔드 입장에서는 모든 요청이 Nginx(로컬호스트)에서 온 것처럼 보이므로, 원래 클라이언트 IP를 알고 싶다면 이 헤더가 필요하다.
- `proxy_read_timeout 60s;` : 백엔드로부터 응답을 기다리는 최대 시간을 60초로 늘려, 백엔드 처리(DB 조회 등)가 조금 오래 걸려도 Nginx가 중간에 타임아웃으로 끊어버리지 않게 한다.

이렇게 하면, 브라우저는 항상 Nginx(`:80`)에만 접속하고, Nginx가 요청 경로를 보고
- 정적 리소스(`/`, `index.html`, JS/CSS 번들, 이미지 등) → `html` 폴더(=`dist`의 내용)에서 직접 서빙
- `/api/*` → 백엔드(`http://localhost:3000`)로 프록시

로 나눠서 처리한다. 그 결과 프론트엔드 코드는 개발 모드와 마찬가지로 `fetch('/api/items')`처럼 상대 경로만으로 백엔드를 호출할 수 있고, 브라우저 입장에서는 프론트/백엔드가 하나의 오리진(`http://localhost`)에서 서비스되는 것처럼 보인다.

(참고: `nginx-GettingStarted-App-todo.conf`에는 이 `/api` 블록 외에도 `location /phpmyadmin { ... }`, `location ~ \.php$ { ... }` 같은 PHP/phpMyAdmin 관련 블록이 함께 들어 있는데, 이는 다른 프로젝트에서 재사용된 설정 조각으로 Node.js/Express 기반인 이 `getting-started-todo-app`에는 실제로 필요하지 않다. 이 프로젝트를 위해 의미 있는 핵심 변경은 위의 `location /api` 블록 하나뿐이다.)

---

# Docker Compose를 통한 시스템 빌드 및 실행

윈도우즈 환경에서 **Docker Desktop**을 사용하여 Node.js나 Nginx, MySQL을 로컬에 직접 설치하지 않고도 컨테이너 기반으로 전체 풀스택 애플리케이션을 빌드 및 구동할 수 있습니다.

> ⚠️ **주의 (명령어 실행 위치)**:
> `compose.yaml`, `Dockerfile` 등 Docker 설정 파일은 프로젝트 **최상위 루트 디렉터리(`getting-started-todo-app/`)** 에 위치합니다.
> `backend`나 `client` 폴더 내부가 아닌 **반드시 프로젝트 루트 폴더에서 명령어를 실행**해야 합니다.

---

## 1. Docker Compose 개발 환경 실행 (`compose.yaml`)

개발 환경에서는 소스 코드 변경 시 컨테이너 내부로 즉시 동기화(Compose Watch)되며, 리버스 프록시(Traefik)를 통해 프론트엔드와 백엔드, DB 관리도구를 한 번에 연동합니다.

### 서비스 구성
- **proxy (Traefik v3.6)**: 80번 포트로 들어오는 요청을 라우팅
  - `http://localhost/` ➡️ `client` (React Vite 개발 서버, 5173 포트)
  - `http://localhost/api` ➡️ `backend` (Express API 서버, 3000 포트)
  - `http://db.localhost/` ➡️ `phpmyadmin` (MySQL 관리 도구, 80 포트)
- **client**: `Dockerfile`의 `client-dev` 타깃 (Vite Dev Server, 실시간 코드 동기화)
- **backend**: `Dockerfile`의 `backend-dev` 타깃 (Nodemon + Express, 실시간 코드 동기화)
- **mysql**: MySQL 9.3 공식 이미지 (데이터는 `todo-mysql-data` 볼륨에 영속 저장)
- **phpmyadmin**: MySQL 웹 GUI 관리자

### 실행 명령어 (프로젝트 루트 디렉터리)
```bash
# 1. 프로젝트 최상위 루트로 이동
cd getting-started-todo-app

# 2. 백그라운드에서 빌드 및 컨테이너 전체 실행
docker compose -f compose.yaml up -d --build

# (선택) 소스 코드 변경 사항을 컨테이너와 실시간 동기화(Watch)하려면
docker compose watch
```

### 접속 주소
- **Todo App (프론트/백엔드 통합)**: [http://localhost](http://localhost)
- **phpMyAdmin (DB 관리자)**: [http://db.localhost](http://db.localhost) (기본 계정: `root` / 비밀번호: `secret`)

### 컨테이너 중지 및 종료
```bash
# 컨테이너 중지
docker compose down

# (선택) 데이터 볼륨(DB 데이터)까지 완전히 삭제하고 초기화할 때
docker compose down -v
```

---

## 2. Docker Compose 프로덕션 환경 실행 (`compose-prod-build.yml`)

프로덕션 환경에서는 Multi-stage `Dockerfile`의 `final` 스테이지를 통해 React 클라이언트를 빌드하여 Express 백엔드의 `src/static` 폴더에 번들링한 후 단일 컨테이너로 서빙합니다.

### 서비스 구성
- **proxy (Traefik)**: 80번 포트로 수신된 모든 `localhost` 요청을 `backend` 프로덕션 컨테이너로 전달
- **backend**: Node.js 22 기반 통합 프로덕션 컨테이너 (정적 파일 + REST API + MySQL 연결)
- **mysql**: MySQL 8.0.38 공식 이미지

### 실행 명령어 (프로젝트 루트 디렉터리)
```bash
# 1. 프로젝트 최상위 루트로 이동
cd getting-started-todo-app

# 2. 프로덕션 빌드 및 실행
docker compose -f compose-prod-build.yml up -d --build
```

### 접속 주소
- **Todo App (프로덕션)**: [http://localhost](http://localhost)

### 프로덕션 컨테이너 종료
```bash
docker compose -f compose-prod-build.yml down
```

---

## 3. 단일 Dockerfile로 프로덕션 컨테이너 단독 빌드 및 실행

Docker Compose 없이 단일 `Dockerfile`만으로도 전체 앱을 빌드하고 실행할 수 있습니다 (기본 SQLite DB 사용).

```bash
# 프로젝트 루트에서 이미지 빌드
docker build -t todo-app .

# 컨테이너 실행 (3000 포트 매핑)
docker run -dp 3000:3000 todo-app
```
- **접속 주소**: [http://localhost:3000](http://localhost:3000)

---

## 💡 자주 발생하는 오류 및 해결 팁
1. **`The system cannot find the file specified` 에러**:
   - `backend`나 `client` 폴더 안에서 `docker compose`를 실행한 경우 발생합니다.
   - `cd ..` 명령으로 프로젝트 최상위 루트 디렉터리로 이동한 후 다시 실행하세요.
2. **포트 80 충돌 (`bind: address already in use`)**:
   - 로컬에 이미 Nginx나 IIS, Apache 또는 이전 Docker 컨테이너가 80번 포트를 점유 중인 경우 발생합니다.
   - 기존 프로세스를 중지하거나 작업 관리자에서 80 포트를 사용하는 서비스를 종료 후 실행하세요.

