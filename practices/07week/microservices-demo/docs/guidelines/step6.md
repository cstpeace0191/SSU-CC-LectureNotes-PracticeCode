# [Step 6] 변경 영향도 평가 및 개발 가이드
- **주의해야 할 고위험 모듈 (High-Risk Areas):**
  - `src/billing/core.ts`: 결제 정산 엔진 (테스트 필수 통과 필요)
- **신규 기능 추가 체크리스트 (Recipe):**
  1. `src/domain/`에 비즈니스 규칙 및 엔티티 정의
  2. `src/repository/`에 DB 쿼리 인터페이스 및 구현 추가
  3. `src/service/`에 Use-Case 로직 작성 및 단위 테스트 추가
  4. `src/controller/`에 엔드포인트 연결 및 DTO 유효성 검사 등록
- **종합 평가:** (시스템의 성숙도, 기술 부채, 유지보수 용이성 요약)
