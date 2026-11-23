#!/usr/bin/env python3
"""Regenerate the local_kind Helm chart and apply the service-type patch.

Why this script exists:
  `katenary convert -c compose-local_kind.yaml ...` fails with
  "no configuration file provided: not found" when run from this repository,
  because katenary always loads a base compose.yaml from the working directory
  and treats `-c` files only as overrides. This repository has no compose.yaml
  (it was replaced by compose-*.yaml variants), so the conversion is done from
  a temporary directory that contains compose.yaml (a copy of the local_kind
  compose file). The chart name comes from that directory's name, so it must be
  "getting-started-todo-app" to match the names in the README.

Usage (from the repository root):
  python scripts/generate-local_kind-chart.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOURCE_COMPOSE = REPO / "compose-local_kind.yaml"
CHART_OUT = REPO / "charts" / "getting-started-todo-app.local_kind"
PROJECT_DIR_NAME = "getting-started-todo-app"


def main() -> int:
    if not SOURCE_COMPOSE.is_file():
        print(f"ERROR: {SOURCE_COMPOSE} not found", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / PROJECT_DIR_NAME
        project.mkdir()
        shutil.copyfile(SOURCE_COMPOSE, project / "compose.yaml")

        cmd = [
            "katenary", "convert",
            "-o", str(CHART_OUT),
            "-a", "1.0.0",
            "-v", "0.1.0",
            "-f",
        ]
        result = subprocess.run(cmd, cwd=project)
        if result.returncode != 0:
            return result.returncode

    patch = REPO / "scripts" / "patch-service-type.py"
    return subprocess.run([sys.executable, str(patch), str(CHART_OUT)], cwd=REPO).returncode


if __name__ == "__main__":
    sys.exit(main())
