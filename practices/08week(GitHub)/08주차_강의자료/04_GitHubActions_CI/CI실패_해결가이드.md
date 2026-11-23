# CI 첫 실행 실패 4가지와 해결 (강의노트 3 · 31 · 32쪽)

ci.yml 을 처음 넣은 PR #4 는 실제로 실패합니다. 아래 네 가지를 차례로 고치면 통과합니다.

| # | job | 증상 (로그) | 원인 | 해결 | 근거 파일 |
|---|---|---|---|---|---|
| 1 | backend | `PermissionError`, `5 failed, 10 passed` | `src/persistence/sqlite.py` 의 기본 DB 경로가 `/etc/todos/todo.db` 라 일반 사용자(러너)는 디렉터리를 만들 수 없음 | job 에 `env: SQLITE_DB_LOCATION: /tmp/todo-test.db` | `files/.github/workflows/ci.yml` 25~26행 |
| 2 | client | `client lint 실패 (TSX 를 파싱할 TypeScript parser 없음)` | 클라이언트가 TSX 로 바뀌었는데 ESLint 설정은 JS 파서 | `@typescript-eslint/parser` 추가, `.eslintrc.cjs` 수정 | `../01_실습앱과_Git핵심/logs/log_git_clean.txt` [1] 단계 |
| 3 | backend | `FAIL Required test coverage of 80% not reached. Total coverage: 64.83%` | 로컬 테스트가 닿지 않는 `src/persistence/mysql.py` 가 커버리지에 포함 | `pyproject.toml` 의 `[tool.coverage.run] omit` 에 mysql.py 를 넣고 **이유를 주석으로 남김** → 88.61% | `logs/log_ci.txt` → `logs/log_ci_pass.txt` |
| 4 | docker | `COPY client/vite.config.js` 소스 없음 (Issue #2) | TSX 전환으로 `vite.config.ts` 가 되었는데 Dockerfile 은 옛 이름 | `vite.config.ts` · `tsconfig*.json` 복사, `npm ci --ignore-scripts`, 비루트 사용자(10001) · HEALTHCHECK 추가 | `logs/log_dockerfile_diff.txt`, `log_docker_baseline.txt` → `log_docker_fixed.txt` |

## 읽는 순서 (32쪽)

1. 어느 job · step 이 실패했는지 확인합니다: `gh pr checks <번호>`
2. 마지막 줄이 아니라 **첫 번째 오류**를 찾습니다: `gh run view --log-failed`
3. 같은 명령, 같은 환경 변수로 로컬에서 재현합니다.
4. 원인을 분류합니다: 코드 버그 / 테스트 문제 / 환경 차이 / 도구 버전 / flaky
5. 고친 뒤 push 하면 PR 이 갱신되며 CI 가 다시 돕니다. 일시 오류라면 `gh run rerun --failed` 를 씁니다.
6. 재발을 막는 테스트나 설정을 남깁니다.

**금지:** 테스트를 지우거나 skip 해서 통과시키기, `continue-on-error: true` 로 덮기.

> 과제 3(MySQL 서비스 컨테이너)은 3번에서 뺀 `mysql.py` 를 다시 커버리지에 넣는 작업입니다.

## 로컬에서 같은 명령 실행 (Windows PowerShell)

backend (`backend` 폴더에서):

```powershell
$env:SQLITE_DB_LOCATION = "$env:TEMP\todo-test.db"; ruff check .; pytest -q --cov=src --cov-fail-under=80
```

client (`client` 폴더에서):

```powershell
npm ci --ignore-scripts; npm run lint; npm run build
```
