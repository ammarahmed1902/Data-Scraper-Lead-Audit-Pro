#!/usr/bin/env python3
"""
Automated PostgreSQL setup for Lead Audit Pro.

Usage (set your postgres superuser password first):
  set PGPASSWORD=your_postgres_password
  python -m scripts.setup_database

Or:
  set POSTGRES_SUPERUSER_PASSWORD=your_postgres_password
  python -m scripts.setup_database
"""

from __future__ import annotations

import os
import subprocess
import sys

# Allow running from backend directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

APP_USER = os.environ.get("POSTGRES_USER", "leadaudit")
APP_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "leadaudit_secret")
APP_DB = os.environ.get("POSTGRES_DB", "lead_audit_pro")
PG_HOST = os.environ.get("POSTGRES_HOST", "localhost")
PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
SUPERUSER = os.environ.get("POSTGRES_SUPERUSER", "postgres")
SUPER_PASSWORD = os.environ.get("POSTGRES_SUPERUSER_PASSWORD") or os.environ.get("PGPASSWORD")


def _connect(dbname: str = "postgres"):
    import psycopg

    return psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=dbname,
        user=SUPERUSER,
        password=SUPER_PASSWORD,
        autocommit=True,
    )


def setup_role_and_database() -> None:
    if not SUPER_PASSWORD:
        print(
            "ERROR: Set the postgres superuser password first:\n"
            "  PowerShell: $env:PGPASSWORD = 'your_postgres_password'\n"
            "  Then run:   python -m scripts.setup_database"
        )
        sys.exit(1)

    from psycopg import sql

    print(f"Connecting as {SUPERUSER}@{PG_HOST}:{PG_PORT}...")

    with _connect("postgres") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (APP_USER,))
            if cur.fetchone() is None:
                cur.execute(
                    sql.SQL("CREATE ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(APP_USER),
                        sql.Literal(APP_PASSWORD),
                    )
                )
                print(f"Created role: {APP_USER}")
            else:
                cur.execute(
                    sql.SQL("ALTER ROLE {} WITH LOGIN PASSWORD {}").format(
                        sql.Identifier(APP_USER),
                        sql.Literal(APP_PASSWORD),
                    )
                )
                print(f"Updated password for role: {APP_USER}")

            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (APP_DB,))
            if cur.fetchone() is None:
                cur.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(APP_DB),
                        sql.Identifier(APP_USER),
                    )
                )
                print(f"Created database: {APP_DB}")
            else:
                print(f"Database already exists: {APP_DB}")

            cur.execute(
                sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                    sql.Identifier(APP_DB),
                    sql.Identifier(APP_USER),
                )
            )

    with _connect(APP_DB) as conn:
        with conn.cursor() as cur:
            for ext in ("uuid-ossp", "pg_trgm", "citext"):
                cur.execute(sql.SQL("CREATE EXTENSION IF NOT EXISTS {}").format(sql.Identifier(ext)))
                print(f"Extension ready: {ext}")
            cur.execute(
                sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(APP_USER))
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}"
                ).format(sql.Identifier(APP_USER))
            )
            cur.execute(
                sql.SQL(
                    "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {}"
                ).format(sql.Identifier(APP_USER))
            )

    print("PostgreSQL setup complete.")


def verify_app_connection() -> None:
    import psycopg

    conn = psycopg.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=APP_DB,
        user=APP_USER,
        password=APP_PASSWORD,
    )
    conn.close()
    print(f"Verified connection as {APP_USER} -> {APP_DB}")


def run_migrations() -> None:
    print("Running Alembic migrations...")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        print("Alembic migration failed.")
        sys.exit(result.returncode)
    print("Migrations complete.")


def seed_admin() -> None:
    print("Seeding admin user...")
    result = subprocess.run(
        [sys.executable, "-m", "scripts.seed_admin"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if result.returncode != 0:
        print("Seed failed.")
        sys.exit(result.returncode)


def main() -> None:
    setup_role_and_database()
    verify_app_connection()
    run_migrations()
    seed_admin()
    print("\nDone! Login with:")
    print("  Email:    admin@leadaudit.pro")
    print("  Password: Admin123!ChangeMe")
    print("  URL:      http://localhost:3002/auth/login")


if __name__ == "__main__":
    main()
