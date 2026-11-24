#!/usr/bin/env bash
# 실습 1. 저장소 준비 · 로컬 실행 · Issue 등록  (강의노트 37쪽)
# 블록(# ⓪ ~ # ④) 단위로 복사해 Git Bash 에서 실행하세요. gh auth login 은 브라우저 인증이 필요합니다.
LAB=${LAB:?"LAB=<8주차실습자료 경로> 를 먼저 설정"}; ME=${ME:?"ME=<GitHub ID> 를 먼저 설정"}

# ⓪ Git 사용자 · gh 인증 (workflow 범위: .github/workflows 를 push 할 때 필요)
git config --global user.name "$ME"
git config --global user.email "$ME@users.noreply.github.com"
gh auth login --hostname github.com --git-protocol https --web
gh auth refresh -s workflow,read:packages && gh auth setup-git

# ① 원본 clone → 내 계정의 새 공개 저장소 todo-lab 으로 push
git clone https://github.com/cstpeace0191/getting-started-todo-app-fastapi-claude.git todo-lab
cd todo-lab && git remote rename origin upstream
gh repo create "$ME/todo-lab" --public --source=. --remote=origin --push
gh repo set-default "$ME/todo-lab"
git tag -a v0.1.0 -m "v0.1.0 baseline" && git push origin v0.1.0

# ② 백엔드 테스트 · API 호출 — DB 경로를 지정하지 않으면 /etc/todos 권한 오류
cd backend && uv venv && source .venv/bin/activate 2>/dev/null || source .venv/Scripts/activate
uv pip install -r requirements.txt
SQLITE_DB_LOCATION=/tmp/todo-test.db pytest -q                 # 15 passed
SQLITE_DB_LOCATION=/tmp/live.db uvicorn src.main:app --port 3000 &
sleep 3; curl -s localhost:3000/api/greeting; echo              # {"greeting":"Hello world!"}
curl -s -X POST localhost:3000/api/items -H "Content-Type: application/json" -d '{"name":"PR 만들기"}'; echo
kill %1

# ③ 운영 이미지로 3개 서비스 실행 — 이 시점에는 실패해야 정상 (Issue #2)
cd .. && cp "$LAB/files/compose-prod-build.yml" .
docker compose -f compose-prod-build.yml up -d --build          # ✗ requirements-dev.txt not found

# ④ 이번 주 Issue 3건 등록 → #1 · #2 · #3
gh issue create -t "[CI] GitHub Actions CI 추가" -F "$LAB/issues/1-ci.md"
gh issue create -t "[Bug] docker build 실패 — requirements-dev.txt 없음" -F "$LAB/issues/2-bug.md" -l bug
gh issue create -t "[Feat] GET /api/items?completed= 필터" -F "$LAB/issues/3-feat.md" -l enhancement
gh issue list
