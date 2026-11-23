# Online Boutique 코드베이스 분석 보고서 목차 (Contents Overview)

본 문서는 **Online Boutique (Google Cloud Platform Microservices Demo)** 프로젝트를 대상으로 시니어 소프트웨어 아키텍트 지침에 따라 수행한 Step 1부터 Step 6까지의 심층 코드베이스 분석 보고서 전체 목차와 주요 분석 요약본입니다.

---

## 📑 생성된 단계별 분석 보고서 목록

| 단계 | 산출물 파일 | 핵심 분석 요약 |
| :--- | :--- | :--- |
| **Step 1** | [Step 1: 환경 및 구조 진단 보고서](.../microservices-demo/docs/codebase_anlaysis/step1.md) | - 11개 마이크로서비스 및 AI 어시스턴트/부하 생성기 언어 및 런타임 분석 (Go 1.25/1.27, .NET 10, Node.js 24, Java 21, Python 3.14)<br/>- 패키지 매니저 및 기술 스택 (gRPC v1, gorilla/mux, Redis, Spanner, OpenTelemetry SDK)<br/>- 주요 디렉토리 매핑 및 로컬/클러스터 빌드/테스트 구동 명령어 명세 |
| **Step 2** | [Step 2: 비즈니스 도메인 및 모델 분석](.../microservices-demo/docs/codebase_anlaysis/step2.md) | - 익명 세션(`user_id`) 기반 클라우드 네이티브 쇼핑몰 비즈니스 목표 및 멀티 통화 변환 체계<br/>- ERD 다이어그램 (User, Cart, CartItem, Product, OrderResult, Money 등)<br/>- 도메인 용어 사전 및 신용카드 유효성 검증/장바구니 증분 적재/배송비 산출 비즈니스 규칙과 주문 상태 전이도(State Diagram) |
| **Step 3** | [Step 3: E2E 데이터 흐름 추적](.../microservices-demo/docs/codebase_anlaysis/step3.md) | - 진입 트리거: `POST /cart/checkout`<br/>- 7개 분산 마이크로서비스 간 연쇄 호출 시퀀스 다이어그램 (Mermaid Sequence Diagram)<br/>- 폼 파싱/DTO 유효성 검증 -> 오케스트레이터(`CheckoutService.PlaceOrder`) -> 장바구니/카탈로그/환율/배송/결제/이메일 연쇄 호출 및 외부 연동/장애 격리 전략 상세 매핑 |
| **Step 4** | [Step 4: 아키텍처 및 품질 감사](.../microservices-demo/docs/codebase_anlaysis/step4.md) | - 폴리글랏 마이크로서비스, gRPC 스키마 기반 계약(SSOT), 오케스트레이션 패턴, BFF 구조 진단<br/>- 공통 코드 규칙 (gRPC 표준 상태 코드 맵핑, 구조화된 JSON 필드 로깅, W3C 트레이스 전파)<br/>- 단위 테스트 스위트 현황 (Go/C# 테스트 환경 및 In-Memory Mock 격리 평가, Node.js/Python 테스트 부재 진단 및 분산 롤백 결여 감사) |
| **Step 5** | [Step 5: 빌드, 실행 및 배포 파이프라인 보고서](.../microservices-demo/docs/codebase_anlaysis/step5.md) | - 멀티 아키텍처(amd64/arm64) 멀티 스테이지 Docker 빌드 및 Skaffold v3 파이프라인 분석<br/>- 로컬 에뮬레이션(`skaffold dev`, `redis-cart`, 포트포워딩, 핵심 환경 변수 주입 테이블)<br/>- GitHub Actions CI/CD 워크플로우, GKE 자동 배포, K8s RollingUpdate, Readiness/Liveness 프로브 및 보안 컨텍스트(비루트/읽기전용 FS) 분석 |
| **Step 6** | [Step 6: 변경 영향도 평가 및 개발 가이드](.../microservices-demo/docs/codebase_anlaysis/step6.md) | - 5대 고위험 모듈(`demo.proto`, `checkoutservice`, `RedisCartStore`, `paymentservice`, `currencyservice`) 영향도 및 완화책<br/>- 신규 기능/마이크로서비스 추가 레시피 체크리스트 (Proto 정의부터 K8s/Skaffold/CI 등록까지 5단계 레시피)<br/>- 아키텍처 종합 평가 (성숙도: 상 / 기술 부채: 중 / 유지보수성: 최상) |

---

## 📌 주요 특징 및 설계 하이라이트

1. **Protocol Buffers 기반 단일 진실 공급원 (SSOT):**
   - 모든 서비스 간 데이터 교환 및 RPC 계약은 [`protos/demo.proto`](.../microservices-demo/protos/demo.proto)에 정의되어 하위 호환성과 타입 안정성을 엄격히 유지합니다.
2. **폴리글랏 분산 오케스트레이션:**
   - Go, C#, Node.js, Python, Java 5개 주요 언어로 구현된 독립 서비스들이 중앙 오케스트레이터(`checkoutservice`)의 조정 하에 유기적인 전자상거래 트랜잭션을 수행합니다.
3. **프로덕션급 컨테이너 보안:**
   - 모든 쿠버네티스 워크로드가 `runAsNonRoot: true`, `capabilities.drop: ["ALL"]`, `readOnlyRootFilesystem: true` 설정을 준수하여 최소 권한 원칙을 철저히 반영하고 있습니다.

