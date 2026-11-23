# getting-started-todo-app-fastapi — 에이전트 작업 규칙

## 구조
- backend/: FastAPI (Python 3.12) — src/routes, src/persistence(sqlite|mysql), spec/ 에 pytest
- client/: React 19 + Vite 6 (TSX)
- Dockerfile: client-build → backend test(pytest) → final (비루트 10001)
- 배포 상태는 별도 저장소 todo-app-config (Kustomize + Argo CD) — 이 저장소에서 kubectl 사용 금지

## 반드시 지킬 것
- 테스트: `cd backend && SQLITE_DB_LOCATION=/tmp/todo-test.db pytest -q` 통과 후 커밋
- 린트: `cd backend && ruff check .` / `cd client && npm run lint`
- 커밋 메시지: Conventional Commits (feat|fix|docs|test|ci|chore)(scope): 요약 (#이슈)
- 브랜치: claude/<이슈번호>-<짧은-설명>, PR 본문에 `Closes #<번호>`
- API 변경 시 spec/routes/ 에 테스트를 함께 추가
- .github/workflows/, Dockerfile 변경은 PR 설명에 이유를 적는다 (CODEOWNERS 리뷰 대상)

## 하지 말 것
- main 에 직접 push, force push, PR 병합
- 비밀값(.env, 토큰) 커밋, requirements.txt 의 버전 하한 낮추기
