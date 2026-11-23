#!/usr/bin/env python3
"""ci.yml 의 job 들을 로컬에서 실행 (run: 단계만, uses: 단계는 로컬 도구로 대체)

사용법: run_ci_local.py <repo> <workflow.yml> <job> [<job> ...]
"""
import os, subprocess, sys, tempfile, yaml

repo, wf_path, jobs = sys.argv[1], sys.argv[2], sys.argv[3:]
wf = yaml.safe_load(open(os.path.join(repo, wf_path)))
venv = "/home/claude/venv/bin"
summary = tempfile.NamedTemporaryFile(delete=False, suffix=".md").name
failed = False

for job in jobs:
    j = wf["jobs"][job]
    wd = j.get("defaults", {}).get("run", {}).get("working-directory", ".")
    env = {**os.environ, **{k: str(v) for k, v in (wf.get("env") or {}).items()},
           **{k: str(v) for k, v in (j.get("env") or {}).items()},
           "GITHUB_STEP_SUMMARY": summary, "CI": "true",
           "PATH": f"{venv}:" + os.environ["PATH"]}
    print(f"\n━━━ job: {job}  ({j.get('name', job)})")
    for st in j["steps"]:
        if "uses" in st:
            print(f"  ◇ uses {st['uses'].split('@')[0]}  → 로컬 대체(이미 checkout · python3.13 venv · node22)")
            continue
        name = st.get("name", st["run"].splitlines()[0][:60])
        if job == "docker":
            print(f"  ◇ {name} → Docker Hub 접근 불가 환경: tools/dockerfile_emulate.py 로 대체")
            continue
        cwd = os.path.join(repo, st.get("working-directory", wd))
        r = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", st["run"]], cwd=cwd,
                           env={**env, **{k: str(v) for k, v in (st.get("env") or {}).items()}},
                           capture_output=True, text=True)
        out = (r.stdout + r.stderr).strip().splitlines()
        mark = "✓" if r.returncode == 0 else "✗"
        print(f"  {mark} {name}  (exit {r.returncode})")
        for line in out[-6:]:
            print("     │ " + line[:140])
        if r.returncode != 0 and not st.get("if"):
            failed = True
            break

print("\n━━━ $GITHUB_STEP_SUMMARY ━━━")
print(open(summary).read())
print("CI RESULT:", "FAIL" if failed else "PASS")
sys.exit(1 if failed else 0)
