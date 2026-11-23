# GCP Cloud Run 개요 및 Todo 애플리케이션 배포 워크플로우

본 문서는 **GCP Cloud Run**의 핵심 개념 및 아키텍처적 특징을 설명하고, 현재 프로젝트([`getting-started-todo-app`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app))의 프로덕션 컨테이너 이미지를 Cloud Run에 배포하는 전체 엔드투엔드(End-to-End) 절차를 안내합니다.

---

## 1. GCP Cloud Run 개요

### 1.1 Cloud Run이란?
**GCP Cloud Run**은 Google Cloud에서 제공하는 **완전 관리형 서버리스 컨테이너 플랫폼(Serverless Container Platform)**입니다.  
컨테이너 이미지(Docker/OCI 호환)만 제공하면 서버 프로비저닝, 클러스터 관리, OS 패치, 네트워크 설정 등의 인프라 관리 없이 즉시 HTTPS 엔드포인트로 서비스를 구동할 수 있습니다.

### 1.2 핵심 특징 및 장점

1. **완전 관리형 서버리스 (No Ops)**
   - GKE처럼 쿠버네티스 노드나 컨트롤 플레인을 관리할 필요가 없으며, VM 관리도 전혀 필요하지 않습니다.
2. **요청 기반 자동 확장 (Scale-to-Zero)**
   - 트래픽이 없을 때는 인스턴스 수가 **0개**로 축소되어 유휴 비용이 전혀 발생하지 않습니다.
   - 트래픽이 폭증하면 수 초 내에 수백~수천 개의 컨테이너 인스턴스로 자동 확장(Scale-out)됩니다.
3. **기본 무료 HTTPS 및 도메인 자동 발급**
   - 배포 즉시 Google이 관리하는 고유의 HTTPS URL(`https://<서비스명>-<해시>-<리전>.a.run.app`)과 SSL/TLS 인증서가 무료로 자동 할당됩니다. (Traefik이나 Nginx 같은 별도 리버스 프록시 불필요)
4. **동적 포트 바인딩 (`PORT` 환경변수)**
   - Cloud Run은 실행 시 컨테이너에 **`PORT` 환경변수(기본값: 8080)**를 자동으로 주입합니다.
   - 앞서 [`backend/src/index.js`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/backend/src/index.js)에서 구현한 `const PORT = process.env.PORT || 3000;` 코드 덕분에 별도 수정 없이 Cloud Run의 포트를 즉시 수용합니다.
5. **초당 과금 (Pay-per-use)**
   - 요청을 처리하는 CPU/메모리 동작 시간 동안에만 100ms 단위로 요금이 청구됩니다.

---

## 2. 클라우드 인프라 비교: VM vs GKE vs Cloud Run

| 구분 | GCP Compute Engine (VM) | GKE (Kubernetes) | **GCP Cloud Run** |
| :--- | :--- | :--- | :--- |
| **서비스 형태** | IaaS (가상 머신) | CaaS (컨테이너 오케스트레이션) | **Serverless PaaS** |
| **운영 부담** | 높음 (OS, Docker 직접 관리) | 보통~높음 (K8s 매니페스트 관리) | **최소 (이미지만 배포)** |
| **인그레스/SSL** | Traefik/Nginx 직접 설치 필요 | Ingress / Cloud Load Balancer 필요 | **자동 제공 (Google 관리형 HTTPS)** |
| **비용 구조** | 24시간 VM 실행 비용 고정 청구 | 노드 인스턴스 비용 지속 청구 | **요청 처리 시간에만 종량제 청구 (0개 축소 가능)** |
| **적합한 용도** | 상태 유지(Stateful), 복잡한 데몬 | 대규모 마이크로서비스, 정교한 오케스트레이션 | **웹 앱, REST API, 이벤트 기반 백엔드** |

---

## 3. 사전 요구사항 및 배포 환경 정보

| 항목 | 설정값 | 비고 |
| :--- | :--- | :--- |
| **GCP Project ID** | `ssu-agent-vertex-509708` | 작업 GCP 프로젝트 ID |
| **배포 리전 (Region)** | `asia-northeast3` | 서울 리전 |
| **Cloud Run 서비스명** | `todo-backend` | 생성할 서비스 이름 |
| **사용 이미지** | `asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod` | Artifact Registry에 푸시된 이미지 |
| **대체 이미지** | `ssucloud/getting-started-todo-app:todo-backend` | Docker Hub 공식 공개 이미지 |

---

## 4. Cloud Run 배포 절차

### 1단계: 필수 GCP API 활성화
Cloud Run 서비스를 사용하기 위해 API를 활성화합니다:

```powershell
# 1. Cloud Run API 활성화
gcloud services enable run.googleapis.com --project=ssu-agent-vertex-509708
```

---

### 2단계: 컨테이너 이미지 준비 (Artifact Registry)
이미 [`GKE-Workflow.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/GKE-Workflow.md)에서 빌드 및 푸시한 Artifact Registry 이미지를 그대로 재사용합니다.

```powershell
# (필요 시) 이미지 재빌드 및 푸시
docker build -t asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod --target final .
docker push asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod
```

> [!TIP]
> Docker Hub의 공개 이미지를 직접 배포할 수도 있습니다:
> `--image=docker.io/ssucloud/getting-started-todo-app:todo-backend`

---

### 3단계: Cloud Run에 서비스 배포 (`gcloud run deploy`)

#### 옵션 A: 로컬/인메모리 SQLite 모드 (빠른 배포 및 단독 검증)
데이터베이스 환경변수를 생략하면 [`backend/src/persistence/`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/backend/src/persistence/)의 기본 SQLite가 사용되어 즉시 동작을 확인할 수 있습니다:

```powershell
gcloud run deploy todo-backend `
    --image=asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod `
    --platform=managed `
    --region=asia-northeast3 `
    --allow-unauthenticated `
    --project=ssu-agent-vertex-509708
```

#### 옵션 B: MySQL 연동 모드 (GCP Cloud SQL 또는 VM MySQL 연결)
MySQL 데이터베이스를 사용하는 경우 환경 변수를 함께 주입하여 배포합니다:

```powershell
gcloud run deploy todo-backend `
    --image=asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod `
    --platform=managed `
    --region=asia-northeast3 `
    --allow-unauthenticated `
    --set-env-vars="MYSQL_HOST=<MYSQL_IP>,MYSQL_USER=root,MYSQL_PASSWORD=secret,MYSQL_DB=todos" `
    --project=ssu-agent-vertex-509708
```

* 주요 옵션 설명:
  * `--allow-unauthenticated`: 웹 브라우저에서 인증 토큰 없이 누구나 접속할 수 있도록 공개 접근(Public Access) 허용.
  * `--region=asia-northeast3`: 서울 리전에 배포하여 빠른 응답 속도 보장.
  * `--platform=managed`: Google 완전 관리형 서버리스 인프라 사용.

---

### 4단계: 배포 결과 및 고유 URL 확인

배포가 성공적으로 완료되면 콘솔 출력에 고유 Service URL이 표시됩니다:

```text
Service [todo-backend] revision [todo-backend-00001-abc] has been deployed and is serving 100 percent of traffic.
Service URL: https://todo-backend-xxxxx-du.a.run.app
```

서비스 URL 확인 명령어:
```powershell
gcloud run services describe todo-backend `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708 `
    --format="value(status.url)"
```

---

### 5단계: 웹 브라우저 접속 및 동작 검증

1. **메인 웹 애플리케이션 접속**:
   - `https://todo-backend-xxxxx-du.a.run.app/`
2. **API 엔드포인트 동작 확인**:
   - `https://todo-backend-xxxxx-du.a.run.app/api/items`
   - `https://todo-backend-xxxxx-du.a.run.app/api/greeting`
3. **CLI 헬스체크**:
   ```powershell
   curl -I https://<SERVICE_URL>/
   ```

---

## 5. Cloud Run 데이터베이스 연동 전략 (3가지 방식)

현재 프로젝트의 [`backend/src/persistence/index.js`](file:///d:/Lecture%20Notes/2026-2CloudComputing/practices/06week/getting-started-todo-app/backend/src/persistence/index.js) 코드는 환경변수 유무에 따라 데이터베이스 드라이버를 동적으로 선택하도록 구현되어 있습니다:

```javascript
if (process.env.MYSQL_HOST) module.exports = require('./mysql');
else module.exports = require('./sqlite');
```

따라서 목적에 따라 다음과 같이 3가지 연동 방식을 선택할 수 있습니다.

### 방법 1: [초간단 테스트] 자체 내장 SQLite로 단독 구동 (추천)
* `MYSQL_HOST` 환경변수를 전달하지 않고 배포하면 별도의 MySQL 서버 없이 컨테이너 내부의 SQLite 모드로 자동 전환되어 즉시 동작합니다.
* 외부 DB 설치 비용 없이 Cloud Run 기능 자체를 빠르게 검증할 때 가장 유용합니다.

### 방법 2: [실습/비용 절감] 기존 GCP VM의 MySQL 컨테이너 연동
* 앞서 배포한 GCP Compute Engine VM(`34.22.79.49`)의 MySQL 컨테이너를 재활용합니다.
* VM 방화벽에서 3306 포트를 허용하고, Cloud Run 환경변수로 VM의 IP를 주입합니다:
  ```powershell
  --set-env-vars="MYSQL_HOST=34.22.79.49,MYSQL_USER=root,MYSQL_PASSWORD=secret,MYSQL_DB=todos"
  ```

### 방법 3: [프로덕션 표준] GCP Cloud SQL (완전 관리형 MySQL) 사용
* Google Cloud의 완전 관리형 RDBMS 서비스인 Cloud SQL 인스턴스를 생성하고 연동합니다.
* Cloud Run의 내장 보안 소켓 연결 옵션(`--add-cloudsql-instances`)을 사용하여 VPC 외부 노출 없이 안전하게 연결합니다:
  ```powershell
  --add-cloudsql-instances="ssu-agent-vertex-509708:asia-northeast3:todo-mysql" `
  --set-env-vars="MYSQL_HOST=/cloudsql/ssu-agent-vertex-509708:asia-northeast3:todo-mysql,MYSQL_USER=root,MYSQL_PASSWORD=secret,MYSQL_DB=todos"
  ```

---

## 6. Cloud Run에서 `todo-backend`와 `mysql` 동시 실행 가능 여부 심층 분석

### 6.1 기술적 구현 가능성 (Cloud Run 멀티 컨테이너 / 사이드카 패턴)
Cloud Run은 쿠버네티스의 파드(Pod) 개념과 유사하게 **단일 서비스 인스턴스 안에 여러 컨테이너(메인 컨테이너 + 사이드카 컨테이너)**를 함께 실행하는 **멀티 컨테이너(Multi-Container)** 기능을 지원합니다.

두 컨테이너는 동일 인스턴스 내부에서 **`localhost` 네트워크를 공유**하므로, 이론적으로 `todo-backend`가 `localhost:3306`을 통해 같은 인스턴스의 `mysql` 컨테이너와 통신하도록 구성할 수 있습니다.

#### 멀티 컨테이너 서비스 매니페스트 예시 (`cloudrun-service.yaml`)
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: todo-fullstack
  annotations:
    run.googleapis.com/launch-stage: BETA
spec:
  template:
    spec:
      containers:
        # [컨테이너 1: 메인 웹/백엔드 (외부 Ingress 트래픽 수신)]
        - name: todo-backend
          image: asia-northeast3-docker.pkg.dev/ssu-agent-vertex-509708/my-repo/todo-backend:prod
          ports:
            - containerPort: 3000
          env:
            - name: MYSQL_HOST
              value: "localhost" # 같은 인스턴스의 사이드카 MySQL과 통신
            - name: MYSQL_USER
              value: "root"
            - name: MYSQL_PASSWORD
              value: "secret"
            - name: MYSQL_DB
              value: "todos"

        # [컨테이너 2: 사이드카 MySQL (내부 통신 전용)]
        - name: mysql
          image: mysql:9.3
          env:
            - name: MYSQL_ROOT_PASSWORD
              value: "secret"
            - name: MYSQL_DATABASE
              value: "todos"
```

배포 명령어:
```powershell
gcloud run services replace cloudrun-service.yaml --region=asia-northeast3
```

---

### 6.2 실무에서 이 구성을 권장하지 않는 3가지 치명적인 한계

기술적으로 위 매니페스트를 배포할 수는 있으나, 데이터베이스(RDBMS)를 Cloud Run 내부에 함께 띄우는 것은 **다음과 같은 심각한 문제**를 야기합니다:

#### ① 데이터 증발 (Scale-to-Zero로 인한 영구 데이터 유실)
* Cloud Run은 트래픽이 없으면 비용 절감을 위해 인스턴스를 **0개로 축소(Scale-to-Zero)**합니다.
* 컨테이너 내부 파일시스템은 임시(Ephemeral/In-memory) 스토리지이므로, **인스턴스가 종료되는 순간 MySQL의 모든 테이블과 데이터가 완전히 삭제(초기화)**됩니다.

#### ② 데이터 파편화 (스케일 아웃 다중 인스턴스 간 데이터 불일치)
* 트래픽이 증가하여 Cloud Run 인스턴스가 2개 이상으로 자동 확장(Scale-out)되면, **각 인스턴스마다 별도의 독립된 MySQL 프로세스가 따로 실행**됩니다.
* 인스턴스 A에 저장한 할 일 목록이 인스턴스 B에서는 전혀 보이지 않는 치명적인 데이터 불일치(파편화)가 발생합니다.

#### ③ 콜드 스타트(Cold Start) 지연 및 요청 타임아웃
* 요청이 들어올 때 인스턴스가 기동되는데, 무거운 MySQL 데몬이 부팅되고 데이터 디렉터리를 초기화하는 데 수 초~수십 초가 소요됩니다.
* 그 결과 사용자의 첫 웹 요청이 백엔드에 도달하기 전에 HTTP 504 게이트웨이 타임아웃 오류가 발생할 가능성이 높습니다.

---

### 6.3 아키텍처 선택 가이드 요약

| 요구 사항 | 권장 인프라 아키텍처 | 설명 |
| :--- | :--- | :--- |
| **추가 비용 없이 Cloud Run 하나로 끝내고 싶을 때** | **Cloud Run 단독 (`todo-backend` + 내장 SQLite)** | `MYSQL_HOST` 미지정 시 자체 SQLite로 구동. 가장 가볍고 빠름 (실습용) |
| **데이터를 영구 보존하며 서버리스 장점을 극대화할 때** | **Cloud Run (`todo-backend`) + GCP Cloud SQL (`MySQL`)** | 애플리케이션은 무상태 서버리스로 확장하고, DB는 관리형 영구 스토리지에 분리하는 **클라우드 모범 규격(Best Practice)** |
| **MySQL 컨테이너 및 로컬/영구 볼륨(PVC)을 함께 묶어 쓸 때** | **GCP VM (Docker Compose)** 또는 **GKE (Kubernetes Pod + PVC)** | 상태 유지(Stateful)가 안정적으로 보장되는 환경 사용 |

---

## 7. Cloud Run 서비스 정지(일시 중지), 재개 및 삭제 워크플로우

Cloud Run은 상시 실행되는 일반 VM과 달리 **서버리스(Serverless)** 환경이므로 동작 및 정지 라이프사이클이 다릅니다.

### 7.1 Cloud Run의 비용 및 정지 특성
* **유휴 상태(Idle) 비용 0원**: 웹 브라우저나 외부에서 호출 요청이 없으면 인스턴스가 자동으로 **0개로 축소(Scale-to-Zero)**되므로, 일반 VM처럼 강제로 끄지 않아도 **유휴 상태에서는 비용이 청구되지 않습니다.**
* 따라서 단순 비용 절감이 목적이라면 별도로 정지하지 않아도 됩니다.

---

### 7.2 서비스 일시 정지 (트래픽 유입 및 실행 완전 차단)

외부 접속을 즉시 차단하거나 컨테이너가 절대 실행되지 않도록 막고 싶다면 다음 두 가지 방식을 사용합니다.

#### 방법 A: 최대 인스턴스를 0개로 설정 (가장 권장 - 즉시 중단)
인스턴스 확장 한도를 0으로 지정하여 어떤 요청이 들어와도 컨테이너가 기동되지 않도록 합니다 (접속자에게는 즉시 HTTP 503 에러 반환).

```powershell
# 서비스 일시 정지 (최대 인스턴스 0개로 제한)
gcloud run services update todo-backend `
    --max-instances=0 `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708
```

#### 방법 B: 외부 공개 접근(Public Access) 권한 회수
일반 사용자의 비인증 접근 권한(`allUsers`)을 박탈하여 인증된 관리자 외에는 접근할 수 없도록 차단합니다:

```powershell
# 외부 비인증 호출 차단 (인증 필요 모드로 전환)
gcloud run services remove-iam-policy-binding todo-backend `
    --member="allUsers" `
    --role="roles/run.invoker" `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708
```

---

### 7.3 서비스 재개 (정상 동작 복구)

정지해 둔 서비스를 다시 정상 서비스 상태로 복구할 때는 최대 인스턴스 설정을 원래대로 되돌립니다:

```powershell
# 서비스 정상 재개 (기본 최대 인스턴스 100개로 복구)
gcloud run services update todo-backend `
    --max-instances=100 `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708
```

---

### 7.4 서비스 완전 삭제 (자원 정리)

배포된 Cloud Run 서비스와 해당 서비스에 발급된 고유 URL(`*.a.run.app`)을 완전히 삭제할 때 사용합니다:

```powershell
# 대화형 확인 프롬프트와 함께 삭제
gcloud run services delete todo-backend `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708

# 확인 프롬프트 없이 즉시 삭제 (--quiet)
gcloud run services delete todo-backend `
    --region=asia-northeast3 `
    --project=ssu-agent-vertex-509708 `
    --quiet
```

---

### 7.5 서비스 관리 명령어 요약표

| 작업 | 실행 명령어 (`gcloud`) | 동작 설명 |
| :--- | :--- | :--- |
| **상태 확인** | `gcloud run services describe todo-backend --region=asia-northeast3 --project=ssu-agent-vertex-509708` | 서비스 URL, 트래픽 배분, 최신 리비전 확인 |
| **일시 정지** | `gcloud run services update todo-backend --max-instances=0 --region=asia-northeast3 --project=ssu-agent-vertex-509708` | 요청이 와도 컨테이너 실행 차단 (503 에러) |
| **서비스 재개**| `gcloud run services update todo-backend --max-instances=100 --region=asia-northeast3 --project=ssu-agent-vertex-509708` | 최대 인스턴스 한도 복구 및 정상 요청 처리 |
| **완전 삭제** | `gcloud run services delete todo-backend --region=asia-northeast3 --project=ssu-agent-vertex-509708 --quiet` | 서비스 및 모든 리비전 영구 제거 |

---

## 8. Cloud Run 배포 시 포트 바인딩 코드(`const PORT = process.env.PORT || 3000;`) 필수 이유 심층 분석

### 8.1 코드 비교 분석

```javascript
// [수정 전: Cloud Run 배포 실패 및 런타임 오류 코드]
db.init()
    .then(() => {        
        app.listen(3000, () => console.log('Listening on port 3000'));
    })
```

```javascript
// [수정 후: Cloud Run 및 로컬/VM 완벽 호환 표준 코드]
db.init()
    .then(() => {
        const PORT = process.env.PORT || 3000;
        app.listen(PORT, () => console.log(`Listening on port ${PORT}`));
    })
```

---

### 8.2 왜 `app.listen(3000)`으로 하드코딩하면 Cloud Run에서 배포가 실패하는가?

#### 1) Cloud Run 컨테이너 계약 (Container Contract) 위반
* **Cloud Run의 포트 정책**:
  - Cloud Run 플랫폼은 컨테이너를 실행할 때 **`PORT=8080` 환경변수를 자동으로 주입**합니다.
  - Cloud Run의 내부 로드밸런서 및 인그레스 프록시는 `PORT` 환경변수가 가리키는 포트(즉, **8080번 포트**)로 헬스체크(Liveness/Startup Probe)와 HTTP 트래픽을 전송하도록 설계되어 있습니다.
* **하드코딩 시 발생하는 현상**:
  - Express 서버는 3000번 포트만 열고 대기합니다.
  - 하지만 Cloud Run은 8080번 포트로 연결을 시도하므로 연결 거부(`Connection Refused`)가 발생합니다.
  - 결국 4분간 헬스체크 응답을 받지 못해 다음과 같은 오류 로그를 남기며 **배포가 즉시 취소되고 컨테이너가 강제 종료(Crash)**됩니다:
    ```text
    Cloud Run error: Container failed to start. Failed to listen on the port defined by the PORT environment variable. (PORT: 8080)
    ```


---

### 8.3 `process.env.PORT` 란 무엇인가? (개념 및 동작 메커니즘)

#### 1) Node.js의 `process.env` 객체
* **`process`**: Node.js 런타임에 기본 내장되어 있는 전역 객체(Global Object)로, 현재 실행 중인 프로세스의 제어 정보와 시스템 환경 정보를 담고 있습니다.
* **`process.env`**: 운영체제(OS)나 컨테이너 런타임으로부터 프로세스에 전달된 **모든 환경 변수(Environment Variables)**를 키-값(Key-Value) 쌍으로 보관하는 객체입니다.
  ```javascript
  // 예시: process.env 객체의 내부 형태
  {
    NODE_ENV: 'production',
    PORT: '8080',            // Cloud Run이 컨테이너 실행 시 주입한 값
    PATH: '/usr/local/bin:...',
    ...
  }
  ```
* 따라서 **`process.env.PORT`**는 *"시스템 또는 외부 플랫폼이 이 컨테이너에게 할당해 준 `PORT`라는 이름의 환경변수 값"*을 조회하는 코드입니다.

---

#### 2) `PORT` 환경변수의 출처와 전달 과정

```text
[GCP Cloud Run 인프라]
         │
         │ 컨테이너 실행 시 내부적으로 환경변수 주입
         │ (docker run -e PORT=8080 ...)
         ▼
[Node.js 애플리케이션 컨테이너]
         │
         ▼
process.env.PORT 조회 ───► 결과: "8080"
```

* **Cloud Run 환경**:
  - Cloud Run 플랫폼은 서버리스 컨테이너를 구동할 때 내부적으로 `-e PORT=8080` (또는 설정된 포트 번호)을 컨테이너에 전달합니다.
  - 이로 인해 Node.js 코드 내에서 `process.env.PORT`를 읽으면 문자열 **`"8080"`**이 반환됩니다.
* **로컬 / Docker Compose / VM 환경**:
  - `docker-compose.yml` 등에서 `PORT` 환경변수를 별도로 선언하지 않으면 운영체제에 해당 변수가 존재하지 않습니다.
  - 이 경우 `process.env.PORT`는 자바스크립트 기본값인 **`undefined`**가 됩니다.

---

### 8.4 왜 `const PORT = process.env.PORT || 3000;` 가 가장 완벽한 해법인가?

자바스크립트의 **단락 평가(Short-circuit Evaluation) 연산자 `||` (OR)**의 동작 특성을 활용한 클라우드 네이티브 패턴입니다:

$$\text{const PORT} = \underbrace{\text{process.env.PORT}}_{\text{우선순위 1}} \;||\; \underbrace{3000}_{\text{폴백(Fallback) 기본값}};$$

1. **Cloud Run 환경에서 실행 시 (값 존재)**:
   - `process.env.PORT`가 `"8080"`(Truthy 값)이므로, 연산자가 첫 번째 값에서 즉시 평가를 종료합니다.
   - `PORT = "8080"`이 되어 Express 서버가 **8080번 포트**로 리슨을 시작하고, Cloud Run의 헬스체크 및 트래픽 라우팅이 즉시 성공합니다.

2. **로컬 Docker / Compose / VM 환경에서 실행 시 (값 없음)**:
   - `process.env.PORT`가 `undefined`(Falsy 값)이므로, `||` 뒤에 있는 기본값 **`3000`**이 선택됩니다.
   - `PORT = 3000`이 되어 기존 로컬 Traefik(3000번 포트 포워딩) 및 개발 환경에서 아무런 수정 없이 그대로 작동합니다.

---

### 8.5 실행 환경별 `PORT` 변수 평가 요약표

| 실행 환경 | `process.env.PORT` 값 | 최종 바인딩 포트 (`PORT`) | 비고 |
| :--- | :--- | :--- | :--- |
| **GCP Cloud Run** | `"8080"` (GCP 자동 주입) | **`8080`** | Cloud Run 인그레스 프록시 계약 준수 $\rightarrow$ 배포 성공 |
| **GCP Compute Engine (VM)** | `undefined` (주입 안 됨) | **`3000`** (기본값) | Traefik 프록시(`port: 3000`)와 일치 $\rightarrow$ 정상 동작 |
| **로컬 Docker Compose** | `undefined` (미지정 시) | **`3000`** (기본값) | 로컬 `http://localhost:3000` 연동 |
| **사용자 임의 지정 환경** | `"5000"` (`-e PORT=5000`) | **`5000`** | 지정한 포트로 유연하게 동적 변경 가능 |

> [!TIP]
> **12-Factor App 원칙 (Config & Port Binding)**  
> 클라우드 네이티브 애플리케이션 설계 방법론인 **12-Factor App**에 따르면, "애플리케이션은 실행 환경에 포트를 하드코딩하지 않고, 실행 환경이 주입하는 포트 바인딩(환경변수)을 통해 서비스를 공개해야 한다"고 규정하고 있습니다.  
> `const PORT = process.env.PORT || 3000;`는 이 원칙을 충실히 반영한 표준적인 구현입니다.




