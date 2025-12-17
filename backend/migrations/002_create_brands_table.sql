-- Create brands table
CREATE TABLE IF NOT EXISTS public.brands (
    brand_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category_id BIGINT NULL,
    configuration JSONB DEFAULT '{}'::jsonb,
    enrichment_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
) TABLESPACE pg_default;

-- Create index on slug for fast lookups
CREATE INDEX IF NOT EXISTS idx_brands_slug ON public.brands USING btree (slug) TABLESPACE pg_default;

-- Create index on category_id for filtering brands by category
CREATE INDEX IF NOT EXISTS idx_brands_category_id ON public.brands USING btree (category_id) TABLESPACE pg_default;

-- Create index on name for search
CREATE INDEX IF NOT EXISTS idx_brands_name ON public.brands USING btree (name) TABLESPACE pg_default;

-- Create GIN index on enrichment_data for JSONB queries
CREATE INDEX IF NOT EXISTS idx_brands_enrichment_data ON public.brands USING gin (enrichment_data) TABLESPACE pg_default;

-- Create trigger for updating updated_at
DROP TRIGGER IF EXISTS update_brands_updated_at ON public.brands;
CREATE TRIGGER update_brands_updated_at
    BEFORE UPDATE ON public.brands
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE public.brands ENABLE ROW LEVEL SECURITY;

-- Create policies
-- Policy: Authenticated users can read all brands
CREATE POLICY "Authenticated users can read brands"
    ON public.brands FOR SELECT
    USING (auth.role() = 'authenticated');

-- Policy: Superusers can insert brands
CREATE POLICY "Superusers can insert brands"
    ON public.brands FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND is_superuser = TRUE
        )
    );

-- Policy: Superusers can update brands
CREATE POLICY "Superusers can update brands"
    ON public.brands FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND is_superuser = TRUE
        )
    );

-- Policy: Superusers can delete brands
CREATE POLICY "Superusers can delete brands"
    ON public.brands FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE id = auth.uid() AND is_superuser = TRUE
        )
    );

