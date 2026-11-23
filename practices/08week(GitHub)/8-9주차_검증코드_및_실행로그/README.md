# 8·9주차 보충자료 — 코드 검증 결과 (2026-11-18)

## 저장소
- `repos/getting-started-todo-app-fastapi` : 실습 시나리오를 실제로 수행한 App 저장소 (.git 이력 포함)
  - v0.1.0 → PR#4(ci, squash) → PR#5(docker, merge) → #6(bob) → PR#7(filter, rebase) → v0.2.0
  - #8 publish/promote/release/pr-title, #9 Claude Code 워크플로 · CLAUDE.md · .claude/, #10 greeting
- `repos/todo-app-config` : GitOps Config 저장소 (base · overlays · argocd · workflows, 승격 · 롤백 이력 포함)

## 실행한 검증
| 대상 | 도구 | 결과 로그 |
|---|---|---|
| 백엔드 테스트 | pytest (19 passed, coverage 88.6%) | logs/log_ci_pass.txt |
| API | uvicorn + curl | logs/log_api.txt |
| Git 시나리오 | tools/git_scenario.sh (bare origin + 2인) | logs/log_git_clean.txt |
| Dockerfile | tools/dockerfile_emulate.py (원본 FAIL / 수정본 PASS), hadolint | logs/log_docker_*.txt |
| ci.yml | tools/run_ci_local.py | logs/log_ci.txt (수정 전) · log_ci_pass.txt |
| 워크플로 | actionlint 1.7.12, zizmor 1.32 | logs/log_actionlint.txt · log_pin.txt |
| gh 명령 56개 | tools/gh_flags_check.py (gh 2.89) | logs/log_gh.txt |
| 브랜치 보호 · Ruleset JSON | GitHub REST OpenAPI 스키마 | logs/log_protection.txt · log_ruleset.txt |
| K8s 매니페스트 | kustomize 5.8.3, kubeconform 0.8.0, kube-linter 0.8.3, kube-apiserver 1.33 dry-run | logs/log_validate.txt · log_k8s_apply.txt |
| Argo CD v3.6.1 | 실제 바이너리(repo-server · controller · appset · server · notifications) + envtest API 서버 | logs/log_argocd*.txt · log_gitops.txt |
| Claude Code 설정 | SchemaStore 스키마, claude-code-action v1 action.yml 대조, 훅 실행, CLI 2.1.327 | 9주차 07 · 08장 |

## 실행하지 못한 것
- 실제 docker build (Docker Hub 접근 차단), KIND/GKE 클러스터 생성, GitHub 서버 측 동작(PR · Actions 러너), Claude API 호출
- Argo CD 검증 환경에는 kubelet 이 없어 Pod 가 실행되지 않음 (Health: Progressing)
- 로컬 검증에서 repoURL 은 git://127.0.0.1/todo-app-config.git, 알림 URL 은 로컬 수신기로 대체
