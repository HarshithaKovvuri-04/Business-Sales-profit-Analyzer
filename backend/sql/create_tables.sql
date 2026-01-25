-- PostgreSQL table creation script for BizAnalyzer AI
-- Run in psql as a superuser or a role with CREATE privileges

-- ENUM types
DO $$ BEGIN
    CREATE TYPE role_enum AS ENUM ('owner','accountant','staff');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE member_role_enum AS ENUM ('accountant','staff');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE transaction_type_enum AS ENUM ('Income','Expense');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(255) UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role role_enum NOT NULL DEFAULT 'owner',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Businesses
CREATE TABLE IF NOT EXISTS businesses (
  id SERIAL PRIMARY KEY,
  owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  industry VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Business members
CREATE TABLE IF NOT EXISTS business_members (
  id SERIAL PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  role member_role_enum NOT NULL
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
  id SERIAL PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
  type transaction_type_enum NOT NULL,
  amount NUMERIC(12,2),
  category VARCHAR(255),
  invoice_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Inventory
CREATE TABLE IF NOT EXISTS inventory (
  id SERIAL PRIMARY KEY,
  business_id INTEGER REFERENCES businesses(id) ON DELETE CASCADE,
  item_name VARCHAR(255),
  quantity INTEGER,
  cost_price NUMERIC(12,2) NOT NULL DEFAULT 0
);
  -- Add category column to inventory if it doesn't exist (safe ALTER)
  DO $$ BEGIN
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_name='inventory' AND column_name='category'
    ) THEN
      ALTER TABLE inventory ADD COLUMN category VARCHAR(255);
    END IF;
  EXCEPTION
    WHEN others THEN
      RAISE NOTICE 'Could not add inventory.category column automatically - please run migration to add it.';
  END $$;
-- Add created_at column to inventory to match models and other tables.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='inventory' AND column_name='created_at'
  ) THEN
    ALTER TABLE inventory ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;
  END IF;
EXCEPTION
  WHEN others THEN
    -- If this fails (e.g., insufficient privileges), leave a note for manual migration.
    RAISE NOTICE 'Could not add inventory.created_at column automatically - please run migration to add it.';
END $$;
-- NOTE: if this DB already exists, run a migration to ensure `cost_price` column exists (do not delete transactional data).
-- NOTE: If your DB already uses `cost_price` this file will match the current model. If the table still has the old column name, run a migration to add/rename the column as needed; do NOT delete existing transactional data.
-- Migration note: inventory table now includes `created_at` TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP.
-- If you manage DB schema via migrations (Alembic, etc.), prefer creating a migration that adds this column without dropping or renaming existing data.
