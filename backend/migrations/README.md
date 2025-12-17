# Database Migrations

This directory contains SQL migration files for setting up the Supabase database schema.

## Running Migrations

### Option 1: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of the migration file
4. Click **Run** to execute

### Option 2: Using Supabase CLI

If you have the Supabase CLI installed:

```bash
supabase db push
```

### Option 3: Using psql

```bash
psql -h db.nhiweevbieqnjnoowmcj.supabase.co -U postgres -d postgres -f migrations/001_create_profiles_table.sql
```

## Migration Files

- `001_create_profiles_table.sql` - Creates profiles table, orgs table, and related indexes/triggers

## Order of Execution

Migrations should be run in numerical order (001, 002, etc.) to ensure dependencies are created correctly.


