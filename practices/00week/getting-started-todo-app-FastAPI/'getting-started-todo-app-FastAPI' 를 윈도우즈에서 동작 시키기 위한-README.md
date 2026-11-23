# Getting Started Todo App (FastAPI + React)
윈도우즈 환경에서 동작시키기 위한 전체 가이드입니다.

---

## 🛠️ 1. 사전 환경 설치
1. **Node.js 설치**: [nodejs.org](https://nodejs.org/) (npm은 자동 설치됨)
2. **Python 3.10+ 설치**: [python.org](https://www.python.org/)
3. 필요 시 VS Code 설치 (선택 사항)

---

## 🐍 2. Backend (FastAPI + Uvicorn) 환경 설치 및 기동 시작

### 2.1 가상환경 생성 및 패키지 설치
PowerShell 또는 CMD 터미널을 열고 다음을 수행합니다:

```powershell
cd backend
python -m venv .venv

# Windows PowerShell의 경우:
.\.venv\Scripts\Activate.ps1
# (만약 스크립트 실행 권한 오류가 발생하면: Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 실행 후 다시 시도)

# 또는 Windows CMD의 경우:
# .\.venv\Scripts\activate.bat

pip install -r requirements.txt
```

### 2.2 백엔드 서버 실행
```powershell
# 방법 1: uvicorn 명령어로 실행 (코드 변경 시 자동 리로드)
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload

# 또는 방법 2: main.py 실행
python main.py
```

- **백엔드 서버 주소**: `http://localhost:3000`
- **Swagger 대화형 API 문서**: `http://localhost:3000/docs`
- **단위 테스트 실행**: `pytest`

---

## 💻 3. Client 개발 모드 수행 (`npm run dev`)

코드 수정 시 브라우저에 즉시 반영되는 HMR 개발 모드입니다.

### 3.1 `vite.config.js` 프록시 설정 확인
Windows 환경에서 Node의 IPv6(`::1`) 해석 문제를 방지하기 위해 `client/vite.config.js`의 프록시 타깃이 `http://127.0.0.1:3000`으로 설정되어 있는지 확인합니다:

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:3000',
                changeOrigin: true,
            },
        },
    },
});
```

### 3.2 패키지 설치 및 개발 서버 기동
새 터미널 창을 열고 실행합니다:

```powershell
cd client
npm install   # 최초 1회만
npm run dev
```

- **웹 브라우저 접속**: [http://localhost:5173/](http://localhost:5173/)

---

## 🚀 4. Client 프로덕션 모드 수행 (`npm run build`)

### 4.1 클라이언트 빌드 및 정적 파일 복사
```powershell
cd client
npm run build
```
> 💡 `npm run build`를 실행하면 React 앱이 번들링되어 `dist/`에 생성된 후, `copy-build.js` 스크립트를 통해 `backend/src/static/` 폴더로 자동 복사됩니다.

---

### 4.2 프로덕션 실행 방식 선택

#### [옵션 A] FastAPI 내장 정적 파일 서빙 (가장 간편한 방법)
별도의 Nginx 설치 없이 백엔드 서버 하나만으로 프론트엔드와 API를 모두 서비스합니다:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn src.main:app --host 0.0.0.0 --port 3000 --reload
# 또는: python main.py
```
- **웹 브라우저 접속**: [http://localhost:3000/](http://localhost:3000/)

---

#### [옵션 B] Nginx 기반 운영 서버 서빙
1. **Nginx 다운로드 및 설치**: [nginx.org/en/download.html](https://nginx.org/en/download.html) 에서 Windows 버전 zip 다운로드 후 압축 해제.
2. **정적 파일 복사**: `client/dist/` 폴더 내의 파일들을 Nginx의 `html/` 폴더(`.../nginx-x.xx.x/html`)로 복사.
3. **Nginx 설정 적용**: `nginx -GettingStarted-App-todo.conf`를 참고하여 Nginx의 `conf/nginx.conf`를 수정.

##### 핵심 Nginx 설정 내용 (`location /api` 리버스 프록시)
```nginx
location /api {
    proxy_pass http://127.0.0.1:3000;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $remote_addr;
    proxy_read_timeout 60s;
}
```

- **`proxy_pass http://127.0.0.1:3000;`**: 브라우저의 `/api/*` 요청을 백엔드 FastAPI 서버(`http://127.0.0.1:3000`)로 포워딩합니다.
- **`proxy_set_header Host $host;`**: 클라이언트가 요청한 원래의 Host 헤더를 백엔드로 넘겨줍니다.
- **`proxy_set_header X-Forwarded-For $remote_addr;`**: 실제 클라이언트 브라우저의 IP를 백엔드로 전달합니다.

4. **실행**:
   - 백엔드 실행: `cd backend` -> `uvicorn src.main:app --host 0.0.0.0 --port 3000`
   - Nginx 실행: Nginx 폴더에서 `nginx.exe` 실행
5. **웹 브라우저 접속**: [http://localhost/](http://localhost/) (80번 포트)
