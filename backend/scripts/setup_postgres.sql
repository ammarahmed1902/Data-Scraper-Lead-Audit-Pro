-- Idempotent PostgreSQL setup for Lead Audit Pro
-- Run as superuser: psql -U postgres -f setup_postgres.sql

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'leadaudit') THEN
    CREATE ROLE leadaudit WITH LOGIN PASSWORD 'leadaudit_secret';
  ELSE
    ALTER ROLE leadaudit WITH PASSWORD 'leadaudit_secret';
  END IF;
END
$$;

SELECT 'CREATE DATABASE lead_audit_pro OWNER leadaudit'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'lead_audit_pro')\gexec

GRANT ALL PRIVILEGES ON DATABASE lead_audit_pro TO leadaudit;

\c lead_audit_pro

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "citext";

GRANT ALL ON SCHEMA public TO leadaudit;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO leadaudit;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO leadaudit;
