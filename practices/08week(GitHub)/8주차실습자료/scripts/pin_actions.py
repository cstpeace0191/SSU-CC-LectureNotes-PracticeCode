#!/usr/bin/env python3
"""워크플로의 `uses: owner/repo@태그` 를 `uses: owner/repo@<커밋 SHA> # vX.Y.Z` 로 고정합니다.

사용법: python pin_actions.py .github/workflows/*.yml          (파일을 직접 수정)
        python pin_actions.py --dry-run .github/workflows/*.yml (변환 결과만 출력)
필요: git (git ls-remote 로 GitHub 의 태그를 조회 — 인증 불필요)
"""
import re
import subprocess
import sys

USES = re.compile(r"(uses:\s*)([\w.-]+/[\w.-]+)((?:/[\w./-]+)?)@([\w.-]+)(\s*#.*)?$")
SEMVER = re.compile(r"^v?\d+\.\d+\.\d+$")
cache = {}


def tags_of(repo):
    if repo not in cache:
        out = subprocess.run(["git", "ls-remote", "--tags", f"https://github.com/{repo}"],
                             capture_output=True, text=True, check=True).stdout
        tags = {}
        for line in out.splitlines():
            sha, ref = line.split("\t")
            name = ref.removeprefix("refs/tags/")
            if name.endswith("^{}"):          # 주석 태그는 가리키는 커밋(peeled) 값을 우선
                tags[name[:-3]] = sha
            else:
                tags.setdefault(name, sha)
        cache[repo] = tags
    return cache[repo]


def pin(line):
    m = USES.search(line)
    if not m or re.fullmatch(r"[0-9a-f]{40}", m.group(4)):
        return line, None
    repo, sub, ref = m.group(2), m.group(3), m.group(4)
    tags = tags_of(repo)
    if ref not in tags:
        return line, f"  ! {repo}@{ref}: 태그를 찾지 못함 (브랜치 참조는 고정하지 않음)"
    sha = tags[ref]
    exact = sorted((t for t, s in tags.items() if s == sha and SEMVER.match(t)),
                   key=lambda t: [int(x) for x in t.lstrip("v").split(".")])
    ver = exact[-1] if exact else ref
    new = line[:m.start()] + f"{m.group(1)}{repo}{sub}@{sha} # {ver}"
    return new, f"  {repo}{sub}@{ref} -> {sha[:12]}… # {ver}"


def main(argv):
    dry = "--dry-run" in argv
    files = [a for a in argv if a != "--dry-run"]
    if not files:
        print(__doc__)
        return 1
    for path in files:
        lines = open(path, encoding="utf-8").read().split("\n")
        out, changed = [], 0
        print(path)
        for line in lines:
            new, msg = pin(line)
            if msg:
                print(msg)
            changed += new != line
            out.append(new)
        if changed and not dry:
            open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out))
        print(f"  → {changed}개 고정{' (dry-run)' if dry else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
