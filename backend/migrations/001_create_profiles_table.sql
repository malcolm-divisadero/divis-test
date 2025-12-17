-- Create update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create orgs table first (if it doesn't exist)
CREATE TABLE IF NOT EXISTS public.orgs (
    org_id BIGSERIAL PRIMARY KEY,
    org_slug VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create profiles table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID NOT NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    org_id BIGINT NULL,
    is_activated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT profiles_pkey PRIMARY KEY (id),
    CONSTRAINT profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users (id) ON DELETE CASCADE,
    CONSTRAINT profiles_org_id_fkey FOREIGN KEY (org_id) REFERENCES orgs (org_id) ON DELETE SET NULL
) TABLESPACE pg_default;

-- Create index on org_id
CREATE INDEX IF NOT EXISTS idx_profiles_org_id ON public.profiles USING btree (org_id) TABLESPACE pg_default;

-- Create trigger for updating updated_at
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orgs ENABLE ROW LEVEL SECURITY;

-- Create policies (basic examples - adjust based on your requirements)
-- Policy: Users can read their own profile
CREATE POLICY "Users can read own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Policy: Superusers can read all profiles
CREATE POLICY "Superusers can read all profiles"
    ON public.profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND is_superuser = TRUE
        )
    );

-- Policy: Users can read their organization
CREATE POLICY "Users can read own org"
    ON public.orgs FOR SELECT
    USING (
        org_id IN (
            SELECT org_id FROM public.profiles
            WHERE id = auth.uid()
        )
    );


