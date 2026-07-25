-- ConnectXperts NMS - Database Initialization Script
-- This script runs automatically when the PostgreSQL container starts for the first time.

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create roles and seed data will be handled by SQLAlchemy migrations
-- This file creates the database if it doesn't exist

-- Note: The actual tables are created by SQLAlchemy via:
--   async with engine.begin() as conn:
--       await conn.run_sync(Base.metadata.create_all)
