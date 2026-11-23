# [Step 4] 아키텍처 및 품질 감사

## 1. 적용된 아키텍처 스타일
Online Boutique는 클라우드 네이티브 환경에 최적화된 **폴리글랏 마이크로서비스 아키텍처 (Polyglot Microservices Architecture)**를 채택하고 있습니다.

1. **폴리글랏 기술 스택 채택:**
   - 도메인별 최적 언어/프레임워크 활용: 고성능 웹 게이트웨이 및 코디네이터는 Go, 캐시/스토리지 연동은 C# .NET, 수치 환율 연산 및 결제는 Node.js, AI/알림은 Python, 타겟 광고는 Java 사용.
2. **인터페이스 중심 설계 (Schema-First Contract):**
   - 모든 서비스 간 결합도를 낮추기 위해 Protocol Buffers v3(`protos/demo.proto`)를 단일 진실 공급원(SSOT)으로 정의하고, gRPC를 통해 엄격한 타입 안정성을 가진 동기 통신을 수행함 ([protos/demo.proto:1-263](.../microservices-demo/protos/demo.proto#L1-L263)).
3. **오케스트레이션 기반 분산 워크플로우 (Orchestration Pattern):**
   - 분산된 서비스들을 결합하기 위해 `checkoutservice`가 중앙 오케스트레이터 역할을 담당하여 장바구니 조회 -> 상품 단가 확인 -> 환율 변환 -> 배송비 계산 -> 결제 승인 -> 배송 접수 -> 장바구니 초기화 -> 이메일 발송 파이프라인을 일괄 제어함 ([src/checkoutservice/main.go:230-280](.../microservices-demo/src/checkoutservice/main.go#L230-L280)).
4. **Backend For Frontend (BFF) 유사 게이트웨이:**
   - `frontend` 서비스가 웹 브라우저 요청을 받아 쿠키 기반 세션 관리와 정적 자원/HTML 렌더링을 처리하며, 백엔드 gRPC 서비스들의 데이터를 집합(Aggregation)하여 단일 뷰 모델로 투영함 ([src/frontend/handlers.go:1-636](.../microservices-demo/src/frontend/handlers.go#L1-L636)).

---

## 2. 공통 코드 규칙 (Code Conventions)

### 2.1 에러 처리 규칙
- **gRPC 표준 상태 코드 준수:**
  - 비즈니스 예외 및 네트워크 에러는 `google.golang.org/grpc/codes` 및 `status.Errorf()`를 사용하여 gRPC 표준 상태 코드로 맵핑됨.
    - 입력값 오류: `codes.InvalidArgument`
    - 리소스 없음: `codes.NotFound`
    - 서버 내부 오류: `codes.Internal`
    - 다운스트림 일시적 장애: `codes.Unavailable` ([src/checkoutservice/main.go:235-260](.../microservices-demo/src/checkoutservice/main.go#L235-L260))
- **에러 래핑 및 전파:**
  - Go 서비스: `github.com/pkg/errors`의 `errors.Wrapf()`를 활용하여 근본 원인(Root Cause)과 콜 스택을 보존함.
  - Node.js 서비스: gRPC 콜백의 첫 번째 인자로 `{ code: grpc.status.INVALID_ARGUMENT, message: "..." }` 구조체를 반환 ([src/paymentservice/charge.js:33-40](.../microservices-demo/src/paymentservice/charge.js#L33-L40)).
  - C# 서비스: `Grpc.Core.RpcException`을 통해 gRPC 상태 코드를 클라이언트에 전파.
  - Python 서비스: `context.abort(grpc.StatusCode.NOT_FOUND, "...")` 패턴 사용.

### 2.2 로깅 및 관측성 규칙
- **구조화된 필드 로깅 (Structured Logging):**
  - Go: `sirupsen/logrus`를 사용하며 `log.WithField("order", ...).Info(...)` 형태로 키-값 구조화 로깅 준수 ([src/frontend/handlers.go:375](.../microservices-demo/src/frontend/handlers.go#L375)).
  - Node.js: `pino` 초고속 JSON 로거를 채택하여 표준 출력으로 스트리밍 ([src/paymentservice/index.js:20-25](.../microservices-demo/src/paymentservice/index.js#L20-L25)).
  - Java: `Log4j2`를 사용한 표준 로깅 ([src/adservice/build.gradle:43](.../microservices-demo/src/adservice/build.gradle#L43)).
- **분산 트레이싱 컨텍스트 전파:**
  - W3C Trace Context 표준(`traceparent`)을 지원하는 OpenTelemetry SDK가 연동되어 전 서비스 간 요청 추적이 가능함 ([src/checkoutservice/main.go:134-140](.../microservices-demo/src/checkoutservice/main.go#L134-L140)).

---

## 3. 테스트 환경 및 품질 상태 감사

### 3.1 서비스별 테스트 러너 및 구현 상태

| 서비스 | 테스트 러너 | 테스트 파일 위치 | 격리 방식 및 대상 |
| :--- | :--- | :--- | :--- |
| **frontend** | Go `testing` (`go test`) | `src/frontend/validator/validator_test.go`<br/>`src/frontend/money/money_test.go` | 폼 입력 DTO 유효성 검증, 화폐 연산 정밀도 검증 |
| **checkoutservice** | Go `testing` (`go test`) | `src/checkoutservice/money/money_test.go` | 결제 금액 합산 및 화폐 단위 변환 테스트 |
| **productcatalogservice** | Go `testing` (`go test`) | `src/productcatalogservice/product_catalog_test.go` | Mock 카탈로그 객체 기반의 메모리 격리 조회/검색 테스트 |
| **shippingservice** | Go `testing` (`go test`) | `src/shippingservice/shippingservice_test.go` | 인메모리 gRPC 서버 객체 기반 배송 견적 및 추적 번호 검증 |
| **cartservice** | .NET `xUnit` (`dotnet test`) | `src/cartservice/tests/CartServiceTests.cs` | `Microsoft.AspNetCore.TestHost` 및 `LocalCartStore`(인메모리)를 활용한 Redis 의존성 없는 완전 격리 테스트 |
| **paymentservice** | N/A (미구현) | `package.json`의 scripts.test가 exit 1로 설정됨 | 단위 테스트 부재 |
| **currencyservice** | N/A (미구현) | `package.json`의 scripts.test가 exit 1로 설정됨 | 단위 테스트 부재 |
| **adservice** | Gradle `test` | `src/test/java` 디렉토리 부재 | 단위 테스트 부재 |
| **emailservice** | Python `unittest` | 전용 테스트 파일 부재 (client.py 연동 샘플만 존재) | 단위 테스트 부재 |
| **recommendationservice** | Python `unittest` | 전용 테스트 파일 부재 (client.py 연동 샘플만 존재) | 단위 테스트 부재 |

### 3.2 테스트 격리 방식 평가
- **긍정적 설계:**
  - `cartservice`는 `ICartStore` 인터페이스 다형성을 제공하여, 단위 테스트 시 Redis 인스턴스 없이 `LocalCartStore.cs` 인메모리 딕셔너리로 완벽하게 격리된 테스트를 수행함 ([src/cartservice/tests/CartServiceTests.cs:33-39](.../microservices-demo/src/cartservice/tests/CartServiceTests.cs#L33-L39)).
  - `productcatalogservice` 및 `shippingservice`는 파일 I/O 및 네트워크를 모킹한 단위 테스트를 구성하여 CI 단계에서 고속 실행이 가능함.
- **제약점 및 주의사항:**
  - 로컬 오프라인 샌드박스 빌드 시 Go 모듈 의존성 캐시(`GOCACHE`)가 지정되지 않거나 외부 프록시 통신이 차단될 경우 테스트 빌드가 실패할 수 있으므로, 컨테이너 빌드 환경에서의 벤더링 또는 캐시 마운트가 권장됨.

---

## 4. 아키텍처 품질 및 기술 부채 감사

1. **분산 트랜잭션 보상(Saga Compensation) 부재:**
   - `checkoutservice`에서 카드 결제(`chargeCard`)가 승인된 후, 다운스트림 `shipOrder` 호출이 실패하면 결제를 자동 취소(Refund)하거나 사용자에게 롤백을 알리는 보상 트랜잭션 로직이 결여되어 있음 ([src/checkoutservice/main.go:252-261](.../microservices-demo/src/checkoutservice/main.go#L252-L261)).
2. **동기 호출 체인의 연쇄 지연(Cascading Latency) 리스크:**
   - 7개의 마이크로서비스가 직렬 동기 RPC로 연결되어 있어, 중간 한 서비스(`currencyservice` 등)의 응답 지연이 전체 체크아웃 지연으로 직결됨. 서킷 브레이커(Circuit Breaker) 또는 비동기 이벤트 큐 도입이 유효함.
3. **Node.js/Python/Java 서비스의 테스트 커버리지 결여:**
   - 핵심 금융 로직을 수행하는 `paymentservice`에 단위 테스트 스위트가 부재하여 회귀 테스트(Regression Test) 안전망 보강이 시급함.

