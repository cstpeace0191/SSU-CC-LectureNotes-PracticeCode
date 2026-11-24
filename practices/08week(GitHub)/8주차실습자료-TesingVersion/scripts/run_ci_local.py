#!/usr/bin/env python3
"""ci.yml 의 job 을 로컬에서 순서대로 실행합니다 (run: 단계는 그대로, uses: 단계는 로컬 도구로 대체).

사용법 (저장소 루트에서, Git Bash · WSL · macOS · Linux):
    python run_ci_local.py . .github/workflows/ci.yml backend client docker
준비:
    pip install pyyaml                          # 이 스크립트용
    backend 폴더의 가상환경을 활성화한 상태      # pip · pytest · ruff 를 그 환경에서 사용
    Node 22 · npm (client job), Docker (docker job)
docker/build-push-action 단계는 `docker build --target <target> -t <tags> .` 로 대신 실행합니다.
"""
import os
import subprocess
import sys
import tempfile

BASH = "bash"
if sys.platform == "win32":
    for p in [r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"]:
        if os.path.exists(p):
            BASH = p
            break

try:
    import yaml
except ImportError:
    sys.exit("PyYAML 이 필요합니다:  pip install pyyaml")

if len(sys.argv) < 4:
    sys.exit(__doc__)
repo, wf_path, jobs = os.path.abspath(sys.argv[1]), sys.argv[2], sys.argv[3:]
wf = yaml.safe_load(open(os.path.join(repo, wf_path), encoding="utf-8"))
summary = tempfile.NamedTemporaryFile(delete=False, suffix=".md").name
failed = False
NOISE = ("Warning", "warnings.warn", "Requirement already satisfied", "npm warn", "WARNING", "DEPRECATION")


def show(text, n=6):
    lines = [ln for ln in text.strip().splitlines() if ln.strip() and not any(x in ln for x in NOISE)]
    for ln in lines[-n:]:
        print("     │ " + ln[:140])


for job in jobs:
    if failed:
        break
    j = wf["jobs"][job]
    wd = j.get("defaults", {}).get("run", {}).get("working-directory", ".")
    env = {**os.environ, **{k: str(v) for k, v in (wf.get("env") or {}).items()},
           **{k: str(v) for k, v in (j.get("env") or {}).items()},
           "GITHUB_STEP_SUMMARY": summary, "CI": "true"}
    print(f"\n━━━ job: {job}  ({j.get('name', job)})")
    for st in j["steps"]:
        if "uses" in st:
            u = st["uses"].split("@")[0]
            if u == "docker/build-push-action":
                w = st.get("with", {})
                cmd = ["docker", "build", "--target", w.get("target", "final"), "-t", w.get("tags", "todo-app:ci"),
                       os.path.join(repo, w.get("context", "."))]
                r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
                mark = "✓" if r.returncode == 0 else "✗"
                print(f"  {mark} {st.get('name', u)}  ({' '.join(cmd[:6])} …, exit {r.returncode})")
                show(r.stdout + r.stderr, 4)
                if r.returncode != 0:
                    failed = True
                    break
            else:
                print(f"  ◇ uses {u}  → 로컬 대체 (현재 작업 트리 · 활성화한 Python · Node)")
            continue
        name = st.get("name", st["run"].splitlines()[0][:60])
        cwd = os.path.join(repo, st.get("working-directory", wd))
        r = subprocess.run([BASH, "-e", "-o", "pipefail", "-c", st["run"]], cwd=cwd,
                           env={**env, **{k: str(v) for k, v in (st.get("env") or {}).items()}},
                           capture_output=True, text=True, errors="replace")
        mark = "✓" if r.returncode == 0 else "✗"
        print(f"  {mark} {name}  (exit {r.returncode})")
        show(r.stdout + r.stderr)
        if r.returncode != 0 and not st.get("if"):
            failed = True
            break
    if job == "docker":
        subprocess.run(["docker", "rm", "-f", "todo"], capture_output=True)

print("\n━━━ $GITHUB_STEP_SUMMARY ━━━", flush=True)
try:
    print(open(summary, encoding="utf-8", errors="replace").read(), flush=True)
except Exception as e:
    print(f"(summary read error: {e})", flush=True)
print("CI RESULT:", "FAIL" if failed else "PASS", flush=True)
sys.exit(1 if failed else 0)
