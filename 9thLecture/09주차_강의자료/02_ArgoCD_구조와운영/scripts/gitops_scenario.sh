#!/usr/bin/env bash
# 9주차 GitOps 시나리오: 승격(dev) → Argo CD 자동 Sync → 드리프트 selfHeal → stg/prod 승격 → 롤백(revert)
set -uo pipefail
export PATH=~/bin:$PATH GIT_PAGER=cat
say(){ printf '\n$ %s\n' "$*"; }
run(){ say "$*"; eval "$@"; }
waitsync(){ for a in "$@"; do argocd app wait "$a" --sync --timeout 90 >/dev/null 2>&1 || echo "(wait timeout: $a)"; done; }
refresh(){ for a in "$@"; do argocd app get "$a" --refresh >/dev/null 2>&1; done; }

APP=/tmp/gitlab-sim/alice
echo "##### [1] App 저장소: 새 커밋 (main 병합 = 이미지 빌드 대상)"
cd $APP
sed -i 's/GREETING = "Hello world!"/GREETING = "Hello GitOps!"/' backend/src/routes/greeting.py
sed -i 's/"Hello world!"/"Hello GitOps!"/' backend/spec/routes/test_getGreeting.py
( cd backend && SQLITE_DB_LOCATION=/tmp/g.db /home/claude/venv/bin/pytest -q -p no:cacheprovider 2>&1 | tail -1 )
git -c user.name=cstpeace0191 -c user.email=cstpeace0191@users.noreply.github.com commit -qam "feat(api): greet with Hello GitOps! (#10)"
NEW_SHA=$(git rev-parse HEAD); echo "새 이미지 태그 = $NEW_SHA"

echo "##### [2] promote.yml 의 run 단계 그대로 실행 (TARGET_ENV=dev)"
rm -rf /tmp/promote && mkdir /tmp/promote && cd /tmp/promote
git clone -q git://127.0.0.1/todo-app-config.git config
export TARGET_ENV=dev IMAGE_TAG=$NEW_SHA IMAGE=ghcr.io/cstpeace0191/getting-started-todo-app-fastapi
[[ "$TARGET_ENV" =~ ^(dev|stg|prod)$ ]] && [[ "$IMAGE_TAG" =~ ^[0-9a-f]{40}$ ]] && echo "✓ Validate inputs"
cd config
run "yq -i '(.images[] | select(.name == strenv(IMAGE)) | .newTag) = strenv(IMAGE_TAG)' overlays/\${TARGET_ENV}/kustomization.yaml"
run git diff
BRANCH="promote/${TARGET_ENV}-${IMAGE_TAG:0:7}"
git config user.name "todo-promoter[bot]"; git config user.email "todo-promoter[bot]@users.noreply.github.com"
run git switch -c "$BRANCH"
run "git commit -qam \"deploy(${TARGET_ENV}): \${IMAGE##*/}@\${IMAGE_TAG:0:7}\" && git log --oneline -1"
run git push -q -u origin "$BRANCH"
echo "(GitHub 에서는 여기서 gh pr create → Validate manifests 통과 → 병합)"
echo "--- Config 저장소 CI(validate.yml) 단계 실행 ---"
kustomize build overlays/dev > /tmp/rendered.yaml && kubeconform -strict -summary -kubernetes-version 1.33.0 /tmp/rendered.yaml && kube-linter lint /tmp/rendered.yaml --config .kube-linter.yaml | tail -1
echo "--- PR 병합 (squash) ---"
git switch -q main && git merge -q --squash "$BRANCH" && git commit -qm "deploy(dev): ${IMAGE_TAG:0:7} (#2)" && git push -q origin main
run git log --oneline -3

echo "##### [3] Argo CD: Git 변경 감지 → 자동 Sync (todo-dev)"
refresh todo-dev; waitsync todo-dev
run "argocd app get todo-dev | sed -n '1,14p'"
run "kubectl -n todo-dev get deploy todo-app -o jsonpath='{.spec.template.spec.containers[0].image}{\"\\n\"}'"
run "kubectl -n todo-stg get deploy todo-app -o jsonpath='{.spec.template.spec.containers[0].image}{\"\\n\"}'"

echo "##### [4] 드리프트: 누군가 kubectl 로 직접 변경 → selfHeal 이 Git 상태로 복구"
run kubectl -n todo-dev scale deploy todo-app --replicas=3
run "kubectl -n todo-dev get deploy todo-app -o jsonpath='{.spec.replicas}{\"\\n\"}'"
sleep 12
run "kubectl -n todo-dev get deploy todo-app -o jsonpath='replicas={.spec.replicas}{\"\\n\"}'"
run "argocd app history todo-dev"

echo "##### [5] prod 는 수동: 승격 PR 병합 후에도 OutOfSync → 사람이 Sync"
cd /tmp/promote/config
export TARGET_ENV=prod
yq -i '(.images[] | select(.name == strenv(IMAGE)) | .newTag) = strenv(IMAGE_TAG)' overlays/prod/kustomization.yaml
git commit -qam "deploy(prod): ${IMAGE_TAG:0:7} (#3)" && git push -q origin main
refresh todo-prod; sleep 3
run "argocd app list -o wide | cut -c1-150"
run "argocd app diff todo-prod | grep -E '^[<>].*image:'"
run "argocd app sync todo-prod | tail -4"
waitsync todo-prod

echo "##### [6] 롤백: Config 저장소에서 git revert → Argo CD 가 이전 태그로"
run "git revert --no-edit HEAD && git push -q origin main && git log --oneline -2"
refresh todo-prod; sleep 2
run "argocd app sync todo-prod | tail -3"
waitsync todo-prod
run "kubectl -n todo-prod get deploy todo-app -o jsonpath='{.spec.template.spec.containers[0].image}{\"\\n\"}'"
run "argocd app history todo-prod"
echo "##### [7] 최종 상태"
run "argocd app list"
echo "GITOPS SCENARIO OK"

echo "##### [8] 동기화 실패 → Argo CD Notifications → GitHub repository_dispatch (로컬 수신기)"
rm -f /tmp/caught.json
cd /tmp/promote/config && git pull -q
cat >> overlays/dev/kustomization.yaml <<'YAML'
patches:
  - target: { kind: Deployment, name: todo-app }
    patch: |-
      - op: replace
        path: /spec/template/spec/containers/0/ports/0/containerPort
        value: 70000
YAML
git -c user.name=student -c user.email=student@example.com commit -qam "chore(dev): change container port" && git push -q origin main
run "git log --oneline -1"
refresh todo-dev
for i in $(seq 1 20); do P=$(kubectl -n argocd get application todo-dev -o jsonpath='{.status.operationState.phase}'); M=$(kubectl -n argocd get application todo-dev -o jsonpath='{.status.operationState.syncResult.revision}'); [ "$P" = "Failed" ] && break; sleep 5; done
run "argocd app get todo-dev | grep -E 'Sync Status|Phase|Message' | cut -c1-200"
run "kubectl -n argocd get application todo-dev -o jsonpath='{.status.operationState.phase}{\"\\n\"}'"
run "argocd admin notifications trigger run on-sync-failed todo-dev -n argocd"
for i in $(seq 1 12); do [ -f /tmp/caught.json ] && break; sleep 5; done
run "cat /tmp/caught.json"
echo "##### [9] 사람(또는 에이전트 롤백 PR)이 revert → 복구"
cd /tmp/promote/config
run "git -c user.name=student -c user.email=student@example.com revert --no-edit HEAD >/dev/null && git push -q origin main && git log --oneline -3"
refresh todo-dev; argocd app sync todo-dev >/dev/null 2>&1; waitsync todo-dev
run "argocd app list"
echo "SCENARIO2 OK"
