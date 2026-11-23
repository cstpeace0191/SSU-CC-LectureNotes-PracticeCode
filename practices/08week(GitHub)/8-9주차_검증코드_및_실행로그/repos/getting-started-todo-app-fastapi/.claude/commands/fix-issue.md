---
description: GitHub 이슈를 읽고 구현 → 테스트 → PR 까지
argument-hint: <이슈 번호>
allowed-tools: Bash(gh issue view:*), Bash(pytest:*), Bash(ruff check:*), Bash(git:*), Bash(gh pr create:*), Edit, Write, Read, Grep, Glob
---
이슈 #$ARGUMENTS 를 처리한다.

1. `gh issue view $ARGUMENTS --comments` 로 요구사항과 수용 기준을 읽는다.
2. 관련 코드를 찾고, 바꿀 파일과 테스트 계획을 3~5줄로 먼저 적는다.
3. 브랜치 `claude/$ARGUMENTS-<짧은-설명>` 을 만든다.
4. 테스트를 먼저 추가하고(spec/routes/), 구현한다.
5. `cd backend && SQLITE_DB_LOCATION=/tmp/todo-test.db pytest -q` 와 `ruff check .` 가 통과할 때까지 고친다.
6. Conventional Commit 으로 커밋하고 push 한 뒤
   `gh pr create --base main --title "<type>(<scope>): <요약> (#$ARGUMENTS)" --body "Closes #$ARGUMENTS ..."` 로 PR 을 연다.
7. 병합은 하지 않는다. PR 링크와 테스트 결과를 보고한다.
