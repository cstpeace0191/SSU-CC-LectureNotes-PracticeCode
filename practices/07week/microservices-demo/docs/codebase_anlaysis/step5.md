# [Step 5] 빌드, 실행 및 배포 파이프라인 보고서

## 1. 컴파일 및 번들링 (Build Pipeline)

### 1.1 빌드 도구 및 멀티 아키텍처 전략
- **빌드 도구:**
  - **Docker & Docker Buildx:** 각 서비스 폴더의 `Dockerfile`에 정의된 멀티 스테이지 빌드(Multi-stage build)를 활용하여 빌드 타임 의존성과 런타임 이미지를 엄격히 분리함.
  - **Skaffold v3:** 마이크로서비스 전체 이미지 빌드 오케스트레이션 도구 ([skaffold.yaml:15-54](.../microservices-demo/skaffold.yaml#L15-L54)).
  - **빌드 플랫폼:** `linux/amd64` 및 `linux/arm64` (Apple Silicon 및 AWS Graviton 호환 멀티 플랫폼 빌드 지원).
- **서비스별 빌드 도구 매핑:**
  - `frontend`, `checkoutservice`, `productcatalogservice`, `shippingservice`: Go Compiler (`golang:1.27.0-alpine`)
  - `cartservice`: .NET SDK (`mcr.microsoft.com/dotnet/sdk:10.0.100-noble`)
  - `paymentservice`, `currencyservice`: Node.js npm (`node:24.20.0-alpine`)
  - `adservice`: Gradle 8.x Wrapper (`eclipse-temurin:25.0.4_7-jdk-noble`)
  - `emailservice`, `recommendationservice`, `shoppingassistantservice`: Python pip (`python:3.14.7-alpine`)
- **최종 빌드 산출물 (Artifact):**
  - 서비스별 경량화된 컨테이너 이미지 (예: `us-docker.pkg.dev/online-boutique-ci/...` 또는 `gcr.io/google-samples/microservices-demo/[service]:[tag]`)

---

## 2. 로컬 실행 및 에뮬레이션 (Run & Emulation)

### 2.1 사전 필수 환경 및 서비스
- **필수 환경:**
  - Docker 엔진 및 Kubernetes 클러스터 (Minikube, Kind, Docker Desktop K8s, 또는 원격 GKE)
  - `kubectl` CLI 및 `skaffold` CLI
- **필수 백엔드 의존 서비스:**
  - `redis-cart` (포트 `6379`): 장바구니 세션 유지를 위한 인메모리 스토리지 필수 구동 ([kubernetes-manifests/redis.yaml](.../microservices-demo/kubernetes-manifests/redis.yaml))

### 2.2 로컬 구동 커맨드
1. **Skaffold 라이브 개발 모드 (권장):**
   ```bash
   # 소스 코드 변경 시 실시간 증분 빌드 및 클러스터 자동 반영
   skaffold dev
   ```
2. **사전 빌드된 릴리즈 매니페스트로 일괄 구동:**
   ```bash
   kubectl apply -f ./release/kubernetes-manifests.yaml
   
   # 모든 Pod가 Running 상태가 될 때까지 확인
   kubectl get pods -w
   ```
3. **로컬 웹 브라우저 접속 (포트포워딩):**
   ```bash
   kubectl port-forward svc/frontend-external 8080:80
   # 브라우저에서 http://localhost:8080 접속
   ```

### 2.3 핵심 환경 변수 설정
마이크로서비스 간 서비스 디스커버리는 쿠버네티스 표준 DNS와 환경 변수 주입을 통해 이루어집니다 ([kubernetes-manifests/frontend.yaml:70-105](.../microservices-demo/kubernetes-manifests/frontend.yaml#L70-L105)).

| 환경 변수명 | 주입 대상 서비스 | 설명 및 설정 예시 |
| :--- | :--- | :--- |
| `PORT` | 공통 전 서비스 | 서비스가 수신 대기할 포트 번호 (예: `8080`, `50051`) |
| `REDIS_ADDR` | `cartservice` | Redis 접속 주소 (기본값: `redis-cart:6379`) |
| `PRODUCT_CATALOG_SERVICE_ADDR` | `frontend`, `checkoutservice`, `recommendationservice` | 상품 카탈로그 서비스 gRPC 엔드포인트 (`productcatalogservice:3550`) |
| `CURRENCY_SERVICE_ADDR` | `frontend`, `checkoutservice` | 통화 변환 서비스 gRPC 엔드포인트 (`currencyservice:7000`) |
| `CART_SERVICE_ADDR` | `frontend`, `checkoutservice` | 장바구니 서비스 gRPC 엔드포인트 (`cartservice:7070`) |
| `SHIPPING_SERVICE_ADDR` | `frontend`, `checkoutservice` | 배송 서비스 gRPC 엔드포인트 (`shippingservice:50051`) |
| `PAYMENT_SERVICE_ADDR` | `checkoutservice` | 결제 승인 서비스 gRPC 엔드포인트 (`paymentservice:50051`) |
| `EMAIL_SERVICE_ADDR` | `checkoutservice` | 이메일 발송 서비스 gRPC 엔드포인트 (`emailservice:50051`) |
| `ENABLE_TRACING` | 공통 전 서비스 | OpenTelemetry 분산 트레이싱 활성화 플래그 (`"1"` 또는 `"0"`) |

---

## 3. 배포 및 인프라 파이프라인 (Deploy Pipeline)

### 3.1 CI/CD 워크플로우 (.github/workflows)
- **CI 트리거 (메인 브랜치):**
  - `.github/workflows/ci-main.yaml`: `main` 브랜치 푸시 또는 `release/*` 브랜치 변경 시 자동 트리거 ([.github/workflows/ci-main.yaml:17-31](.../microservices-demo/.github/workflows/ci-main.yaml#L17-L31)).
  - 단위 테스트(`code-tests`): Go 및 C# 단위 테스트 선행 실행.
  - 통합 배포 테스트(`deployment-tests`): Google Cloud Workload Identity 연동 -> GKE 테스트 클러스터에 임시 네임스페이스 생성 -> `skaffold run`으로 컨테이너 빌드 및 배포 -> 모든 파드 Available 대기 -> `Smoke Test` 수행 ([.github/workflows/ci-main.yaml:70-140](.../microservices-demo/.github/workflows/ci-main.yaml#L70-L140)).
- **PR 트리거 검증:**
  - `.github/workflows/ci-pr.yaml`, `.github/workflows/deploy-pr.yaml`: PR 생성 시 격리된 네임스페이스(`pr-${PR_NUMBER}`)에 동적 배포 후 E2E 유효성 검증.
- **릴리즈 파이프라인:**
  - `.github/workflows/make-release.yaml`: 태그 생성 시 단일 결합 매니페스트(`release/kubernetes-manifests.yaml`) 자동 생성 및 공식 이미지 퍼블리싱.

### 3.2 배포 대상(Target) 및 레지스트리
- **컨테이너 이미지 레지스트리:** Google Artifact Registry (`us-docker.pkg.dev/...`) 및 GitHub Container Registry(GHCR), Docker Hub.
- **배포 인프라 타겟:**
  - Google Kubernetes Engine (GKE Autopilot / Standard)
  - Istio / Cloud Service Mesh 연동 인프라 ([istio-manifests/](.../microservices-demo/istio-manifests))
  - Terraform 기반 GCP 인프라 자동 프로비저닝 ([terraform/](.../microservices-demo/terraform))

### 3.3 무중단 배포(Zero-Downtime Deployment) 및 헬스 체크 전략
1. **롤링 업데이트 전략 (RollingUpdate Strategy):**
   - 쿠버네티스 Deployment 표준 기본값(`maxSurge: 25%`, `maxUnavailable: 25%`)에 따라 점진적으로 신규 파드를 구동하고 구버전 파드를 회수.
2. **Health Check Probes:**
   - **Readiness Probe:** 트래픽 유입 전 파드의 정상 초기화 여부 검증.
     - `frontend`: HTTP `GET /_healthz` (쿠키 헤더 주입) ([kubernetes-manifests/frontend.yaml:50-57](.../microservices-demo/kubernetes-manifests/frontend.yaml#L50-L57)).
     - 백엔드 서비스들: gRPC Health Checking Protocol (`grpc.health.v1.Health/Check`) 기반 프로브 수행.
   - **Liveness Probe:** 서비스 교착 상태(Deadlock) 감지 시 파드 자동 재시작.
3. **컨테이너 보안 격리 (Security Hardening):**
   - 모든 서비스의 쿠버네티스 매니페스트에 비루트 유저 실행(`runAsNonRoot: true`, `runAsUser: 1000`), 모든 리눅스 기능 제거(`capabilities.drop: ["ALL"]`), 읽기 전용 루트 파일시스템(`readOnlyRootFilesystem: true`)을 강제 적용하여 프로덕션급 보안성 확보 ([kubernetes-manifests/frontend.yaml:40-47](.../microservices-demo/kubernetes-manifests/frontend.yaml#L40-L47)).

