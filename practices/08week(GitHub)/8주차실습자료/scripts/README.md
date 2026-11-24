# scripts 디렉터리 가이드

`scripts/` 디렉터리는 8주차 실습(Git · GitHub · PR · GitHub Actions)의 각 단계별 터미널 명령어 모음 스크립트와 검증용 Python 유틸리티들을 포함하고 있습니다.

---

## 1. 실습 가이드 스크립트 (`*.sh`)

> [!IMPORTANT]
> 스크립트 파일들은 한 번에 전체를 일괄 실행(`bash script.sh`)하는 용도가 아닙니다.  
> 브라우저 인증, 코드 리뷰 승인, 코드 충돌 편집 등 **사람이 직접 개입해야 하는 단계가 포함**되어 있으므로, 스크립트 내부의 **블록 단위(`## ⓪`, `## ①`, ...)**로 복사하여 터미널(Git Bash)에서 단계별로 실행해야 합니다.

### ① [`check_env.sh`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture\8주차실습자료\scripts\check_env.sh) (사전 환경 점검)
- **목적**: 8주차 실습에 필요한 핵심 CLI 도구들의 설치 여부 및 버전 확인, GitHub CLI 로그인 상태 점검
- **점검 대상**: `git`, `gh`, `python`, `uv`, `node`, `npm`, `docker`, `docker compose`, `ruff`, `actionlint`, `zizmor`
- **실행 방법**:
  ```bash
  bash scripts/check_env.sh
  ```

### ② [`lab1_setup.sh`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\lab1_setup.sh) (실습 1: 저장소 준비 · 로컬 실행 · Issue 등록)
- **주요 내용**:
  1. `git config` 사용자 설정 및 `gh auth login` 인증 (workflow 권한 갱신)
  2. 원본 저장소 clone 후 개인 GitHub 계정의 `todo-lab` 저장소로 push (`v0.1.0` 베이스라인 태그)
  3. 백엔드 가상환경(`.venv`) 생성, 로컬 테스트 및 uvicorn 임시 실행 검증
  4. 도커 컴포즈 실행 시도 및 실패 확인 (Issue #2 버그 시뮬레이션)
  5. GitHub CLI로 실습용 Issue 3건(`1-ci`, `2-bug`, `3-feat`) 일괄 등록

### ③ [`lab2_ci_protection.sh`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\lab2_ci_protection.sh) (실습 2: CI PR · 브랜치 보호 · Docker 수정 PR)
- **주요 내용**:
  1. **Issue #1 브랜치 (`ci/1-github-actions`)**: `pr1-ci-setup` 복사, Ruff 린트 에러 수정(`pr1-ruff-fix`), 커밋 및 푸시
  2. **PR #4 생성 및 Squash Merge**: 백엔드/프론트엔드 통과 및 docker 빌드 실패 확인 후 squash 머지
  3. **브랜치 보호 규칙 적용**: `gh api`로 `settings/protection.json` 적용 및 직접 push 차단 검증
  4. **Issue #2 브랜치 (`fix/2-docker-requirements-dev`)**: `requirements-dev.txt` 추가, 비루트 실행 및 HEALTHCHECK 적용(`pr2-docker-fix`), PR 생성 및 Merge Commit 머지

### ④ [`lab3_feature_conflict.sh`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\lab3_feature_conflict.sh) (실습 3: 기능 PR · 충돌 해결 · Rebase Merge · v0.2.0)
- **주요 내용**:
  1. **Issue #3 브랜치 (`feat/3-completed-filter`)**: 필터링 기능(`pr3-filter`) 구현 커밋
  2. **동료 Bob 시뮬레이션 (`../bob`)**: 동일 함수에 미완료 정렬(`pr6-bob`)을 적용하여 먼저 PR 머지
  3. **Rebase 충돌 및 해결**: Alice 브랜치에서 `git rebase origin/main` 시 충돌 발생 $\rightarrow$ `answers/items.py`를 참조하여 수동 해결 후 `git rebase --continue`
  4. **PR 생성 및 Rebase Merge**: Draft PR 생성 후 검토 완료 및 Rebase Merge 진행
  5. **v0.2.0 태그 릴리스**: `main` 브랜치에 `v0.2.0` 태그 생성 및 원격 push

### ⑤ [`lab4_actions_security.sh`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\lab4_actions_security.sh) (실습 4: Actions 보안 · GHCR 배포 · 정적 분석)
- **주요 내용**:
  1. GitHub Actions 실패 로그 조회 (`gh run view <RUN_ID> --log-failed`)
  2. 로컬 CI 재현 (`run_ci_local.py`)
  3. GHCR 컨테이너 이미지 게시 워크플로(`publish.yml`) 추가 및 증명서 검증(`gh attestation verify`)
  4. Action 의존성 버전 태그를 불변 커밋 SHA로 고정 (`pin_actions.py`)
  5. `actionlint` 및 `zizmor`를 통한 워크플로 정적 보안 분석
  6. 스크립트 인젝션(`run: ... ${{ github.event ... }}`) 취약점 점검

---

## 2. 파이썬 유틸리티 스크립트 (`*.py`)

### ① [`pin_actions.py`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\pin_actions.py) (Action SHA 고정 도구)
- **목적**: 소프트웨어 공급망 보안을 위해 GitHub Actions 워크플로 파일 내 가변 태그(예: `uses: actions/checkout@v7`)를 불변의 40자리 커밋 해시(SHA)로 자동 변환합니다.
- **동작 원리**: `git ls-remote --tags`를 사용하여 원격 저장소의 태그에 대응하는 실제 커밋 SHA를 조회하고, 주석으로 버전명을 병기합니다.
  ```yaml
  # 변환 전:
  uses: actions/checkout@v7

  # 변환 후:
  uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v7.0.1
  ```
- **사용법**:
  ```bash
  python scripts/pin_actions.py .github/workflows/*.yml          # 직접 파일 수정
  python scripts/pin_actions.py --dry-run .github/workflows/*.yml # 변환 결과만 미리보기
  ```

### ② [`run_ci_local.py`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes\8thLecture\8주차실습자료\scripts\run_ci_local.py) (로컬 CI 실행기)
- **목적**: GitHub Actions에 코드를 푸시하기 전에, `.github/workflows/ci.yml`에 선언된 작업 단계들을 로컬 터미널 환경에서 순서대로 재현/검증합니다.
- **동작 방식**:
  - `uses: actions/checkout`, `setup-python` 등 클라우드 전용 액션은 로컬의 현재 환경으로 대체합니다.
  - `run:` 블록의 셸 명령어들을 로컬 bash 프로세스로 실행하고 종료 코드를 확인합니다.
  - `docker/build-push-action` 단계는 `docker build` 명령어로 변환하여 실행합니다.
  - 최종적으로 `$GITHUB_STEP_SUMMARY` 테이블과 `CI RESULT: PASS/FAIL` 결과를 출력합니다.
- **사용법**:
  ```bash
  # backend 작업만 로컬 재현 (가상환경 활성화 상태 권장)
  python scripts/run_ci_local.py todo-lab .github/workflows/ci.yml backend

  # 전체 작업 로컬 재현
  python scripts/run_ci_local.py todo-lab .github/workflows/ci.yml backend client docker
  ```

