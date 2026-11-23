# 8주차 강의자료 — Git · GitHub 협업과 GitHub Actions

강의노트: `../08주차_강의노트(Git_GitHub_PR_GitHubActions)_20261117_final.pptx` (41쪽)
원본 검증 자료: `../8-9주차_검증코드_및_실행로그/` (2026-11-18 실행)

이 폴더는 강의노트의 5개 장 순서대로 실습 파일 · 실제 실행 로그 · 검증 스크립트를 모아 둔 것입니다.
슬라이드에 나오는 출력은 모두 `logs/` 의 실제 로그에서 가져왔습니다.

## 폴더 구성

| 폴더 | 강의노트 | 내용 |
|---|---|---|
| `01_실습앱과_Git핵심/` | 01장 (5~13쪽) | API 호출 로그, Git 시나리오(커밋 · 브랜치 · 병합 3방식 · rebase 충돌 · revert · reflog) |
| `02_GitHub_gh_Issues/` | 02장 (14~18쪽) | Issue Form 템플릿, 슬라이드의 gh 명령 56개와 점검 결과 |
| `03_PullRequests_CodeReview/` | 03장 (19~25쪽) | PR 템플릿, CODEOWNERS, 브랜치 보호 · Ruleset JSON (추가) |
| `04_GitHubActions_CI/` | 04장 (26~33쪽) | ci.yml, Dockerfile, CI 실패 → 통과 로그, CI 실패 해결 가이드 (추가) |
| `05_배포_워크플로보안/` | 05장 (34~38쪽) | publish · release · pr-title 워크플로, SHA 고정, actionlint · zizmor 결과 |
| `실습저장소/` | 전체 | 8주차 종료 시점(#8, `a4d6ce7`) 앱 저장소 스냅샷 + 전체 커밋 그래프 |
| `과제.md` | 40쪽 | 8주차 과제 3개와 제출 체크리스트 (추가) |

각 장 폴더는 같은 구조를 씁니다.

- `files/`: 저장소에 그대로 넣는 파일 (`.github/...` 경로 유지)
- `logs/`: 실제 실행 로그
- `scripts/`: 검증에 쓴 스크립트

## 장별 파일 ↔ 슬라이드

### 01 실습 앱과 Git 핵심
| 파일 | 슬라이드 |
|---|---|
| `logs/log_api.txt` | 6쪽 REST API: curl 로 greeting · items CRUD 호출 |
| `logs/log_git_clean.txt` | 8~13쪽: bare origin + 2인(alice · bob) 시나리오 전체 (PR #4 squash → #5 merge → #7 rebase · 충돌 → revert) |
| `logs/log_show.txt` | `git show --stat` 로 커밋 내용 보기 |
| `logs/log_refs.txt` | 10쪽 브랜치 = 포인터 (`.git/HEAD`, `rev-parse`) |
| `logs/log_reflog.txt` | 13쪽 `reset --hard` 실수를 reflog 로 복구 |
| `logs/log_push_rejected.txt` | push 거부(fetch first) → pull --rebase 후 push |
| `scripts/git_scenario.sh` | 위 로그를 만든 스크립트 |

### 02 GitHub · gh CLI · Issues
| 파일 | 슬라이드 |
|---|---|
| `files/.github/ISSUE_TEMPLATE/bug_report.yml` · `feature_request.yml` · `config.yml` | 16쪽 Issue Form |
| `scripts/gh_cmds.txt` | 강의에 쓰는 gh 명령 56개 |
| `scripts/gh_flags_check.py` · `logs/log_gh.txt` | gh 2.89 에서 하위 명령 · 플래그 존재 여부 점검 (전부 OK) |

### 03 Pull Requests · Code Review
| 파일 | 슬라이드 |
|---|---|
| `files/.github/pull_request_template.md` | 21쪽 PR 본문 |
| `files/.github/CODEOWNERS` | 23쪽 |
| `files/protection.json` · `files/ruleset-main.json` · `브랜치보호_적용방법.md` | 22 · 33쪽 (추가 자료: 슬라이드 설정값으로 재구성) |
| `logs/log_protection.txt` · `logs/log_ruleset.txt` | GitHub REST OpenAPI 스키마 검증 결과 |

### 04 GitHub Actions 와 CI 파이프라인
| 파일 | 슬라이드 |
|---|---|
| `files/.github/workflows/ci.yml` | 30쪽 ci.yml 전체 구조 |
| `files/Dockerfile` | 수정본 (vite.config.ts · 비루트 · HEALTHCHECK) |
| `logs/log_ci.txt` → `logs/log_ci_pass.txt` | 31~32쪽 CI 첫 실행 실패(커버리지 64.83%) → 통과(19 passed, 88.6%) |
| `logs/log_docker_baseline.txt` → `log_docker_fixed.txt` · `log_dockerfile_diff.txt` | Issue #2: 원본 Dockerfile FAIL → 수정본 PASS |
| `scripts/run_ci_local.py` · `scripts/dockerfile_emulate.py` | ci.yml 로컬 실행기, Dockerfile 단계 흉내 실행기 |
| `CI실패_해결가이드.md` | 첫 실행 실패 원인 4가지 정리 (추가) |

### 05 배포 · 워크플로 보안
| 파일 | 슬라이드 |
|---|---|
| `files/.github/workflows/publish.yml` | 35쪽 GHCR 게시 |
| `files/.github/workflows/pr-title.yml` · `logs/log_prtitle.txt` | 36쪽 스크립트 인젝션 안전 예 (env 전달), PR 제목 검사 결과 |
| `files/.github/workflows/release.yml` | 태그 → Release |
| `files/.github/dependabot.yml` | Action · pip · npm 의존성 자동 갱신 |
| `logs/log_pin.txt` | 37쪽 Action 태그 → SHA 변환 결과 |
| `logs/log_actionlint.txt` | 38쪽 actionlint 결과 |

## 실습 저장소

`실습저장소/getting-started-todo-app-fastapi_8주차종료/` 는 커밋 `a4d6ce7`(#8: publish · promote · release · pr-title 추가) 시점의 파일입니다.
`git_log_graph.txt` 에 v0.1.0 → PR #4 → #5 → #6 → #7(v0.2.0) → #8 → #9 → #10 전체 이력이 있습니다.
Git 이력까지 포함한 최종 저장소는 `../09주차_강의자료/실습저장소/` 에 있습니다.

```powershell
cd 실습저장소\getting-started-todo-app-fastapi_8주차종료\backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:SQLITE_DB_LOCATION = "$env:TEMP\todo-test.db"; pytest -q
```

## 참고: 검증 환경

- `scripts/` 의 스크립트는 Linux 검증 환경에서 실행했습니다. `/home/claude/...`, `/tmp/...` 경로가 그대로 남아 있으므로 수업 PC 에서 다시 실행하려면 경로를 바꿔야 합니다. 내용을 읽는 참고 자료로 쓰면 됩니다.
- 실행하지 못한 것: 실제 `docker build`(Docker Hub 접근 차단), GitHub 서버 측 동작(PR 화면 · Actions 러너). Dockerfile 은 `dockerfile_emulate.py` 와 hadolint 로, ci.yml 은 `run_ci_local.py` 로 대신 검증했습니다.
- `log_git.txt`(ANSI 색 코드 포함)는 `log_git_clean.txt` 와 내용이 같아 제외했습니다.
