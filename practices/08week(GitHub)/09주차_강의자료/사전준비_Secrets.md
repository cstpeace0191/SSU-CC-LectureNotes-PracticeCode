# 사전 준비 — 워크플로가 쓰는 Secret · Variable

아래 목록은 실습 저장소의 워크플로를 직접 검색해 만들었습니다 (`secrets.*`, `vars.*`).

| 저장소 | 이름 | 종류 | 사용 워크플로 | 용도 |
|---|---|---|---|---|
| App | `ANTHROPIC_API_KEY` | Secret | claude · claude-review · claude-implement · claude-ci-fix · claude-release-notes | claude-code-action 의 Claude API 키 |
| App | `PROMOTER_APP_ID` | Variable | promote.yml | 승격용 GitHub App ID |
| App | `PROMOTER_APP_KEY` | Secret | promote.yml (publish.yml 이 workflow_call 로 넘김) | GitHub App 개인 키 (.pem) |
| App | `GITHUB_TOKEN` | 자동 제공 | publish.yml | ghcr.io 로그인 (`packages: write`) |
| Config | `ANTHROPIC_API_KEY` | Secret | claude-config-review · claude-sync-incident | 위와 같음 |
| Argo CD | `argocd-notifications-secret` 의 `github-token` | K8s Secret | notifications-cm.yaml | Config 저장소에 repository_dispatch 를 보내는 토큰 |

## 1. 승격용 GitHub App (22쪽)

App 저장소의 Actions 가 Config 저장소에 PR 을 열려면 저장소를 넘나드는 토큰이 필요합니다. `GITHUB_TOKEN` 은 자기 저장소에만 쓸 수 있습니다.

1. GitHub → Settings → Developer settings → GitHub Apps → New GitHub App
2. 권한: Repository permissions 의 **Contents: Read and write**, **Pull requests: Read and write** (이것만)
3. App 을 본인 계정에 설치하고, 저장소는 `todo-app-config` 하나만 선택
4. App ID 와 개인 키(.pem)를 App 저장소에 등록 (아래 명령)

클러스터 권한은 하나도 주지 않습니다. 배포는 Argo CD 가 Pull 합니다 (34쪽).

## 2. 등록 명령 (PowerShell, App 저장소 폴더에서)

```powershell
gh secret set ANTHROPIC_API_KEY
```

```powershell
gh variable set PROMOTER_APP_ID --body "<App ID>"
```

```powershell
Get-Content .\promoter.private-key.pem -Raw | gh secret set PROMOTER_APP_KEY
```

Config 저장소:

```powershell
gh secret set ANTHROPIC_API_KEY --repo <OWNER>/todo-app-config
```

Argo CD Notifications (클러스터):

```powershell
kubectl -n argocd create secret generic argocd-notifications-secret --from-literal=github-token=<repo 권한 토큰>
```

`gh secret set` 은 값을 프롬프트로 받으므로 명령 기록에 남지 않습니다. 키 값은 채팅 · 슬라이드 · 커밋에 붙여 넣지 마세요.

## 3. 그 밖에

- `agent-ready` 라벨을 App 저장소에 만들어 둡니다 (claude-implement.yml 의 트리거):

```powershell
gh label create agent-ready --color 5319e7 --description "Claude 가 구현할 이슈"
```

- Claude GitHub App 설치: Claude Code 에서 `/install-github-app` 을 실행하면 App 설치와 `ANTHROPIC_API_KEY` 등록을 한 번에 안내합니다.
- prod 승격 PR 을 사람이 승인하도록 Config 저장소에도 CODEOWNERS 와 브랜치 보호를 겁니다 (8주차 `03_PullRequests_CodeReview/브랜치보호_적용방법.md`).
