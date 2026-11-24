#!/usr/bin/env bash
# 8주차 실습 도구 점검 — 없는 도구는 ✗ 로 표시됩니다.
for c in "git --version" "gh --version" "python --version" "uv --version" "node --version" "npm --version" \
         "docker --version" "docker compose version" "ruff --version" "actionlint -version" "zizmor --version"; do
  if out=$($c 2>/dev/null | head -1); then printf '✓ %-24s %s\n' "${c%% *}" "$out"; else printf '✗ %-24s (설치 필요)\n' "$c"; fi
done
gh auth status 2>&1 | grep -E "Logged in|Token scopes" || echo "✗ gh 로그인 필요: gh auth login"
