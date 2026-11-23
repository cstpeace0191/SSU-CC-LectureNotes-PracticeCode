# [Step 1] 환경 및 구조 진단 보고서

## 1. 코드베이스 탐색 개요
- **프로젝트 명칭:** Online Boutique (Google Cloud Platform Microservices Demo)
- **저장소 성격:** 클라우드 네이티브 마이크로서비스 e-커머스 참조 아키텍처 ([README.md:6-10](.../microservices-demo/README.md#L6-L10))
- **전체 구성:** 총 11개의 핵심 마이크로서비스 및 1개의 AI 쇼핑 어시스턴트 서비스, 1개의 부하 생성기(Load Generator)로 구성되어 있으며 서비스 간 내부 통신은 gRPC(HTTP/2) 프로토콜을 사용함 ([README.md:17-18](.../microservices-demo/README.md#L17-L18), [protos/demo.proto:1-263](.../microservices-demo/protos/demo.proto#L1-L263)).
- **개발 및 배포 환경:**
  - Kubernetes (GKE, Minikube, Kind 등 호환)
  - Skaffold 기반 로컬/원격 지속적 개발 루프 ([skaffold.yaml:1-120](.../microservices-demo/skaffold.yaml#L1-L120))
  - Helm 차트 및 Kustomize 지원 ([helm-chart/](.../microservices-demo/helm-chart), [kustomize/](.../microservices-demo/kustomize))
  - Terraform 인프라 프로비저닝 스크립트 ([terraform/](.../microservices-demo/terraform))

---

## 2. 서비스별 언어 및 런타임 버전

| 마이크로서비스 | 주 언어 | 런타임 / 타겟 버전 | 베이스 컨테이너 이미지 | 코드 위치 확인 |
| :--- | :--- | :--- | :--- | :--- |
| **frontend** | Go | Go 1.25 (Toolchain 1.27.1) | `golang:1.27.0-alpine` | [src/frontend/go.mod:3-5](.../microservices-demo/src/frontend/go.mod#L3-L5), [src/frontend/Dockerfile:18](.../microservices-demo/src/frontend/Dockerfile#L18) |
| **cartservice** | C# | .NET 10.0 (`net10.0`) | `mcr.microsoft.com/dotnet/sdk:10.0.100-noble` | [src/cartservice/src/cartservice.csproj:4](.../microservices-demo/src/cartservice/src/cartservice.csproj#L4), [src/cartservice/src/Dockerfile:19](.../microservices-demo/src/cartservice/src/Dockerfile#L19) |
| **productcatalogservice** | Go | Go 1.25 (Toolchain 1.27.1) | `golang:1.27.0-alpine` | [src/productcatalogservice/go.mod:3-5](.../microservices-demo/src/productcatalogservice/go.mod#L3-L5), [src/productcatalogservice/Dockerfile:18](.../microservices-demo/src/productcatalogservice/Dockerfile#L18) |
| **currencyservice** | JavaScript | Node.js 24.x | `node:24.20.0-alpine` | [src/currencyservice/package.json:1-28](.../microservices-demo/src/currencyservice/package.json#L1-L28), [src/currencyservice/Dockerfile:18](.../microservices-demo/src/currencyservice/Dockerfile#L18) |
| **paymentservice** | JavaScript | Node.js 24.x | `node:24.20.0-alpine` | [src/paymentservice/package.json:1-28](.../microservices-demo/src/paymentservice/package.json#L1-L28), [src/paymentservice/Dockerfile:18](.../microservices-demo/src/paymentservice/Dockerfile#L18) |
| **shippingservice** | Go | Go 1.25 (Toolchain 1.27.1) | `golang:1.27.0-alpine` | [src/shippingservice/go.mod:3-5](.../microservices-demo/src/shippingservice/go.mod#L3-L5), [src/shippingservice/Dockerfile:18](.../microservices-demo/src/shippingservice/Dockerfile#L18) |
| **emailservice** | Python | Python 3.14.x | `python:3.14.7-alpine` | [src/emailservice/requirements.in:1-12](.../microservices-demo/src/emailservice/requirements.in#L1-L12), [src/emailservice/Dockerfile:18](.../microservices-demo/src/emailservice/Dockerfile#L18) |
| **checkoutservice** | Go | Go 1.25 (Toolchain 1.27.1) | `golang:1.27.0-alpine` | [src/checkoutservice/go.mod:3-5](.../microservices-demo/src/checkoutservice/go.mod#L3-L5), [src/checkoutservice/Dockerfile:18](.../microservices-demo/src/checkoutservice/Dockerfile#L18) |
| **recommendationservice** | Python | Python 3.14.x | `python:3.14.7-alpine` | [src/recommendationservice/requirements.in:1-12](.../microservices-demo/src/recommendationservice/requirements.in#L1-L12), [src/recommendationservice/Dockerfile:18](.../microservices-demo/src/recommendationservice/Dockerfile#L18) |
| **adservice** | Java | Java 21 (JDK 25 빌더) | `eclipse-temurin:25.0.4_7-jdk-noble` | [src/adservice/build.gradle:22-25](.../microservices-demo/src/adservice/build.gradle#L22-L25), [src/adservice/Dockerfile:18](.../microservices-demo/src/adservice/Dockerfile#L18) |
| **loadgenerator** | Python | Python 3.14.x | `python:3.14.7-alpine` | [src/loadgenerator/requirements.in:1](.../microservices-demo/src/loadgenerator/requirements.in#L1), [src/loadgenerator/Dockerfile:18](.../microservices-demo/src/loadgenerator/Dockerfile#L18) |
| **shoppingassistantservice** | Python | Python 3.14.x | `python:3.14.7-alpine` | [src/shoppingassistantservice/requirements.in:1-5](.../microservices-demo/src/shoppingassistantservice/requirements.in#L1-L5), [src/shoppingassistantservice/Dockerfile:18](.../microservices-demo/src/shoppingassistantservice/Dockerfile#L18) |

---

## 3. 빌드 및 패키지 매니저
- **Go 모듈 (`go.mod`, `go.sum`):** `frontend`, `checkoutservice`, `productcatalogservice`, `shippingservice`에서 표준 Go 의존성 관리 사용.
- **.NET CLI / NuGet (`cartservice.csproj`, `cartservice.sln`):** `cartservice`에서 NuGet 패키지 의존성 복원 및 dotnet SDK 빌드 사용.
- **npm (`package.json`, `package-lock.json`):** `paymentservice`, `currencyservice`에서 Node.js npm 생태계 사용.
- **pip / pip-tools (`requirements.in`, `requirements.txt`):** `emailservice`, `recommendationservice`, `loadgenerator`, `shoppingassistantservice`에서 핀 고정된 종속성 관리 사용.
- **Gradle Wrapper (`build.gradle`, `gradlew`):** `adservice`에서 Gradle 8.x 빌드 툴체인 사용.

---

## 4. 핵심 기술 스택

### 4.1 웹/API 프레임워크
- **외부 공개 웹 게이트웨이 (Frontend):**
  - Go 표준 라이브러리 `net/http` 및 HTTP 라우터 `github.com/gorilla/mux` v1.8.1 ([src/frontend/main.go:88-123](.../microservices-demo/src/frontend/main.go#L88-L123))
  - HTML 템플릿 렌더링 (`html/template`)
- **내부 서비스 간 통신 RPC (gRPC):**
  - 모든 백엔드 마이크로서비스 간 통신은 gRPC v1.x 및 Protobuf v3를 사용 ([protos/demo.proto:1-263](.../microservices-demo/protos/demo.proto#L1-L263))
  - Go: `google.golang.org/grpc`
  - C#: `Grpc.AspNetCore`
  - Node.js: `@grpc/grpc-js`, `@grpc/proto-loader`
  - Python: `grpcio`, `grpcio-tools`, `grpcio-health-checking`
  - Java: `io.grpc:grpc-netty`, `io.grpc:grpc-protobuf`

### 4.2 데이터 저장소 및 캐시
- **장바구니 저장소 (Cart Store):**
  - **기본값 (Default):** Redis (`redis:6379`) 캐시/키-값 저장소 ([src/cartservice/src/cartstore/RedisCartStore.cs:1-125](.../microservices-demo/src/cartservice/src/cartstore/RedisCartStore.cs#L1-L125))
  - **In-Memory 폴백:** `LocalCartStore.cs` ([src/cartservice/src/cartstore/LocalCartStore.cs:1-60](.../microservices-demo/src/cartservice/src/cartstore/LocalCartStore.cs#L1-L60))
  - **엔터프라이즈 옵션:** Google Cloud Spanner (`SpannerCartStore.cs`), AlloyDB / PostgreSQL (`PostgresCartStore.cs`) ([src/cartservice/src/cartstore/](.../microservices-demo/src/cartservice/src/cartstore))
- **상품 카탈로그 저장소:**
  - **기본값:** 로컬 정적 JSON 파일 로더 ([src/productcatalogservice/products.json:1-150](.../microservices-demo/src/productcatalogservice/products.json#L1-L150), [src/productcatalogservice/catalog_loader.go:1-135](.../microservices-demo/src/productcatalogservice/catalog_loader.go#L1-L135))
  - **클라우드 스토리지 옵션:** Google Cloud Storage 버킷 및 Spanner 연동 가능.
- **통화 환율 데이터:**
  - 유럽중앙은행(ECB) 환율 데이터 파일 기반 인메모리 파싱 ([src/currencyservice/data/currency_conversion.json:1-35](.../microservices-demo/src/currencyservice/data/currency_conversion.json#L1-L35))

### 4.3 메시지 브로커 / 큐
- 본 시스템은 비동기 메시지 브로커(Kafka, RabbitMQ 등)를 사용하지 않고, **동기식 gRPC RPC 호출 체인 (Request-Response 패턴)**을 통해 주문 생성, 결제, 배송 등의 분산 트랜잭션을 처리함.
- Checkout 오케스트레이터([src/checkoutservice/main.go:88-160](.../microservices-demo/src/checkoutservice/main.go#L88-L160))가 동기 RPC 파이프라인으로 각 서비스를 제어함.

### 4.4 관측성(Observability) 및 모니터링
- **분산 트레이싱 & 메트릭:** OpenTelemetry (OTel SDK 및 OTLP gRPC 익스포터) 표준 적용 ([src/frontend/main.go:48-60](.../microservices-demo/src/frontend/main.go#L48-L60), [src/checkoutservice/main.go:40-60](.../microservices-demo/src/checkoutservice/main.go#L40-L60))
- **프로파일링:** Google Cloud Profiler (`cloud.google.com/go/profiler`, `@google-cloud/profiler`) 연동

---

## 5. 주요 디렉토리 매핑 및 역할 분석

| 디렉토리 경로 | 역할 및 비즈니스 책임 |
| :--- | :--- |
| [`/protos`](.../microservices-demo/protos) | 모든 마이크로서비스 간 통신 규약 인터페이스 정의 (`demo.proto`, HealthCheck proto) |
| [`/src/frontend`](.../microservices-demo/src/frontend) | 사용자 인터페이스(HTML/CSS/JS) 제공, 쿠키 기반 세션 관리, 백엔드 gRPC 집합 게이트웨이 |
| [`/src/cartservice`](.../microservices-demo/src/cartservice) | 장바구니 품목 추가/조회/비우기 gRPC API 및 Redis/Spanner/Postgres 스토어 연동 |
| [`/src/productcatalogservice`](.../microservices-demo/src/productcatalogservice) | 상품 목록, 상세 정보, 키워드 검색 gRPC API 제공 |
| [`/src/currencyservice`](.../microservices-demo/src/currencyservice) | 국가별 통화 지원 목록 반환 및 금액 변환(Currency Convert) gRPC API (최고 QPS) |
| [`/src/paymentservice`](.../microservices-demo/src/paymentservice) | 신용카드 정보 검증 및 모의 결제 승인(Transaction ID 생성) |
| [`/src/shippingservice`](.../microservices-demo/src/shippingservice) | 배송비 견적 산출 및 주문 배송 트래킹 번호 생성 |
| [`/src/emailservice`](.../microservices-demo/src/emailservice) | 결제 완료 후 주문 명세 이메일 발송 처리 (모의 구현) |
| [`/src/checkoutservice`](.../microservices-demo/src/checkoutservice) | 전체 주문 결제 플로우(장바구니 확인 -> 배송비 -> 결제 -> 배송 -> 이메일 -> 장바구니 비우기) 오케스트레이션 |
| [`/src/recommendationservice`](.../microservices-demo/src/recommendationservice) | 장바구니 항목 기반 맞춤형 연관 상품 추천 |
| [`/src/adservice`](.../microservices-demo/src/adservice) | 요청 컨텍스트 키워드에 부합하는 타겟 광고 텍스트 제공 |
| [`/src/loadgenerator`](.../microservices-demo/src/loadgenerator) | Locust 기반 자동 부하 발생기 (E2E 유저 플로우 시뮬레이션) |
| [`/src/shoppingassistantservice`](.../microservices-demo/src/shoppingassistantservice) | Gemini AI API를 활용한 대화형 쇼핑 어시스턴트 서비스 |
| [`/kubernetes-manifests`](.../microservices-demo/kubernetes-manifests) | 개별 마이크로서비스 배포를 위한 쿠버네티스 Deployment/Service YAML 매니페스트 |
| [`/release`](.../microservices-demo/release) | 단일 릴리즈 통합 쿠버네티스 매니페스트 (`kubernetes-manifests.yaml`) |
| [`/helm-chart`](.../microservices-demo/helm-chart) | 헬름 기반 패키징 및 설정 관리 차트 |

---

## 6. 빌드 및 테스트 구동 명령어

### 6.1 서비스별 로컬 빌드 및 단위 테스트
- **Go 서비스 (`frontend`, `checkoutservice`, `productcatalogservice`, `shippingservice`):**
  ```bash
  # 예: shippingservice
  cd src/shippingservice
  go build -o server .
  go test -v ./...
  ```
- **C# .NET 서비스 (`cartservice`):**
  ```bash
  cd src/cartservice/src
  dotnet build cartservice.csproj
  dotnet test ../tests/cartservice.tests.csproj
  ```
- **Node.js 서비스 (`currencyservice`, `paymentservice`):**
  ```bash
  cd src/paymentservice
  npm install
  # 단위 테스트 실행 (테스트 스크립트 등록 시)
  npm test
  ```
- **Java 서비스 (`adservice`):**
  ```bash
  cd src/adservice
  ./gradlew build
  ./gradlew test
  ```
- **Python 서비스 (`emailservice`, `recommendationservice`):**
  ```bash
  cd src/emailservice
  pip install -r requirements.txt
  python email_server.py
  ```

### 6.2 통합 개발 및 클러스터 배포 구동
- **Skaffold 라이브 개발 모드 (로컬/원격 쿠버네티스 클러스터 연결 시):**
  ```bash
  # 코드 변경 시 컨테이너 빌드 및 클러스터 핫 리로드 자동 동기화
  skaffold dev
  ```
- **쿠버네티스 매니페스트 직접 배포:**
  ```bash
  kubectl apply -f ./release/kubernetes-manifests.yaml
  ```
- **Helm 차트 배포:**
  ```bash
  helm install online-boutique ./helm-chart
  ```

