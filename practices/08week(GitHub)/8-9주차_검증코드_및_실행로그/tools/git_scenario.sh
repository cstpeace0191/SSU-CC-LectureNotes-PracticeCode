#!/usr/bin/env bash
# 8주차 Git/GitHub 시나리오를 로컬 bare 저장소(= GitHub origin 대역)로 실제 수행
set -euo pipefail
export GIT_PAGER=cat PAGER=cat GIT_CONFIG_GLOBAL=/tmp/gitcfg-sim
printf '[init]\n\tdefaultBranch = main\n' > /tmp/gitcfg-sim
V=/home/claude/verify
W=/tmp/gitlab-sim; rm -rf "$W"; mkdir -p "$W"; cd "$W"
say(){ printf '\n\033[1m$ %s\033[0m\n' "$*"; }
run(){ say "$*"; eval "$@"; }
export GIT_AUTHOR_DATE="2026-11-18T10:00:00+09:00" GIT_COMMITTER_DATE="2026-11-18T10:00:00+09:00"
tick(){ local t; t=$(date -d "${GIT_AUTHOR_DATE} +7 min" --iso-8601=seconds); export GIT_AUTHOR_DATE=$t GIT_COMMITTER_DATE=$t; }

git init -q --bare -b main origin.git          # GitHub 원격 저장소 역할

echo "##### [0] 초기 커밋과 push"
mkdir alice && cd alice
run git init -q -b main
git config user.name "cstpeace0191"; git config user.email "cstpeace0191@users.noreply.github.com"
cp -r $V/baseline/. .
run git add -A
run 'git commit -q -m "chore: initial import of todo app (FastAPI + React)"'
run git remote add origin ../origin.git
run git push -q -u origin main
run 'git tag -a v0.1.0 -m "v0.1.0 baseline"'; git push -q origin v0.1.0
run git log --oneline --decorate

echo "##### [1] Issue #1 → ci/1-github-actions 브랜치"
tick
run git switch -c ci/1-github-actions
P1=$V/changes/pr1-ci-setup
mkdir -p .github
cp -r $P1/.github/. .github/; cp $P1/.gitattributes .
cp $P1/backend/pyproject.toml $P1/backend/requirements-dev.txt $P1/backend/pytest.ini $P1/backend/main.py backend/
cp $P1/backend/spec/routes/test_updateItem.py backend/spec/routes/
run git add -A
run 'git commit -q -m "ci: add GitHub Actions CI, issue/PR templates, CODEOWNERS (#1)"'
run git status -sb
echo "--- 로컬에서 CI 단계 실행 (client lint) ---"
( cd client && rm -rf node_modules && npm ci --ignore-scripts >/dev/null 2>&1 && npm run lint 2>&1 | tail -6 ) || echo ">>> client lint 실패 (TSX 를 파싱할 TypeScript parser 없음)"
tick
cp $P1/client/.eslintrc.cjs $P1/client/package.json $P1/client/package-lock.json client/
( cd client && npm ci --ignore-scripts >/dev/null 2>&1 && npm run lint 2>&1 | tail -3 && echo ">>> client lint 통과" )
run git add client
run 'git commit -q -m "fix(client): lint TSX with @typescript-eslint/parser (#1)"'
run git push -q -u origin ci/1-github-actions
run git log --oneline main..ci/1-github-actions
run git diff --stat main...ci/1-github-actions
echo "--- PR #4 병합: Squash merge (GitHub의 'Squash and merge'와 동일 결과) ---"
tick
git switch -q main
run git merge --squash ci/1-github-actions
run 'git commit -q -m "ci: add GitHub Actions CI and collaboration templates (#4)" -m "Closes #1"'
run git push -q origin main
git branch -D ci/1-github-actions >/dev/null; git push -q origin --delete ci/1-github-actions

echo "##### [2] Issue #2 (bug) → fix/2-docker-vite-config"
tick
run git switch -c fix/2-docker-vite-config
cp $V/changes/pr2-docker-fix/Dockerfile .
run git diff --stat
run 'git commit -qam "fix(docker): copy vite.config.ts and tsconfig*.json; run as non-root (#2)"'
run git push -q -u origin fix/2-docker-vite-config
tick; git switch -q main
echo "--- PR #5 병합: Create a merge commit (--no-ff) ---"
run 'git merge -q --no-ff fix/2-docker-vite-config -m "Merge pull request #5 from cstpeace0191/fix/2-docker-vite-config"'
run git push -q origin main
git branch -d fix/2-docker-vite-config >/dev/null; git push -q origin --delete fix/2-docker-vite-config

echo "##### [3] Issue #3 (feature) → feat/3-completed-filter  /  동료 bob 의 동시 변경"
tick
run git switch -c feat/3-completed-filter
cp $V/changes/pr3-filter/backend/src/routes/items.py backend/src/routes/
cp $V/changes/pr3-filter/backend/spec/routes/test_filterItems.py backend/spec/routes/
run git add -A
run 'git commit -q -m "feat(api): filter items by ?completed=true|false (#3)"'
run git push -q -u origin feat/3-completed-filter

cd "$W"; git clone -q origin.git bob; cd bob
git config user.name "bob-reviewer"; git config user.email "bob@example.com"
tick
python3 - <<'EOF'
p='backend/src/routes/items.py'; s=open(p).read()
s=s.replace('''async def get_items():
    items = await db.get_items()
    return items''','''async def get_items():
    items = await db.get_items()
    return sorted(items, key=lambda item: item["completed"])  # 미완료 항목 먼저''')
open(p,'w').write(s)
EOF
run 'git commit -qam "feat(api): list incomplete items first (#6)"'
run git push -q origin main

cd "$W/alice"
echo "--- alice: main 이 앞서 나감 → rebase 시도 ---"
run git fetch -q origin
run git log --oneline --graph --all -8
say "git rebase origin/main"
git rebase origin/main || true
run git status -s
echo "--- 충돌 표시 ---"
sed -n '/<<<<<<</,/>>>>>>>/p' backend/src/routes/items.py
python3 - <<'EOF'
import re
p='backend/src/routes/items.py'; s=open(p).read()
s=re.sub(r"<<<<<<<.*?>>>>>>>[^\n]*\n", '''    if completed is not None:
        items = [item for item in items if item["completed"] == completed]
    return sorted(items, key=lambda item: item["completed"])  # 미완료 항목 먼저
''', s, flags=re.S)
open(p,'w').write(s)
EOF
echo "--- 해결 결과 ---"
sed -n '10,20p' backend/src/routes/items.py
echo "--- 해결 후 테스트 ---"
( cd backend && SQLITE_DB_LOCATION=/tmp/sim.db /home/claude/venv/bin/pytest -q -p no:cacheprovider 2>&1 | tail -2 )
run git add backend/src/routes/items.py
run "GIT_EDITOR=true git rebase --continue"
run git push -q --force-with-lease origin feat/3-completed-filter
run git log --oneline --graph -5
echo "--- PR #7 병합: Rebase and merge (fast-forward) ---"
tick; git switch -q main; git pull -q --ff-only origin main
run git merge --ff-only feat/3-completed-filter
run git push -q origin main
run 'git tag -a v0.2.0 -m "v0.2.0: CI + docker fix + completed filter"'; git push -q origin v0.2.0
run git log --oneline --graph --decorate -10

echo "##### [4] 잘못된 병합 되돌리기: git revert (공유 이력은 reset 금지)"
tick
run 'git revert --no-edit HEAD~0 >/dev/null; git log --oneline -2'
( cd backend && SQLITE_DB_LOCATION=/tmp/sim.db /home/claude/venv/bin/pytest -q -p no:cacheprovider 2>&1 | tail -1 )
run git reset -q --hard HEAD~1   # (실습 정리: 로컬 전용 revert 커밋 제거, push 하지 않았음)
run git log --oneline -1

echo "##### [5] 이력 조사 명령"
run git log --oneline --graph --decorate --all -12
run 'git log --format="%h %an %s" -- backend/src/routes/items.py'
run 'git blame -L 12,18 backend/src/routes/items.py | cut -c1-90'
run git describe --tags
run git shortlog -sn HEAD
run git cat-file -t HEAD
run 'git cat-file -p HEAD | head -6'
echo "SCENARIO OK"
