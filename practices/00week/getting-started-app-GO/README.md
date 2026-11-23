# Getting started

This repository is a sample application for users following the getting started guide at https://docs.docker.com/get-started/.

The application is based on the application from the getting started tutorial at https://github.com/docker/getting-started.

---

## 🚀 Go 애플리케이션 실행 방법

본 프로젝트는 **Go 언어(Gin 프레임워크)** 기반의 Todo 백엔드 및 정적 파일 서빙 애플리케이션입니다.

### 방법 1. 로컬 환경에서 직접 실행 (Go CLI)

터미널(PowerShell 또는 CMD)에서 프로젝트 루트 디렉터리로 이동한 후 실행합니다.

#### 1) 의존성 패키지 동기화 (최초 1회)
```powershell
go mod tidy
```

#### 2) 서버 직접 실행
```powershell
go run .
```
*(또는 `go run main.go`)*

#### 3) (선택) 바이너리 빌드 후 실행
```powershell
# 실행 파일 빌드
go build -o app.exe .

# 실행
.\app.exe
```

---

### 방법 2. Docker 컨테이너로 실행

#### 1) Docker 이미지 빌드
```powershell
docker build -t getting-started-go .
```

#### 2) 컨테이너 실행 (3000번 포트 연결)
```powershell
docker run -dp 3000:3000 getting-started-go
```

---

## 🌐 브라우저 접속 및 확인

서버 실행 후 웹 브라우저에서 아래 주소로 접속합니다:

- **접속 URL:** [http://localhost:3000](http://localhost:3000)
- **주요 API 엔드포인트:**
  - `GET /items` - 할 일 목록 조회
  - `POST /items` - 할 일 추가
  - `PUT /items/:id` - 할 일 상태 변경
  - `DELETE /items/:id` - 할 일 삭제