# Supabase Setup Guide

This guide will help you set up Supabase for the Divisadero project.

## Prerequisites

1. A Supabase account (sign up at https://supabase.com)
2. A Supabase project created

## Step 1: Get Your Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to **Settings** → **API**
3. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`) - Keep this secret!

## Step 2: Configure Backend

1. Create a `.env` file in the `backend/` directory:

```bash
cd backend
cp .env.example .env  # If .env.example exists, or create manually
```

2. Add your Supabase credentials to `backend/.env`:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Optional: Email sending via Resend API (if Supabase SMTP is not configured)
# RESEND_API_KEY=re_your_resend_api_key_here
# RESEND_FROM_EMAIL=noreply@yourdomain.com
# RESEND_FROM_NAME=Divisadero
```

## Step 3: Configure Frontend

1. Create a `.env` file in the `frontend/` directory:

```bash
cd frontend
cp .env.example .env  # If .env.example exists, or create manually
```

2. Add your Supabase credentials to `frontend/.env`:

```env
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
```

**Important:** Only use the anon key in the frontend. Never expose the service_role key in client-side code.

## Step 4: Create Database Tables

Based on the product requirements, you'll need to create the following tables in Supabase:

### Organizations Table (`orgs`)

```sql
CREATE TABLE orgs (
    org_id BIGSERIAL PRIMARY KEY,
    org_slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Users Table (`users`)

```sql
CREATE TABLE users (
    user_id BIGSERIAL PRIMARY KEY,
    is_superuser BOOLEAN DEFAULT FALSE,
    email VARCHAR(255) UNIQUE NOT NULL,
    org_id BIGINT REFERENCES orgs(org_id),
    is_activated BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Analytics Table (`analytics`)

```sql
CREATE TABLE analytics (
    event_id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT NOW(),
    user_id BIGINT REFERENCES users(user_id),
    url VARCHAR(500) NOT NULL
);
```

## Step 5: Set Up Row Level Security (RLS)

Supabase uses Row Level Security to control access to your data. You'll need to create policies based on your authentication requirements.

Example policy for users to read their own organization:

```sql
-- Enable RLS
ALTER TABLE orgs ENABLE ROW LEVEL SECURITY;

-- Policy: Users can read their own organization
CREATE POLICY "Users can read their own org"
    ON orgs FOR SELECT
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE email = auth.jwt() ->> 'email'
        )
    );
```

## Step 6: Test the Connection

### Backend Test

```bash
cd backend
source ../venv/bin/activate
python -c "from database import get_client; client = get_client(); print('Connected!')"
```

Or test via the API:

```bash
curl http://localhost:8000/health/db
```

### Frontend Test

The frontend Supabase client is automatically configured when you set the environment variables. You can test it in your React components:

```javascript
import { supabase } from './lib/supabase'

// Test connection
const testConnection = async () => {
  const { data, error } = await supabase.from('users').select('count')
  console.log('Connection test:', { data, error })
}
```

## Step 7: Configure Email Sending (Optional)

The invite system needs to send emails to invited users. You have two options:

### Option 1: Configure Supabase SMTP (Recommended)

1. Go to your Supabase Dashboard
2. Navigate to **Settings** → **Auth** → **SMTP Settings**
3. Configure your SMTP provider (Gmail, SendGrid, etc.) or use Supabase's built-in email service
4. Supabase will automatically send invite emails when users are invited

### Option 2: Use Resend API (Fallback)

If Supabase SMTP is not configured, the system will attempt to use Resend API as a fallback:

1. Sign up for a Resend account at https://resend.com
2. Get your API key from https://resend.com/api-keys
3. Add to `backend/.env`:
   ```env
   RESEND_API_KEY=re_your_api_key_here
   RESEND_FROM_EMAIL=noreply@yourdomain.com  # Optional
   RESEND_FROM_NAME=Divisadero  # Optional
   ```
4. Restart your backend server

**Note:** If neither option is configured, invite links will still be generated and returned in the API response, but emails won't be sent automatically. You can manually send the invite link to users.

## Next Steps

- Set up authentication flows (login, invite, etc.)
- Configure additional RLS policies
- Create indexes for better query performance
- Set up database migrations (consider using Supabase migrations)

## Security Notes

- **Never commit `.env` files** - They are already in `.gitignore`
- **Never expose service_role key** - Only use it server-side
- **Use anon key in frontend** - It respects RLS policies
- **Review RLS policies** - Ensure they match your security requirements


