"""간단한 SQL 마이그레이션 러너 (Helm pre-install/pre-upgrade 훅 Job에서 실행).

migrations/ 폴더의 NNN_*.sql 파일을 번호 순으로 적용하고,
적용 이력은 schema_migrations 테이블에 기록한다. 이미 적용된 파일은 건너뛴다.
실패하면 0이 아닌 종료 코드를 반환 → 훅 Job 실패 → helm upgrade 중단.
"""
import os
import pathlib
import sys
import time

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]
MIGRATIONS_DIR = pathlib.Path(__file__).parent / "migrations"


def wait_for_db(retries: int = 30) -> None:
    for i in range(retries):
        try:
            with psycopg.connect(DATABASE_URL, connect_timeout=2):
                return
        except psycopg.OperationalError:
            print(f"[migrate] DB 대기 중... ({i + 1}/{retries})", flush=True)
            time.sleep(2)
    sys.exit("[migrate] DB에 연결할 수 없습니다.")


def main() -> None:
    wait_for_db()
    with psycopg.connect(DATABASE_URL, autocommit=False) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ DEFAULT now())"
        )
        applied = {r[0] for r in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                print(f"[migrate] skip  {path.name}")
                continue
            print(f"[migrate] apply {path.name}", flush=True)
            conn.execute(path.read_text(encoding="utf-8"))
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
        conn.commit()
    print("[migrate] 완료")


if __name__ == "__main__":
    main()
