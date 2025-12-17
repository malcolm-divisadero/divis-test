-- Insert Coca Cola brand
INSERT INTO public.brands (name, slug, description, configuration, enrichment_data)
VALUES (
    'Coca Cola',
    'coca-cola',
    'The Coca-Cola Company is an American multinational corporation founded in 1892, best known as the producer of Coca-Cola.',
    '{}'::jsonb,
    '{}'::jsonb
)
ON CONFLICT (slug) DO NOTHING;

