#!/usr/bin/env bash
# PostToolUse 훅: 방금 수정한 파일이 backend/*.py 이면 ruff 로 검사 → 실패 시 exit 2 로 Claude 에게 되돌려 줌
f=$(jq -r '.tool_input.file_path // empty')
[[ "$f" == *backend/*.py ]] || exit 0
cd "$CLAUDE_PROJECT_DIR/backend" || exit 0
out=$(ruff check "$f" 2>&1) || { echo "$out" >&2; exit 2; }
exit 0
