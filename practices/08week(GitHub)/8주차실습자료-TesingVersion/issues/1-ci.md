## 배경
저장소에 CI 가 없어 PR 마다 테스트 · 린트 · 이미지 빌드를 사람이 직접 확인해야 합니다.

## 할 일
- [ ] `.github/workflows/ci.yml` — backend(ruff + pytest + 커버리지 80%) · client(eslint · tsc · build) · docker(멀티 스테이지 빌드 + 스모크 테스트)
- [ ] Issue Form 2개(bug_report · feature_request) · PR 템플릿 · CODEOWNERS · dependabot
- [ ] `__pycache__` · `backend/src/static` 빌드 산출물 추적 해제 (`.gitignore`)

## 수용 기준
- [ ] PR 을 열면 3개 job 이 자동 실행된다
- [ ] backend · client job 이 통과한다
