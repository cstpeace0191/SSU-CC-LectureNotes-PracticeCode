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

## Client 프로그램 환경 설치, 'vite.config.js' 수정 및 기동 시작
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