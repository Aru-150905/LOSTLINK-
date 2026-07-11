-- LostLink initial schema with pgvector support

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Lost and found items
CREATE TABLE IF NOT EXISTS public.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('lost', 'found')),
    title TEXT NOT NULL,
    description TEXT,
    location TEXT NOT NULL,
    item_timestamp TIMESTAMPTZ NOT NULL,
    image_url TEXT,
    category TEXT,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'matched', 'claimed', 'returned', 'resolved')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Vector embeddings for semantic search
CREATE TABLE IF NOT EXISTS public.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL UNIQUE REFERENCES public.items(id) ON DELETE CASCADE,
    image_embedding vector(512),
    text_embedding vector(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Stored match results
CREATE TABLE IF NOT EXISTS public.matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES public.items(id) ON DELETE CASCADE,
    matched_item_id UUID NOT NULL REFERENCES public.items(id) ON DELETE CASCADE,
    confidence_score DOUBLE PRECISION NOT NULL,
    image_score DOUBLE PRECISION DEFAULT 0,
    text_score DOUBLE PRECISION DEFAULT 0,
    metadata_score DOUBLE PRECISION DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (item_id, matched_item_id)
);

-- Claim requests
CREATE TABLE IF NOT EXISTS public.claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES public.items(id) ON DELETE CASCADE,
    claimer_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    message TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'rejected')),
    admin_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- User notifications
CREATE TABLE IF NOT EXISTS public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('match', 'claim', 'status', 'admin')),
    read BOOLEAN NOT NULL DEFAULT FALSE,
    related_item_id UUID REFERENCES public.items(id) ON DELETE SET NULL,
    related_match_id UUID REFERENCES public.matches(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_items_user_id ON public.items(user_id);
CREATE INDEX IF NOT EXISTS idx_items_type ON public.items(type);
CREATE INDEX IF NOT EXISTS idx_items_status ON public.items(status);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON public.items(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_matches_item_id ON public.matches(item_id);
CREATE INDEX IF NOT EXISTS idx_matches_matched_item_id ON public.matches(matched_item_id);
CREATE INDEX IF NOT EXISTS idx_claims_item_id ON public.claims(item_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON public.claims(status);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(read);

-- pgvector indexes for similarity search
CREATE INDEX IF NOT EXISTS idx_embeddings_image
    ON public.embeddings USING ivfflat (image_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_embeddings_text
    ON public.embeddings USING ivfflat (text_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER items_updated_at
    BEFORE UPDATE ON public.items
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

CREATE TRIGGER claims_updated_at
    BEFORE UPDATE ON public.claims
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- Auto-create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, name, email, phone)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'name', split_part(NEW.email, '@', 1)),
        NEW.email,
        NEW.raw_user_meta_data->>'phone'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- Users policies
CREATE POLICY "Users can view own profile"
    ON public.users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.users FOR UPDATE
    USING (auth.uid() = id);

-- Items policies
CREATE POLICY "Anyone authenticated can view active items"
    ON public.items FOR SELECT
    TO authenticated
    USING (status IN ('active', 'matched', 'claimed'));

CREATE POLICY "Users can insert own items"
    ON public.items FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own items"
    ON public.items FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

-- Embeddings policies
CREATE POLICY "Authenticated users can view embeddings"
    ON public.embeddings FOR SELECT
    TO authenticated
    USING (true);

-- Matches policies
CREATE POLICY "Users can view matches for their items"
    ON public.matches FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = matches.item_id AND items.user_id = auth.uid()
        )
        OR EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = matches.matched_item_id AND items.user_id = auth.uid()
        )
    );

-- Claims policies
CREATE POLICY "Users can view own claims"
    ON public.claims FOR SELECT
    TO authenticated
    USING (
        auth.uid() = claimer_id
        OR EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = claims.item_id AND items.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create claims"
    ON public.claims FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = claimer_id);

-- Notifications policies
CREATE POLICY "Users can view own notifications"
    ON public.notifications FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own notifications"
    ON public.notifications FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

-- Storage bucket for item images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'item-images',
    'item-images',
    true,
    5242880,
    ARRAY['image/jpeg', 'image/png', 'image/webp', 'image/gif']
)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Authenticated users can upload item images"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'item-images');

CREATE POLICY "Anyone can view item images"
    ON storage.objects FOR SELECT
    TO public
    USING (bucket_id = 'item-images');

CREATE POLICY "Users can update own item images"
    ON storage.objects FOR UPDATE
    TO authenticated
    USING (bucket_id = 'item-images');

CREATE POLICY "Users can delete own item images"
    ON storage.objects FOR DELETE
    TO authenticated
    USING (bucket_id = 'item-images');
