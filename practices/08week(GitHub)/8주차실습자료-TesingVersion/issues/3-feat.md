## 배경 / 문제
완료 여부로 할 일을 걸러 보는 API 가 없어 클라이언트가 전체 목록을 받아 직접 필터링합니다.

## 수용 기준 (Acceptance Criteria)
- [ ] `GET /api/items?completed=true` 는 완료 항목만 반환
- [ ] `GET /api/items?completed=false` 는 미완료 항목만 반환
- [ ] 파라미터를 생략하면 전체 목록 (기존 동작 유지)
- [ ] 잘못된 값(`?completed=abc`)은 422
- [ ] 위 4가지를 `spec/routes/test_filterItems.py` 테스트로 확인
