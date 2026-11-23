#!/usr/bin/env python3
"""슬라이드에 쓰는 gh 명령의 하위 명령/플래그가 설치된 gh 에 실제로 존재하는지 점검."""
import re, shlex, subprocess, sys

CMDS = open(sys.argv[1], encoding="utf-8").read().strip().splitlines()
bad = 0
for line in CMDS:
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    toks = shlex.split(line)
    assert toks[0] == "gh"
    # 하위 명령 경로 찾기
    path = []
    for t in toks[1:]:
        if t.startswith("-"):
            break
        h = subprocess.run(["gh", *path, t, "--help"], capture_output=True, text=True)
        if h.returncode == 0 and ("USAGE" in h.stdout) and (not path or t in subprocess.run(["gh", *path, "--help"], capture_output=True, text=True).stdout):
            path.append(t)
        else:
            break
    help_txt = subprocess.run(["gh", *path, "--help"], capture_output=True, text=True).stdout
    flags = [t.split("=")[0] for t in toks if t.startswith("-")]
    missing = [f for f in flags if not re.search(r"(?<![\w-])" + re.escape(f) + r"(?![\w-])", help_txt)]
    status = "OK " if not missing else "BAD"
    if missing:
        bad += 1
    print(f"{status} gh {' '.join(path):<22} {' '.join(flags):<55} {('missing: ' + ' '.join(missing)) if missing else ''}")
print(f"\n{len([c for c in CMDS if c.strip() and not c.startswith('#')])} commands checked, {bad} with problems")
sys.exit(1 if bad else 0)
