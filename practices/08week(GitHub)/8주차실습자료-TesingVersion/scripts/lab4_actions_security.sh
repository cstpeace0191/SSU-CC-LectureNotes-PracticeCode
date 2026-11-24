#!/usr/bin/env bash
# 실습 4. GitHub Actions — 실패 로그 · GHCR 게시 · SHA 고정 · 정적 검사  (강의노트 40쪽)
LAB=${LAB:?}; ME=${ME:?}

# ① 실행 이력과 실패 로그 (PR #4 의 docker job)
gh run list --workflow ci.yml -L 5
# gh run view <RUN_ID> --log-failed | grep -m3 -E "ERROR|not found"

# ② 로컬에서 CI 재현 (backend/.venv 활성화, pip install pyyaml 필요)
python "$LAB/scripts/run_ci_local.py" . .github/workflows/ci.yml backend client docker   # CI RESULT: PASS

# ③ 이미지 게시 워크플로 → main push 시 ghcr.io/$ME/todo-lab
git switch -c ci/publish-image
cp "$LAB/changes/publish/.github/workflows/publish.yml" .github/workflows/
git add -A && git commit -m "ci: publish image to GHCR with provenance"
git push -u origin HEAD && gh pr create --fill --base main
gh pr checks --watch && gh pr merge --squash --delete-branch
gh run watch                                                   # Publish image
gh auth token | docker login ghcr.io -u "$ME" --password-stdin
docker pull "ghcr.io/$ME/todo-lab:latest"
gh attestation verify "oci://ghcr.io/$ME/todo-lab:latest" --owner "$ME"

# ④ Action 을 커밋 SHA 로 고정 → 정적 검사
git switch main && git pull --ff-only && git switch -c ci/pin-actions
python "$LAB/scripts/pin_actions.py" .github/workflows/*.yml
actionlint && zizmor --offline .github/workflows

# ⑤ 스크립트 인젝션 점검 — 결과가 없어야 함
grep -n 'run:.*\${{ *github.event' .github/workflows/*.yml || echo "OK: run: 에 github.event 직접 사용 없음"
git commit -am "ci: pin actions to commit SHA" && git push -u origin HEAD
gh pr create --fill --base main
