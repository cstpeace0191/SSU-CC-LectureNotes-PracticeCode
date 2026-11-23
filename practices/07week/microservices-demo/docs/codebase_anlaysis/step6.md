# [Step 6] 변경 영향도 평가 및 개발 가이드

## 1. 주의해야 할 고위험 모듈 (High-Risk Areas)

| 고위험 모듈 및 파일 위치 | 위험 요인 및 파급 영향도 | 권장 완화 대책 |
| :--- | :--- | :--- |
| **`protos/demo.proto`**<br/>([protos/demo.proto:1-263](.../microservices-demo/protos/demo.proto#L1-L263)) | **전체 시스템 공통 통신 계약(Contract):** 필드 번호 변경, 타입 변경, 메시지 삭제 등 하위 호환성을 깨뜨리는(Breaking) 수정 시 11개 마이크로서비스 전체의 컴파일 및 런타임 직렬화 장애 유발. | Protobuf 예약어(`reserved`) 활용, 필드 삭제 지양, 신규 필드는 옵셔널(optional) 추가 원칙 준수, 필드 번호 재사용 금지. |
| **`src/checkoutservice/main.go`**<br/>([src/checkoutservice/main.go:230-280](.../microservices-demo/src/checkoutservice/main.go#L230-L280)) | **중앙 분산 트랜잭션 오케스트레이터:** 결제, 장바구니, 배송, 이메일이 연계되어 있어 한 단계의 로직 수정 오류가 전체 주문 실패 또는 결제 후 배송 누락 등의 비즈니스 불일치 초래. | 분산 트랜잭션 실패 시 결제 취소(보상 트랜잭션) 로직 추가 및 E2E Mock 기반 통합 테스트 필수 수행. |
| **`src/cartservice/src/cartstore/RedisCartStore.cs`**<br/>([src/cartservice/src/cartstore/RedisCartStore.cs:50-90](.../microservices-demo/src/cartservice/src/cartstore/RedisCartStore.cs#L50-L90)) | **사용자 세션 상태 저장소:** Redis 연결 풀링 및 Protobuf 직렬화/역직렬화 처리. 메모리 누수 또는 타임아웃 발생 시 전 사용자의 장바구니 담기 및 체크아웃 불가. | Redis 헬스체크 및 재연결 백오프 정책 엄격 적용, Redis 장애 시 인메모리 fallback 또는 graceful 에러 전파. |
| **`src/paymentservice/charge.js`**<br/>([src/paymentservice/charge.js:28-55](.../microservices-demo/src/paymentservice/charge.js#L28-L55)) | **신용카드 결제 유효성 및 승인 모듈:** 결제 금액 계산 오류, 자격 증명 취약점 등 보안 및 금융 정밀도에 직접적인 영향. | 엄격한 단위 테스트 스위트 도입, 카드 번호 마스킹 로깅 준수. |
| **`src/currencyservice/server.js`**<br/>([src/currencyservice/server.js:80-140](.../microservices-demo/src/currencyservice/server.js#L80-L140)) | **최고 QPS(초당 요청수) 트래픽 집중 서비스:** 상품 목록 표시, 장바구니, 체크아웃의 모든 단계에서 반복 호출되므로 연산 지연 시 전체 시스템 응답 속도 저하. | 환율 계산 결과 인메모리 캐싱(LRU 캐시) 및 gRPC 커넥션 풀 튜닝. |

---

## 2. 신규 기능 추가 체크리스트 (Recipe)

신규 비즈니스 기능(예: 할인 쿠폰 적용 시스템) 또는 신규 마이크로서비스 추가 시 반드시 준수해야 하는 엔드투엔드 개발 절차입니다 ([docs/adding-new-microservice.md:1-62](.../microservices-demo/docs/adding-new-microservice.md#L1-L62)).

### Step 1. 프로토콜 계약 정의 (`protos/demo.proto`)
- [ ] 신규 RPC 메서드 및 요청/응답 메시지를 `protos/demo.proto`에 선언.
- [ ] 각 언어별 서비스 디렉토리의 프로토콜 버퍼 컴파일 스크립트 실행 (예: `genproto.sh` 실행하여 Go, Python, Java 코드 갱신).

### Step 2. 서비스 비즈니스 로직 구현 및 단위 테스트
- [ ] 신규 서비스 디렉토리(`src/[new-service]/`) 생성 또는 기존 서비스에 핸들러 추가.
- [ ] 멀티 스테이지 빌드를 적용한 `Dockerfile` 작성 (비루트 실행 및 보안 컨텍스트 반영).
- [ ] 단위 테스트 작성 및 로컬 검증 (Go `go test`, .NET `dotnet test`, Java `./gradlew test` 등).

### Step 3. 상위 연동 서비스에 클라이언트 바인딩
- [ ] `checkoutservice` 또는 `frontend`에 신규 서비스 통신을 위한 gRPC 클라이언트 및 연결 풀 초기화 추가.
- [ ] 환경 변수 매핑 등록 (예: `COUPON_SERVICE_ADDR` 등).

### Step 4. 배포 매니페스트 및 인프라 등록
- [ ] `kubernetes-manifests/[new-service].yaml` 생성:
  - `Deployment`: `readinessProbe`, `livenessProbe`, `securityContext` (`readOnlyRootFilesystem: true`, `drop: ALL`, `runAsNonRoot: true`) 설정 필수.
  - `Service`: 클러스터 내부 통신용 ClusterIP 서비스 정의.
- [ ] `skaffold.yaml`에 신규 아티팩트 이미지 태그 및 컨텍스트 등록 ([skaffold.yaml:26-50](.../microservices-demo/skaffold.yaml#L26-L50)).
- [ ] `helm-chart/templates/` 및 `default-values.yaml`에 신규 컴포넌트 템플릿 반영.
- [ ] `kustomize/components/` 및 `kustomization.yaml`에 리소스 등록.

### Step 5. CI/CD 파이프라인 검증
- [ ] `.github/workflows/ci-main.yaml`에 단위 테스트 및 E2E Pod 헬스체크 목록 추가 ([.github/workflows/ci-main.yaml:120-135](.../microservices-demo/.github/workflows/ci-main.yaml#L120-L135)).
- [ ] `loadgenerator`의 `locustfile.py`에 신규 사용자 흐름 반영하여 성능 부하 검증.

---

## 3. 종합 평가 (Architectural Review)

### 3.1 시스템 성숙도 (Maturity) : **상 (High - Production-Ready Demo)**
- **클라우드 네이티브 모범 사례 구현:**
  - 컨테이너 보안 하드닝(비루트 실행, 리눅스 기능 제거, 읽기 전용 파일시스템)이 전 매니페스트에 일관되게 적용됨.
  - OpenTelemetry를 이용한 분산 트레이싱 및 Google Cloud Profiler가 기본 내장되어 있어 가시성이 매우 뛰어남.
  - Skaffold, Helm, Kustomize, Terraform 등 다양한 배포 도구 세트를 균형 있게 지원함.

### 3.2 기술 부채 (Technical Debt) : **중 (Moderate)**
- **분산 트랜잭션 보상 트랜잭션(Saga Rollback) 결여:**
  - `checkoutservice`가 2단계 커밋(2PC)이나 Saga 보상 메커니즘 없이 단순 순차 RPC로 구성되어 있어, 결제 후 후속 장애 시 데이터 정합성 불일치가 발생할 수 있음.
- **테스트 커버리지 불균형:**
  - Go 및 C# 서비스에는 견고한 단위 테스트가 구축되어 있으나, Node.js(`paymentservice`, `currencyservice`) 및 Python 서비스의 단위 테스트가 부재함.
- **인메모리 의존성 및 백오프 미흡:**
  - 서비스 간 gRPC 호출 시 일시적 네트워크 장애에 대응하는 재시도(Retry) 및 지수 백오프(Exponential Backoff), 서킷 브레이커 설정이 전역적으로 표준화되어 있지 않음.

### 3.3 유지보수 및 확장 용이성 (Maintainability & Extensibility) : **최상 (Excellent)**
- **모듈 격리성:** 각 서비스가 독자적인 저장소/의존성을 가지며, 단일 Protobuf 계약을 통해서만 결합되므로 개별 서비스의 언어 교체나 업그레이드가 독립적으로 가능함.
- **개발 생산성:** Skaffold를 통해 로컬 변경 사항이 실시간으로 쿠버네티스 클러스터에 핫 리로드되므로 개발자 경험(DX)이 극대화되어 있음.

