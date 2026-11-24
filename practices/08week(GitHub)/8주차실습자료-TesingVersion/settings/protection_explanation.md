# GitHub Branch Protection 설정 및 명령 해설

이 문서는 `settings/protection.json` 파일의 구성 내용과 이를 원격 저장소의 `main` 브랜치에 적용하는 `gh api` 명령어의 동작 및 보호 효과를 설명합니다.

---

## 1. 명령어 분석
'현재 폴더가, 'todo-lab' 인 것으로 가정'

```bash
gh api -X PUT repos/$ME/todo-lab/branches/main/protection --input ../settings/protection.json
```

- **`gh api`**: GitHub CLI(`gh`)를 통해 GitHub REST API 엔드포인트를 직접 호출하는 명령입니다.
- **`-X PUT`**: HTTP `PUT` 메서드를 사용하여 지정한 리소스의 브랜치 보호 설정을 생성하거나 전체 덮어쓰기(업데이트)합니다.
- **`repos/$ME/todo-lab/branches/main/protection`**:
  - 대상 엔드포인트: `/repos/{owner}/{repo}/branches/{branch}/protection`
  - `$ME`: 현재 GitHub 계정 사용자명(예: `cstpeace0191`) 환경 변수입니다.
  - 대상 브랜치: 원격 저장소(`cstpeace0191/todo-lab`)의 기본 브랜치인 **`main`** 브랜치입니다.
- **`--input ../settings/protection.json`**:
  - `protection.json` 파일에 정의된 JSON 바디를 API 요청 본문(Payload)으로 전송합니다.

즉, 이 명령어는 **원격 저장소 `cstpeace0191/todo-lab`의 `main` 브랜치에 `protection.json`에 정의된 엄격한 브랜치 보호 규칙(Branch Protection Rules)을 적용**하는 작업입니다.

---

## 2. `settings/protection.json` 세부 내용 및 보호 효과

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "backend (ruff + pytest)",
      "client (eslint + tsc + build)",
      "docker (multi-stage build)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "require_code_owner_reviews": true,
    "dismiss_stale_reviews": true
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
```

### (1) `required_status_checks` (필수 상태 검사 / CI 검증)
- **`"strict": true` ("Require branches to be up to date before merging")**:
  - 머지하려는 PR 브랜치가 대상 브랜치(`main`)의 최신 커밋들을 모두 반영하고 있는 최신 상태여야만 머지를 허용합니다.
  - 다른 PR이 먼저 `main`에 머지되었다면, 내 PR 브랜치를 최신 `main`과 동기화(Rebase/Merge)한 후 다시 CI 검사를 통과해야 머지할 수 있습니다.
- **`"contexts"` (필수 통과 CI 작업 목록)**:
  - 머지되기 전에 다음 3가지 GitHub Actions 워크플로 작업(Status Check)이 **반드시 성공(Success)** 해야 합니다:
    1. `backend (ruff + pytest)`: 백엔드 린트 검사 및 단위/통합 테스트
    2. `client (eslint + tsc + build)`: 프론트엔드 린트, 타입스크립트 타입 검사 및 프로덕션 빌드
    3. `docker (multi-stage build)`: 멀티스테이지 도커 컨테이너 빌드 검증

### (2) `enforce_admins: true` (관리자 예외 배제)
- 저장소 소유자(Owner)나 관리자(Admin) 권한을 가진 계정이라도 **이 브랜치 보호 규칙을 예외 없이 강제 적용**받습니다.
- 관리자라 할지라도 규칙을 우회하여 직접 푸시하거나 승인/CI 없이 머지할 수 없습니다.

### (3) `required_pull_request_reviews` (풀 리퀘스트 및 코드 리뷰 강제)
- `main` 브랜치로의 직접 푸시(`git push origin main`)를 차단하고, 반드시 **Pull Request(PR)** 를 거치도록 합니다.
- **`"required_approving_review_count": 1`**:
  - 최소 1명 이상의 다른 리뷰어로부터 승인(Approve)을 받아야 머지가 가능합니다.
- **`"require_code_owner_reviews": true`**:
  - `.github/CODEOWNERS`에 정의된 코드 소유자(Code Owner)의 승인이 반드시 포함되어야 합니다.
- **`"dismiss_stale_reviews": true`**:
  - 승인(Approve)을 받은 상태에서 PR에 새로운 커밋이 푸시되면, 기존 승인이 자동으로 취소(Stale 처리)되어 새로운 변경사항에 대해 다시 리뷰와 승인을 받아야 합니다.

### (4) `allow_force_pushes: false` (강제 푸시 차단)
- `git push --force` 또는 `git push --force-with-lease` 명령을 차단합니다.
- 기존 커밋 히스토리가 덮어쓰여지거나 유실되는 치명적인 사고를 방지합니다.

### (5) `allow_deletions: false` (브랜치 삭제 차단)
- 원격 저장소의 `main` 브랜치가 실수로 삭제되는 것을 방지합니다.

### (6) `required_conversation_resolution: true` (코드 리뷰 대화 해결 강제)
- PR 리뷰 과정에서 남겨진 모든 코멘트/피드백 스레드가 "Resolved" 상태로 완료 처리되어야만 머지 버튼이 활성화됩니다.
- 리뷰 피드백을 확인하지 않고 지나치는 실수를 방지합니다.

### (7) 기타 설정
- **`"restrictions": null`**: 특정 사용자/팀만 푸시할 수 있도록 제한하는 커스텀 푸시 권한 제한은 두지 않고 기본 권한 모델을 따릅니다.
- **`"required_linear_history": false`**: 선형 커밋 히스토리(Rebase / Squash)를 강제하지 않으며 일반 Merge 커밋 생성을 허용합니다.

---

## 3. 요약: 원격 저장소 `main` 브랜치에 대해 보호하는 것

이 설정을 적용함으로써 `cstpeace0191/todo-lab` 저장소의 `main` 브랜치는 다음과 같이 철저히 보호됩니다:

1. **직접 변경 방지**: 누군가(관리자 포함) `main` 브랜치에 `git push`로 바로 코드를 밀어 넣는 행위 원천 차단.
2. **불안정한 코드 유입 차단**: 백엔드/프론트엔드 테스트, 린트, 도커 빌드(`contexts` 3개)가 통과하지 못한 코드는 절대 `main`에 머지 불가.
3. **검증되지 않은 코드 차단**: 최소 1인의 승인 및 CODEOWNER의 승인 없이 머지 불가, 추가 커밋 시 재승인 요구.
4. **히스토리 및 브랜치 보존**: `main` 브랜치 삭제 및 강제 푸시(`--force`)를 통한 히스토리 훼손 방지.

---

## 4. 실습 참고사항 (`protection-solo.json`과의 비교)

- `protection.json`은 팀 협업 환경을 기준으로 작성되어 있어 **최소 1인의 타인 승인(`required_approving_review_count: 1`)** 과 **코드 오너 승인**이 필수입니다.
- 만약 혼자서 1인 실습(Solo)을 진행할 경우, 본인이 올린 PR을 본인이 승인할 수 없으므로 머지가 블로킹될 수 있습니다.
- 동일 디렉터리의 `settings/protection-solo.json`은 이러한 점을 고려하여 리뷰 필수 승인 수를 `0`으로 지정하고 코드 오너 검토를 `false`로 완화한 버전입니다.

