-- Lead Audit Pro — PostgreSQL Initialization
-- Extensions and baseline configuration

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Enable case-insensitive text search for domain lookups
CREATE EXTENSION IF NOT EXISTS "citext";
