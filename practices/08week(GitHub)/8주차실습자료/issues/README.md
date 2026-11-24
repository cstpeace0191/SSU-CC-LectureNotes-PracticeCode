# issues 디렉터리 가이드

`issues/` 디렉터리는 8주차 실습에서 GitHub CLI(`gh issue create -F <파일>`)를 통해 저장소에 등록할 **Issue 본문 마크다운 파일 모음**입니다.

GitHub Issue를 통해 버그를 제보하거나 새로운 기능을 요구하고, 이를 해결하는 브랜치와 Pull Request(PR)를 연결하여 작업하는 실무 개발 흐름을 실습합니다.

---

## 파일 목록 및 상세 내용

### 1. [`1-ci.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/issues/1-ci.md) (Issue #1: CI 구축 및 협업 템플릿)
- **실습 단계**: 실습 1 ④ 이슈 등록 $\rightarrow$ 실습 2에서 해결
- **유형**: Feature / Setup
- **배경**: 저장소에 CI가 없어 PR마다 테스트, 린트, 이미지 빌드를 개발자가 수동으로 확인해야 하는 문제를 해결하고자 함.
- **주요 요구사항**:
  - GitHub Actions CI 워크플로(`.github/workflows/ci.yml`) 구성
    - `backend`: ruff 린트, pytest, 커버리지 80% 이상 필수
    - `client`: eslint, tsc 타입체크, vite build
    - `docker`: 멀티스테이지 컨테이너 빌드 및 스모크 테스트
  - 협업 템플릿 추가 (Issue Form 2개, PR 템플릿, CODEOWNERS, Dependabot)
  - 빌드 산출물(`__pycache__`, `backend/src/static` 등)의 `.gitignore` 제외 처리
- **수용 기준 (Acceptance Criteria)**:
  - PR 오픈 시 3개 작업이 자동 실행될 것
  - backend, client 작업이 성공적으로 통과할 것

---

### 2. [`2-bug.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/issues/2-bug.md) (Issue #2: Docker 빌드 오류 수정)
- **실습 단계**: 실습 1 ④ 이슈 등록 $\rightarrow$ 실습 2 ④에서 해결
- **유형**: Bug Report
- **문제점**: 새로 clone한 저장소에서 `docker build --target final .` 또는 Docker Compose 실행 시 빌드가 실패함.
- **에러 로그**:
  ```text
  #11 [backend-dev 1/5] COPY backend/requirements-dev.txt ./
  #11 ERROR: ... "/backend/requirements-dev.txt": not found
  ```
- **원인 및 제안**:
  - 작성자 로컬 PC에만 있고 Git에는 커밋되지 않았던 `backend/requirements-dev.txt` 파일을 커밋에 추가.
  - `requirements.txt`에는 실제 운영 런타임 의존성만 남겨 컨테이너 경량화.
  - 운영 컨테이너를 루트 권한 대신 비루트 사용자(`USER 10001`)로 실행하고 `HEALTHCHECK` 추가.

---

### 3. [`3-feat.md`](file:///d:/Lecture%20Notes/2026-2CloudComputing/2026-2CloudComputing_LectureNotes/8thLecture/8주차실습자료/issues/3-feat.md) (Issue #3: 할 일 완료 여부 필터링 API)
- **실습 단계**: 실습 1 ④ 이슈 등록 $\rightarrow$ 실습 3에서 해결
- **유형**: Feature Request
- **배경**: 완료 여부로 할 일을 필터링하는 API가 없어 클라이언트가 전체 목록을 모두 다운로드하여 브라우저에서 직접 필터링해야 하는 비효율 발생.
- **수용 기준 (Acceptance Criteria)**:
  - `GET /api/items?completed=true` : 완료된 항목만 반환
  - `GET /api/items?completed=false` : 미완료된 항목만 반환
  - 파라미터 생략 시 : 전체 목록 반환 (하위 호환성 유지)
  - 잘못된 파라미터 값(`?completed=abc`) 입력 시 : 422 Unprocessable Entity 에러 반환
  - 단위 테스트(`spec/routes/test_filterItems.py`)를 통해 위 4가지 기준 검증 완료

---

## 활용 명령어 예시

```bash
# 실습 1 ④에서 Issue 3건을 한 번에 등록하는 명령:
gh issue create --title "ci: add GitHub Actions CI and collaboration templates" -F "$LAB/issues/1-ci.md"
gh issue create --title "fix(docker): requirements-dev.txt not found on fresh clone" -F "$LAB/issues/2-bug.md"
gh issue create --title "feat(api): filter items by ?completed=true|false" -F "$LAB/issues/3-feat.md"
```

