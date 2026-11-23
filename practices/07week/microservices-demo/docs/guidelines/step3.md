# [Step 3] E2E 데이터 흐름 추적 (예: [기능명])
- **아키텍처 및 실행 흐름 이해:** 모듈 간 관계, API 호출, 데이터 흐름 분석
- **트리거:** `POST /api/v1/orders`
- **호출 시퀀스:**
  1. `OrderController.create()`: 입력값 DTO 검증 및 인증 토큰 파싱
  2. `OrderService.placeOrder()`: 재고 확인 및 주문 인스턴스 생성
  3. `PaymentClient.charge()`: 외부 PG사 API 연동
  4. `OrderRepository.save()`: 트랜잭션 내 주문 정보 커밋
  5. `EventPublisher.publish()`: 'OrderCreated' 카프카 이벤트 발행
- **외부 연동 포인트:** Redis (분산 락), MySQL (영속화), PG사 API
