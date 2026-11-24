# GitHub Dependabot 및 브랜치 Check Status 해설

이 문서는 저장소의 자동 의존성 업데이트 도구인 **Dependabot 설정(`dependabot.yml`)**, 이로 인해 자동 생성된 원격 브랜치들, 그리고 GitHub 브랜치 목록 화면에 표시되는 **Check status**의 의미 및 실패 원인을 설명합니다.

---

## 1. `.github/dependabot.yml` 설정 내용 및 동작 설명

`.github/dependabot.yml` 파일은 GitHub의 자동 의존성 관리 봇인 **Dependabot**이 어떤 패키지 생태계(ecosystem)와 디렉터리를 감시하고, 언제 업데이트 Pull Request를 생성할지 정의한 설정 파일입니다.

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /backend
    schedule: { interval: weekly }
    groups:
      python-deps: { patterns: ["*"] }
  - package-ecosystem: npm
    directory: /client
    schedule: { interval: weekly }
    groups:
      npm-deps: { patterns: ["*"] }
  - package-ecosystem: github-actions
    directory: /
    schedule: { interval: weekly }
  - package-ecosystem: docker
    directory: /
    schedule: { interval: weekly }
```

### 항목별 상세 설명:

1. **`version: 2`**:
   - Dependabot 설정 파일의 최신 v2 규격을 사용함을 지정합니다.

2. **백엔드 Python 패키지 검사 (`pip`)**:
   - `package-ecosystem: pip`: Python 패키지 관리자(`requirements.txt` 등)를 대상으로 지정합니다.
   - `directory: /backend`: 백엔드 소스 코드가 위치한 `/backend` 디렉터리를 탐색합니다.
   - `schedule: { interval: weekly }`: 매주 1회 주기적으로 새 버전 및 보안 패치를 확인합니다.
   - `groups: python-deps: { patterns: ["*"] }`: 업데이트가 여러 개 발생할 경우 PR을 개별로 수십 개 만들지 않고, **하나의 PR로 모아서(`python-deps`) 생성**하도록 그룹화합니다. (→ PR #9 생성)

3. **프론트엔드 Node.js 패키지 검사 (`npm`)**:
   - `package-ecosystem: npm`: Node.js npm 패키지(`package.json`, `package-lock.json`)를 대상으로 지정합니다.
   - `directory: /client`: 프론트엔드가 위치한 `/client` 디렉터리를 탐색합니다.
   - `schedule: { interval: weekly }`: 매주 1회 점검합니다.
   - `groups: npm-deps: { patterns: ["*"] }`: npm 패키지 변경사항을 **하나의 PR로 모아서(`npm-deps`) 생성**합니다. (→ PR #10 생성)

4. **GitHub Actions 워크플로 액션 검사 (`github-actions`)**:
   - `package-ecosystem: github-actions`: `.github/workflows/` 내 워크플로 파일에서 사용하는 Actions 도구 버전(예: `actions/checkout@v7` 등)을 점검합니다.
   - `directory: /`: 루트 경로 기준으로 워크플로 폴더를 감시합니다.
   - `schedule: { interval: weekly }`: 매주 1회 점검합니다.

5. **도커 베이스 이미지 검사 (`docker`)**:
   - `package-ecosystem: docker`: 루트 디렉터리의 `Dockerfile` 등에 명시된 베이스 이미지 태그(예: `python:3.14-slim`, `busybox`, `mysql` 등)의 최신 릴리스를 확인합니다.
   - `directory: /`: 루트 경로의 Dockerfile을 대상으로 합니다.
   - `schedule: { interval: weekly }`: 매주 1회 점검하며, 업데이트할 이미지마다 각각 개별 PR을 생성합니다. (→ PR #7, #8 등 생성)

---

## 2. 원격 브랜치들의 생성 배경 및 시점

GitHub 저장소의 `Branches` 페이지에 표시되는 원격 브랜치들은 크게 **Dependabot 자동 생성 브랜치**와 **사용자 작업 브랜치**로 구분됩니다.

### (1) Dependabot 자동 생성 브랜치 (`dependabot/...`)
- **생성 시점**: `main` 브랜치에 `.github/dependabot.yml` 설정이 머지된 직후 (약 8시간 전)
- **생성 원인**: 
  - `dependabot.yml`이 `main`에 등록되자마자 Dependabot이 즉시 1회성 스캔을 수행하였습니다.
  - 최신 버전 업데이트가 감지된 항목들에 대해 고유한 브랜치를 자동 생성하고 연계된 Pull Request(PR)를 오픈했습니다.

#### 현재 생성된 Dependabot 브랜치 및 PR 목록:
| 브랜치명 | 대상 에코시스템 | 관련 PR | 목적 |
| :--- | :--- | :---: | :--- |
| `dependabot/docker/python-3.15-slim` | Docker (`/`) | PR #7 | Dockerfile의 베이스 이미지를 Python 3.15-slim으로 버전 갱신 |
| `dependabot/docker/busybox-1.38` | Docker (`/`) | PR #8 | Dockerfile의 busybox 이미지를 1.38 버전으로 갱신 |
| `dependabot/pip/backend/python-deps-...` | pip (`/backend`) | PR #9 | 백엔드 파이썬 패키지(FastAPI, Uvicorn 등) 일괄 갱신 |
| `dependabot/npm_and_yarn/client/npm-deps-...` | npm (`/client`) | PR #10 | 프론트엔드 의존성 패키지 일괄 갱신 |

---

### (2) 작업용 브랜치 (`fix/2-docker-requirements-dev`)
- **생성 시점**: 실습자가 로컬에서 작업 후 원격으로 푸시한 시점 (최근 갱신)
- **생성 원인**:
  - `main` 브랜치의 도커 빌드 실패 원인인 `/backend/requirements-dev.txt` 누락 문제를 해결하기 위해, PR 2번 작업용으로 생성하여 원격(`origin`)으로 푸시한 브랜치입니다.

---

## 3. Check status (체크 상태)의 의미

GitHub 브랜치 목록 화면의 **Check status** 열은 각 브랜치의 최신 커밋에 대해 실행된 **GitHub Actions CI 워크플로(Status Checks)의 종합 실행 결과**를 나타냅니다.

### (1) 아이콘 및 기호 의미
- **`❌` (빨간색 X 표시)**:
  - 해당 브랜치 커밋에서 실행된 CI 워크플로 작업(Job) 중 **최소 1개 이상이 실패(Failure)** 했음을 나타냅니다.
- **분수 표기 (`3/4`, `2/3`, `1/3` 등)**:
  - **`[성공(통과)한 작업 수] / [전체 실행된 작업 수]`** 를 의미합니다.
  - 예시:
    - **`❌ 3/4`**: 전체 4개의 작업 중 3개는 통과했으나, 1개가 실패하여 전체 결과가 실패 상태임.
    - **`❌ 2/3`**: 전체 3개의 작업 중 2개 통과, 1개 실패.
    - **`❌ 1/3`**: 전체 3개의 작업 중 1개 통과, 2개 실패.

---

## 4. 실제 CI 실패 원인 분석 (`main` 및 작업 브랜치의 `❌ 3/4`)

`.github/workflows/ci.yml`에 정의된 3가지 핵심 Job 중:
1. `✓ client (eslint + tsc + build)` → **성공**
2. `✓ backend (ruff + pytest)` → **성공**
3. `X docker (multi-stage build)` → **실패**

### 세부 실패 로그 (Docker Job):
```text
failed to solve: failed to compute cache key: failed to calculate checksum of ref ...: 
"/backend/requirements-dev.txt": not found
```
- Dockerfile 빌드 단계에서 `backend/requirements-dev.txt` 파일을 복사하려 했으나 해당 파일이 존재하지 않아 Docker 빌드가 실패하였고, 이로 인해 전체 Check status에 `❌`가 표시되었습니다.
- Dependabot 브랜치들 역시 베이스 코드의 도커 빌드 오류 또는 최신 패키지 업데이트로 인한 호환성 문제로 인해 CI 체크를 통과하지 못하고 `❌` 상태로 남아 있는 것입니다.
