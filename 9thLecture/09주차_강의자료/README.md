# 9주차 강의자료 — GitOps · Argo CD 와 Claude Code Agentic CI/CD

강의노트: `../09주차_강의노트(GitOps_ArgoCD_Claude)_20261117_final.pptx` (40쪽)
원본 검증 자료: `../8-9주차_검증코드_및_실행로그/` (2026-11-18 실행)

8주차 todo 앱을 Config 저장소 + Argo CD 로 배포하고, Claude Code 에게 PR 단위로 일을 맡깁니다.
폴더는 강의노트의 5개 장 순서대로 나뉘며, 슬라이드에 나오는 출력은 모두 `logs/` 의 실제 로그에서 가져왔습니다.

## 폴더 구성

| 폴더 | 강의노트 | 내용 |
|---|---|---|
| `01_GitOps_Config저장소/` | 01장 (5~11쪽) | Kustomize base · overlays(dev · stg · prod), validate.yml, kubeconform · kube-linter 결과 |
| `02_ArgoCD_구조와운영/` | 02장 (12~19쪽) | AppProject · ApplicationSet · root-app, 설치 · Sync · selfHeal · 롤백 로그 |
| `03_승격파이프라인과_클러스터/` | 03장 (20~24쪽) | publish.yml · promote.yml, End-to-end GitOps 시나리오 로그, KIND · GKE 실습 가이드 (추가) |
| `04_ClaudeCode_AgenticPR_CI/` | 04장 (25~32쪽) | CLAUDE.md, .claude/(settings · 훅 · 슬래시 커맨드), Claude 워크플로 5개 |
| `05_AgenticCD/` | 05장 (33~37쪽) | Config 리뷰 · 동기화 장애 대응 워크플로, Notifications 설정, 알림 payload · 롤백 로그 |
| `실습저장소/` | 전체 | 최종 App 저장소 · Config 저장소 (Git 이력 포함) |
| `사전준비_Secrets.md` | 21 · 22 · 31쪽 | 워크플로가 쓰는 Secret · Variable 과 설정 명령 (추가) |
| `과제.md` | 39쪽 | 9주차 과제 3개와 제출 체크리스트 (추가) |

각 장 폴더 구조:

- `files/`: 저장소에 그대로 넣는 파일 (경로 유지)
- `logs/`: 실제 실행 로그
- `scripts/`: 검증에 쓴 스크립트

## 장별 파일 ↔ 슬라이드

### 01 GitOps 와 Config 저장소
| 파일 | 슬라이드 |
|---|---|
| `files/base/` (deployment · service · kustomization) | 9쪽 Config 저장소 구조 |
| `files/overlays/{dev,stg,prod}/kustomization.yaml` | 10쪽 overlays/dev 와 overlays/prod |
| `files/.kube-linter.yaml` · `files/.github/workflows/validate.yml` | 11쪽, PR 마다 env 3개 matrix 검증 |
| `logs/log_validate.txt` | 11쪽 kustomize build → kubeconform · kube-linter (dev · stg · prod 모두 통과) |
| `logs/log_bad_manifest.txt` · `logs/log_weak_manifest.txt` | 대조 실험: 스키마 위반 · 보안 설정 누락이 실제로 잡히는지 |
| `logs/log_rendered_prod.txt` | prod 렌더링 결과 (LoadBalancer · 512Mi) |

### 02 Argo CD 구조와 운영
| 파일 | 슬라이드 |
|---|---|
| `files/argocd/project.yaml` | AppProject todo (허용 저장소 · 네임스페이스 · 리소스) |
| `files/argocd/applicationset.yaml` | 16쪽 list 생성기로 todo-dev · stg · prod 생성 |
| `files/argocd/root-app.yaml` | App of Apps (argocd/ 폴더를 관리) |
| `logs/log_argocd_install.txt` · `log_argocd1.txt` | 13쪽 설치 · CRD · 초기 로그인 |
| `logs/log_k8s_apply.txt` · `log_appset_generated.txt` | 15~16쪽 Project · AppSet 적용, 생성된 Application 의 syncPolicy (dev 자동, prod 수동) |
| `logs/log_argocd2.txt` · `log_appstatus.txt` · `log_tracking.txt` | 14 · 17쪽 Sync · Health · history, tracking-id 주석 |
| `scripts/gitops_scenario.sh` · `scripts/reset_gitops.sh` | 17~19쪽 시나리오(승격 → Sync → 드리프트 → 롤백) 스크립트와 초기화 |

### 03 승격 파이프라인과 클러스터
| 파일 | 슬라이드 |
|---|---|
| `files/.github/workflows/publish.yml` | 21쪽 image job → promote-dev 호출 |
| `files/.github/workflows/promote.yml` | 22쪽 GitHub App 토큰 · yq · 승격 PR |
| `logs/log_gitops.txt` | 21 · 17~19쪽 End-to-end 8단계 실제 출력 ([1] 새 커밋 → [2] promote → [3] 자동 Sync → [4] 드리프트 → [5] prod 수동 → [6] 롤백 → [7] 최종 → [8] 동기화 실패 알림) |
| `KIND_GKE_실습가이드.md` | 24쪽 (추가: Windows PowerShell 기준 명령) |

### 04 Claude Code — Agentic PR · CI
| 파일 | 슬라이드 |
|---|---|
| `files/CLAUDE.md` | 28쪽 저장소 규칙 파일 |
| `files/.claude/settings.json` | 29쪽 권한 규칙(allow · ask · deny)과 훅 |
| `files/.claude/hooks/ruff-on-edit.sh` | PostToolUse 훅: 편집 후 ruff, 실패 시 exit 2 |
| `files/.claude/commands/fix-issue.md` | 슬래시 커맨드 `/fix-issue <번호>` |
| `files/.github/workflows/claude.yml` | 30~31쪽 @claude 대화형 |
| `files/.github/workflows/claude-review.yml` | PR 자동 리뷰 (자동화 모드) |
| `files/.github/workflows/claude-implement.yml` | `agent-ready` 라벨 → 이슈 구현 PR |
| `files/.github/workflows/claude-ci-fix.yml` | CI 실패(workflow_run) → 수정 PR |
| `files/.github/workflows/claude-release-notes.yml` | 태그 push → 헤드리스 Claude 로 릴리스 노트 |

### 05 Agentic CD
| 파일 | 슬라이드 |
|---|---|
| `files/.github/workflows/claude-config-review.yml` | 37쪽 Config PR 렌더링 diff 리뷰 |
| `files/.github/workflows/claude-sync-incident.yml` | 36쪽 3~4단계: 이슈 + 롤백 PR |
| `files/argocd/notifications-cm.yaml` | 36쪽 2단계: on-sync-failed → repository_dispatch |
| `logs/log_render_diff.txt` | base · head 렌더링 diff (리뷰 입력) |
| `logs/log_notify.txt` · `log_notify_payload.json` | 36쪽 1~2단계 실제 알림과 payload |
| `logs/log_incident_gitlog.txt` | 장애 커밋(containerPort 변경)과 revert 이력 |

## 실습 저장소

| 폴더 | 최종 커밋 | 이력 |
|---|---|---|
| `실습저장소/getting-started-todo-app-fastapi/` | `8ef8077` feat(api): greet with Hello GitOps! (#10) | v0.1.0 → #4 → #5 → #6 → #7(v0.2.0) → #8 → #9(Claude) → #10 |
| `실습저장소/todo-app-config/` | `2567708` Revert "chore(dev): change container port" | 초기 구성 → dev 승격 → prod 승격 → prod 롤백 → 장애 커밋 → revert |

두 저장소 모두 `.git` 을 포함하므로 `git log --graph --oneline --all` 로 강의 흐름을 그대로 따라갈 수 있습니다.

## 참고: 검증 환경

- Argo CD v3.6.1 은 실제 바이너리와 envtest API 서버로 실행했습니다. kubelet 이 없어 Pod 는 뜨지 않으므로 Health 는 `Progressing` 으로 남습니다.
- 검증할 때는 repoURL 을 `git://127.0.0.1/todo-app-config.git` 로, 알림 URL 을 로컬 수신기로 바꿨습니다. 로그에는 `<config-repo>` 로 표시됩니다. `files/` 의 YAML 은 실제 GitHub 주소입니다.
- 실행하지 못한 것: KIND · GKE 클러스터 생성, GitHub 서버 측 동작(PR · Actions 러너), Claude API 호출.
- Claude Code 설정은 SchemaStore 스키마, claude-code-action v1 의 action.yml 과 대조하고, 훅을 실제로 실행하고, CLI 2.1.327 로 확인했습니다.
- `scripts/` 는 Linux 검증 환경의 경로(`/tmp/...`, `~/bin`)를 그대로 씁니다. 읽기 자료로 쓰고, 다시 실행하려면 경로를 바꿔야 합니다.
