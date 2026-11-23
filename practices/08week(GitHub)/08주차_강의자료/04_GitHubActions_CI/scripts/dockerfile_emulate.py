#!/usr/bin/env python3
"""Docker 데몬/베이스 이미지 없이 Dockerfile 을 단계별로 '흉내' 실행해 점검한다.

- 모든 COPY <컨텍스트 경로> 소스가 실제로 존재하는지 검사 (glob 포함)
- 각 stage 를 임시 디렉터리(rootfs 흉내)에 재현: COPY → RUN (npm/pip/pytest 만 실행)
- final 단계는 uvicorn 을 띄워 /api/greeting 스모크 테스트

사용법: dockerfile_emulate.py <repo_dir> [--target final]
"""
import glob, json, os, re, shlex, shutil, subprocess, sys, tempfile, time, urllib.request

repo = os.path.abspath(sys.argv[1])
target = sys.argv[sys.argv.index("--target") + 1] if "--target" in sys.argv else "final"
venv_bin = os.environ.get("VENV_BIN", "/home/claude/venv/bin")

lines, buf = [], ""
for raw in open(os.path.join(repo, "Dockerfile"), encoding="utf-8"):
    s = raw.rstrip("\n")
    if s.strip().startswith("#") and not buf:
        continue
    if s.endswith("\\"):
        buf += s[:-1] + " "
        continue
    buf += s
    if buf.strip():
        lines.append(buf.strip())
    buf = ""

stages, cur = {}, None
for ln in lines:
    m = re.match(r"FROM\s+(\S+)\s+AS\s+(\S+)", ln, re.I)
    if m:
        cur = m.group(2)
        stages[cur] = {"base": m.group(1), "steps": []}
        continue
    if cur:
        stages[cur]["steps"].append(ln)

root = tempfile.mkdtemp(prefix="dfemu-")
fs = {}          # stage -> rootfs dir
errors = []


def build(stage):
    if stage in fs:
        return fs[stage]
    info = stages[stage]
    base = info["base"]
    sroot = os.path.join(root, stage)
    if base in stages:                      # FROM <다른 stage>
        shutil.copytree(build(base), sroot, symlinks=True)
    else:
        os.makedirs(sroot)
    workdir, env = "/", {}
    if base in stages:                      # 부모 stage 의 WORKDIR/ENV 상속
        workdir, env = stages[base]["workdir"], dict(stages[base]["env"])
    print(f"\n=== stage {stage}  (FROM {base})")
    for st in info["steps"]:
        op, _, rest = st.partition(" ")
        op = op.upper()
        if op == "WORKDIR":
            workdir = rest.strip()
            os.makedirs(sroot + workdir, exist_ok=True)
        elif op == "ENV":
            k, _, v = rest.partition("=")
            env[k.strip()] = v.strip()
        elif op == "COPY":
            args = shlex.split(rest)
            src_stage = None
            if args[0].startswith("--from="):
                src_stage = args.pop(0).split("=", 1)[1]
            *srcs, dest = args
            dest_abs = sroot + (dest if dest.startswith("/") else os.path.join(workdir, dest))
            for s in srcs:
                base_dir = build(src_stage) if src_stage else repo
                pattern = os.path.join(base_dir, s.lstrip("/")) if src_stage else os.path.join(repo, s)
                hits = glob.glob(pattern)
                if not hits:
                    errors.append(f"[{stage}] COPY 소스 없음: {s}")
                    print(f"  ✗ COPY {s}  -> 없음!")
                    continue
                for h in hits:
                    if os.path.isdir(h) and (dest.endswith("/") is False and len(srcs) == 1 and not dest.endswith("./")):
                        shutil.copytree(h, dest_abs, dirs_exist_ok=True)
                    elif os.path.isdir(h):
                        shutil.copytree(h, os.path.join(dest_abs, os.path.basename(h)), dirs_exist_ok=True)
                    else:
                        os.makedirs(dest_abs if dest.endswith("/") or len(srcs) > 1 or len(hits) > 1 else os.path.dirname(dest_abs), exist_ok=True)
                        tgt = os.path.join(dest_abs, os.path.basename(h)) if (dest.endswith("/") or len(srcs) > 1 or len(hits) > 1) else dest_abs
                        shutil.copy2(h, tgt)
                print(f"  ✓ COPY {'--from='+src_stage+' ' if src_stage else ''}{s} -> {dest}")
        elif op == "RUN":
            cmd = rest.strip()
            cwd = sroot + workdir
            if cmd.startswith(("npm ci", "npm install", "npm run")):
                run(cmd, cwd, env)
            elif cmd.startswith("pip install"):
                run(cmd.replace("pip install", f"{venv_bin}/pip install -q", 1), cwd, env)
            elif cmd.startswith("pytest"):
                e = dict(env, SQLITE_DB_LOCATION=os.path.join(sroot, "etc/todos/todo.db"))
                run(f"{venv_bin}/pytest -q -p no:cacheprovider", cwd, e)
            else:
                print(f"  · RUN (시스템 패키지/사용자 생성 — 건너뜀): {cmd[:70]}")
        else:
            print(f"  · {op} {rest[:70]}")
    fs[stage] = sroot
    info["workdir"], info["env"] = workdir, env
    return sroot


def run(cmd, cwd, env):
    print(f"  ▶ RUN {cmd}")
    r = subprocess.run(cmd, shell=True, cwd=cwd, env={**os.environ, **env},
                       capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()[-3:]
    for t in tail:
        print("     │ " + t[:150])
    if r.returncode != 0:
        errors.append(f"RUN 실패({r.returncode}): {cmd}")


try:
    final_root = build(target)
except Exception as ex:          # noqa: BLE001
    errors.append(f"예외: {ex}")
    final_root = None

if final_root and not errors and target == "final":
    wd = final_root + stages[target]["workdir"]
    db = os.path.join(final_root, "data/todo.db")
    p = subprocess.Popen([f"{venv_bin}/uvicorn", "src.main:app", "--port", "3999"], cwd=wd,
                         env={**os.environ, "SQLITE_DB_LOCATION": db},
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ok = False
    for _ in range(30):
        try:
            body = urllib.request.urlopen("http://127.0.0.1:3999/api/greeting", timeout=1).read().decode()
            idx = urllib.request.urlopen("http://127.0.0.1:3999/", timeout=1).read().decode()
            print(f"\n  ✓ smoke: GET /api/greeting -> {body}")
            print(f"  ✓ smoke: GET / -> index.html ({len(idx)} bytes, React SPA 포함={'<div id=\"root\">' in idx})")
            ok = True
            break
        except Exception:        # noqa: BLE001
            time.sleep(0.5)
    p.terminate()
    if not ok:
        errors.append("smoke test 실패")

print("\n" + ("RESULT: FAIL\n  - " + "\n  - ".join(errors) if errors else f"RESULT: PASS (target={target})"))
sys.exit(1 if errors else 0)
