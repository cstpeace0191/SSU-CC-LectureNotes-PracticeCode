# 8주차 실습자료 — Git · GitHub · PR · GitHub Actions

강의노트 `08주차_강의노트(Git_GitHub_PR_GitHubActions)_20261125_final.pptx` 의 **05 실습(37~40쪽)** 과
**8주차 과제(43쪽)** 를 수행하기 위한 파일 · 스크립트 · 가이드입니다.
실습 앱은 `cstpeace0191/getting-started-todo-app-fastapi-claude`(FastAPI + React) 이고,
운영 실행은 `compose-prod-build.yml`(Traefik · backend · MySQL) 기준입니다.

각자 **내 GitHub 계정에 `todo-lab` 저장소**를 만들고, Issue 3개 → PR #4 · #5 · #6 · #7 을 직접 진행합니다.

## 1. 폴더 구성

| 경로 | 내용 | 쓰는 곳 |
|---|---|---|
| `files/compose-prod-build.yml` | 운영 이미지(target final)로 Traefik · backend · MySQL 3개 서비스 실행. 원본 저장소에는 없음 | 실습 1 ③, 실습 2 ④ |
| `issues/1-ci.md` · `2-bug.md` · `3-feat.md` | `gh issue create -F` 로 등록할 Issue 본문 | 실습 1 ④ |
| `changes/pr1-ci-setup/` | Issue #1 첫 커밋: `.github/`(ci.yml · Issue Form 2개 · PR 템플릿 · CODEOWNERS · dependabot), `.gitattributes`, `.gitignore`, ruff · pytest 설정 | 실습 2 ① |
| `changes/pr1-ruff-fix/` | Issue #1 두 번째 커밋: ruff 6건 수정, 커버리지 대상에서 mysql.py 제외 | 실습 2 ① |
| `changes/pr2-docker-fix/` | Issue #2: `requirements-dev.txt` 추가, `requirements.txt` 운영 의존성만, Dockerfile 비루트(USER 10001) · HEALTHCHECK, ci.yml 설치 단계 수정 | 실습 2 ④ |
| `changes/pr3-filter/` | Issue #3: `GET /api/items?completed=` 필터 + 테스트 4개 | 실습 3 ① |
| `changes/pr6-bob/` | 동료(bob) 역할: 같은 `get_items()` 를 "미완료 먼저" 정렬로 수정 → 충돌 유발 | 실습 3 ② |
| `answers/items.py` | 충돌 해결 예시 (필터 + 정렬 모두 유지) | 실습 3 ③ |
| `changes/publish/.github/workflows/publish.yml` | main · `v*.*.*` 태그 push 시 GHCR 게시 + 출처 증명(attestation). 9주차 승격(promote) job 은 뺀 8주차용 | 실습 4 ③ |
| `settings/protection.json` | 브랜치 보호: 필수 검사 3개 · 리뷰 1명 · CODEOWNERS 리뷰 · 대화 해결 | 실습 2 ③ |
| `settings/protection-solo.json` | 혼자 실습할 때: 필수 리뷰 0명 (나머지 동일) | 실습 2 ③ |
| `scripts/check_env.sh` | 필요한 도구 설치 · gh 로그인 상태 점검 | 시작 전 |
| `scripts/lab1_setup.sh` ~ `lab4_actions_security.sh` | 강의노트 37~40쪽 터미널 명령 전체 (설명 주석 포함) | 실습 1~4 |
| `scripts/run_ci_local.py` | `ci.yml` 의 `run:` 단계를 job 순서대로 로컬 실행 | 실습 4 ② |
| `scripts/pin_actions.py` | `uses: owner/repo@v7` → `@<커밋 SHA> # v7.0.1` 로 고정 (`git ls-remote` 조회) | 실습 4 ④ |

## 2. 준비물

| 도구 | 버전(확인 기준) | 설치 예 (Windows) |
|---|---|---|
| Git · Git Bash | 2.43 이상 | `winget install Git.Git` |
| GitHub CLI (gh) | 2.89 이상 | `winget install GitHub.cli` |
| Python + uv | 3.14 · uv 최신 | `winget install Python.Python.3.14` · `winget install astral-sh.uv` |
| Node.js | 22 LTS | `winget install OpenJS.NodeJS.LTS` |
| Docker Desktop | 최신 | `winget install Docker.DockerDesktop` |
| actionlint · zizmor | 1.7.x · 1.x | `winget install rhysd.actionlint` · `uv tool install zizmor` |

```bash
# 모든 실습에서 공통으로 쓰는 변수 — 새 터미널마다 다시 설정
LAB="/e/Lecture Notes/.../8주차실습자료"   # 이 폴더의 경로 (Git Bash 표기)
ME=<GitHub ID>
bash "$LAB/scripts/check_env.sh"
```

> 스크립트는 **블록(# ⓪, # ①, …) 단위로 복사해 실행**하는 명령 모음입니다. `gh auth login` · 리뷰 승인 · 충돌 편집처럼
> 사람이 해야 하는 단계가 섞여 있으므로 파일 전체를 한 번에 실행하지 마세요.

## 3. 실습 순서와 확인 포인트

### 실습 1. 저장소 준비 · 로컬 실행 · Issue 등록 (37쪽, `scripts/lab1_setup.sh`)
1. Git 사용자(noreply 이메일)와 gh 인증. `gh auth refresh -s workflow,read:packages` — workflow 범위가 없으면 `.github/workflows` push 가 거부됩니다.
2. 원본을 `todo-lab` 으로 clone → `origin` 을 `upstream` 으로 바꾸고 `gh repo create … --source=. --remote=origin --push` 로 내 공개 저장소를 만듭니다. `gh repo set-default` 로 이후 gh 명령의 대상을 내 저장소로 고정합니다.
3. `SQLITE_DB_LOCATION` 을 지정해 pytest(15 passed) 와 API 호출. 지정하지 않으면 일반 사용자(=CI 러너)는 `/etc/todos` 권한 오류로 5 failed.
4. `compose-prod-build.yml` 로 운영 이미지 빌드 → **`requirements-dev.txt not found` 로 실패하는 것이 정상**입니다. 이 실패를 Issue #2 로 기록합니다.
5. Issue 3건 등록 → 번호가 #1 · #2 · #3 인지 `gh issue list` 로 확인.

### 실습 2. CI PR · 브랜치 보호 · Docker 수정 PR (38쪽, `scripts/lab2_ci_protection.sh`)
1. `gh issue develop 1` 로 이슈와 연결된 브랜치 생성 → `changes/pr1-ci-setup` 복사, CODEOWNERS 의 아이디를 내 아이디로 변경.
2. `ruff check .` 가 6건 지적 → `changes/pr1-ruff-fix` 로 수정 → 통과 후 push.
3. PR #4: backend ✓ · client ✓ · **docker ✗**(Issue #2 와 같은 원인). 확인 후 **Squash merge**.
4. `protection.json` 으로 브랜치 보호 적용 → main 직접 push 가 거부되는지 확인. **혼자 하면 `protection-solo.json`** 을 쓰세요(본인 PR 은 본인이 승인할 수 없음).
5. PR #5(`changes/pr2-docker-fix`): docker ✓ → **Create a merge commit**. 이제 `compose-prod-build.yml` 실행이 성공합니다(http://localhost).

### 실습 3. 기능 PR — 충돌 해결 · Rebase merge · v0.2.0 (39쪽, `scripts/lab3_feature_conflict.sh`)
1. Issue #3 브랜치에 `changes/pr3-filter` 를 커밋 · push (PR 은 아직 만들지 않음).
2. `../bob` 폴더에서 동료 역할: `changes/pr6-bob` 로 같은 함수를 고쳐 **PR #6** 을 먼저 병합.
3. `todo-lab` 에서 `git rebase origin/main` → `CONFLICT … items.py`. 필터와 정렬을 모두 남겨 해결(`answers/items.py` 참고) → `pytest` 19 passed → `rebase --continue` → `push --force-with-lease`.
4. **PR #7** 을 Draft 로 열고 Ready → Checks 통과 → **Rebase and merge** → `v0.2.0` 주석 태그.
5. (선택) `git revert` 로 되돌리기 연습 후 `reset --hard origin/main` 으로 원상 복구(push 하지 않음).

### 실습 4. GitHub Actions — 실패 로그 · GHCR · SHA 고정 · 정적 검사 (40쪽, `scripts/lab4_actions_security.sh`)
1. `gh run list` · `gh run view <RUN_ID> --log-failed` 로 PR #4 docker job 의 실패 step 만 읽기.
2. `run_ci_local.py` 로 ci.yml 을 로컬에서 재현 → `CI RESULT: PASS` (backend `.venv` 활성화, `pip install pyyaml`).
3. `changes/publish/…/publish.yml` 을 PR 로 추가 → main 병합 시 `ghcr.io/<ID>/todo-lab:{SHA, latest}` 게시 → `docker pull` · `gh attestation verify`.
4. `pin_actions.py` 로 Action 을 커밋 SHA 로 고정 → `actionlint` · `zizmor --offline` 결과 확인 → PR.

## 4. 자주 만나는 문제

| 증상 | 원인 · 해결 |
|---|---|
| `refusing to allow an OAuth App to create or update workflow` | gh 토큰에 workflow 범위 없음 → `gh auth refresh -s workflow` |
| `gh pr create` 가 원본(cstpeace0191) 저장소로 가려 함 | `gh repo set-default $ME/todo-lab` |
| `git tag v0.1.0` 이 이미 있다고 함 | 원본에서 태그가 함께 받아진 경우 — 그대로 두고 다음 단계 진행 |
| PR 병합 버튼이 막혀 있음 | 필수 검사 미통과 또는 승인 0명 → `gh pr checks`, 혼자 실습이면 `protection-solo.json` 재적용 |
| 필수 검사가 "Expected — Waiting" 에서 멈춤 | protection 의 `contexts` 가 ci.yml 의 job `name` 과 글자 하나까지 같아야 함 |
| `docker pull ghcr.io/...` 가 denied | 패키지가 비공개 → `gh auth token \| docker login ghcr.io -u $ME --password-stdin` (read:packages 범위) |
| Windows 에서 `sed -i` 가 없음 | Git Bash 에서 실행 (PowerShell 아님) |

## 5. 과제 연결 (강의노트 43쪽)

- **과제 1** 기능 PR(`?q=` 검색) — 실습 1(Issue Form) · 실습 3(브랜치 · PR · 테스트) 흐름 그대로. 제출 `학번-이름-8week1.jpg`
- **과제 2** 코드 리뷰(인라인 코멘트 3개 이상, Suggested change 1개) — 실습 2 · 3 의 PR 에서 동료와 진행. 제출 `학번-이름-8week2.pdf`
- **과제 3** CI 확장(MySQL 서비스 컨테이너 job) — `pyproject.toml` 의 `omit` 에서 mysql.py 를 빼고 필수 검사에 등록. 제출 `학번-이름-8week3.zip`

## 6. 검증 범위

- `changes/` 의 파일은 `8주차_검증코드_및_실행로그` 폴더의 시나리오(로컬 bare 저장소를 origin 대역으로 사용)에서 실제로 실행한 것과 같습니다.
- 이 폴더를 만들 때 다시 확인한 것: baseline 에 pr1 → pr1-ruff-fix → pr2 → pr3 를 순서대로 적용해 ruff 통과 · pytest 15 → 19 passed · 커버리지 88%,
  pr6-bob 적용 후 rebase 에서 `items.py` 충돌 발생과 `answers/items.py` 로 해결, `run_ci_local.py` 의 backend job PASS, `pin_actions.py` 의 SHA 변환(강의노트 35쪽 값과 동일).
- 실제 GitHub 서버 동작(PR 화면, Actions 러너, 브랜치 보호 API, GHCR 게시)과 client · docker job 은 이 정리 과정에서 다시 실행하지 않았습니다. 수업 전 한 번 시연해 보시길 권합니다.
