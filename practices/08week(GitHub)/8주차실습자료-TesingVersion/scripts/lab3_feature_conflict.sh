#!/usr/bin/env bash
# 실습 3. 기능 PR — 동료 변경과 충돌 해결 · Rebase merge · v0.2.0  (강의노트 39쪽)
LAB=${LAB:?}; ME=${ME:?}

# ① Issue #3 브랜치 — ?completed= 필터 + 테스트 4개
git switch main && git pull --ff-only
gh issue develop 3 --checkout --name feat/3-completed-filter --base main
cp -r "$LAB/changes/pr3-filter/." . && git add -A
git commit -m "feat(api): filter items by ?completed=true|false (#3)"
git push -u origin feat/3-completed-filter

# ② 동료(bob) 역할 — 다른 폴더에서 같은 함수(get_items)를 먼저 고쳐 PR #6 병합
git clone "https://github.com/$ME/todo-lab.git" ../bob && cd ../bob
git switch -c feat/6-incomplete-first
cp "$LAB/changes/pr6-bob/backend/src/routes/items.py" backend/src/routes/
git commit -am "feat(api): list incomplete items first (#6)"
git push -u origin HEAD
gh pr create --fill --base main && gh pr checks --watch && gh pr merge --squash --delete-branch

# ③ 다시 alice(todo-lab) — main 이 앞서 나감 → rebase 중 충돌
cd ../todo-lab && git fetch origin
git rebase origin/main            # CONFLICT (content): Merge conflict in backend/src/routes/items.py
git status -s                     # UU backend/src/routes/items.py
# 편집기에서 <<<<<<< ~ >>>>>>> 사이를 정리: 필터와 정렬을 모두 남김 (해결 예: $LAB/answers/items.py)
(cd backend && SQLITE_DB_LOCATION=/tmp/t.db pytest -q)        # 19 passed
git add backend/src/routes/items.py && git rebase --continue
git push --force-with-lease

# ④ PR #7 → 리뷰 · 승인 → Rebase merge → 릴리스 태그
gh pr create --draft --base main --title "feat(api): filter items by ?completed=true|false" --body "Closes #3"
gh pr ready 7
gh pr checks 7 --watch && gh pr merge 7 --rebase --delete-branch
git switch main && git pull --ff-only
git tag -a v0.2.0 -m "v0.2.0: CI + docker fix + completed filter" && git push origin v0.2.0
git log --oneline --graph --decorate -8

# ⑤ (선택) 되돌리기 — 공유 이력은 revert, 로컬 연습 후 원래대로
git revert --no-edit HEAD && git log --oneline -2 && git reset --hard origin/main
