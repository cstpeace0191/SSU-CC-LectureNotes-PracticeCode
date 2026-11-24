#!/usr/bin/env bash
# 실습 2. CI PR(Squash) · 브랜치 보호 · Docker 수정 PR(Merge commit)  (강의노트 38쪽)
# todo-lab 폴더에서 블록 단위로 실행하세요. backend 가상환경(.venv)을 활성화한 상태여야 ruff 가 동작합니다.
LAB=${LAB:?}; ME=${ME:?}

# ① Issue #1 브랜치 — CI · Issue Form · PR 템플릿 · CODEOWNERS
gh issue develop 1 --checkout --name ci/1-github-actions --base main
cp -r "$LAB/changes/pr1-ci-setup/." .
sed -i "s/cstpeace0191/$ME/" .github/CODEOWNERS               # 코드 소유자 = 나
git rm -r -q --cached backend/spec backend/src && git add -A  # __pycache__ · static 추적 해제
git commit -m "ci: add GitHub Actions CI, issue/PR templates, CODEOWNERS (#1)"
uv pip install ruff==0.17.5 pytest-cov
(cd backend && ruff check .)                                  # Found 6 errors
cp -r "$LAB/changes/pr1-ruff-fix/." . && (cd backend && ruff check .)   # All checks passed!
git commit -am "fix(backend): resolve ruff findings, scope coverage (#1)"
git push -u origin ci/1-github-actions

# ② PR #4 → Checks (backend ✓ · client ✓ · docker ✗ = Issue #2) → Squash merge
gh pr create --base main --title "ci: add GitHub Actions CI and collaboration templates" --body "Closes #1"
gh pr checks 4 --watch
gh pr merge 4 --squash --delete-branch && git switch main && git pull --ff-only

# ③ 브랜치 보호 — 혼자 실습하면 protection-solo.json (필수 리뷰 0명)
gh api -X PUT "repos/$ME/todo-lab/branches/main/protection" --input "$LAB/settings/protection.json"
git commit --allow-empty -m "test: direct push" && git push origin main   # ✗ protected branch 거부
git reset --hard origin/main

# ④ Issue #2 → PR #5 — requirements-dev.txt · 비루트 실행 · HEALTHCHECK
gh issue develop 2 --checkout --name fix/2-docker-requirements-dev --base main
cp -r "$LAB/changes/pr2-docker-fix/." . && git add -A
git commit -m "fix(docker): add missing requirements-dev.txt; run as non-root (#2)"
git push -u origin fix/2-docker-requirements-dev
gh pr create --base main --title "fix(docker): add missing requirements-dev.txt; run as non-root" --body "Closes #2"
gh pr checks 5 --watch
gh pr merge 5 --merge --delete-branch                         # (동료 Approve 후) Create a merge commit
git switch main && git pull --ff-only && git log --oneline --graph -4
docker compose -f compose-prod-build.yml up -d --build          # 이제 성공 → http://localhost
