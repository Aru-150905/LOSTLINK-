-- Vector similarity search RPC for pgvector

CREATE OR REPLACE FUNCTION public.match_items_by_embedding(
    query_embedding vector,
    embedding_column text,
    match_type text,
    match_count int DEFAULT 50
)
RETURNS TABLE (
    id uuid,
    user_id uuid,
    type text,
    title text,
    description text,
    location text,
    item_timestamp timestamptz,
    image_url text,
    category text,
    status text,
    created_at timestamptz,
    updated_at timestamptz,
    image_embedding vector(512),
    text_embedding vector(384),
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    IF embedding_column = 'image_embedding' THEN
        RETURN QUERY
        SELECT
            i.id,
            i.user_id,
            i.type,
            i.title,
            i.description,
            i.location,
            i.item_timestamp,
            i.image_url,
            i.category,
            i.status,
            i.created_at,
            i.updated_at,
            e.image_embedding,
            e.text_embedding,
            1 - (e.image_embedding <=> query_embedding) AS similarity
        FROM public.items i
        JOIN public.embeddings e ON e.item_id = i.id
        WHERE i.type = match_type
          AND i.status = 'active'
          AND e.image_embedding IS NOT NULL
        ORDER BY e.image_embedding <=> query_embedding
        LIMIT match_count;

    ELSIF embedding_column = 'text_embedding' THEN
        RETURN QUERY
        SELECT
            i.id,
            i.user_id,
            i.type,
            i.title,
            i.description,
            i.location,
            i.item_timestamp,
            i.image_url,
            i.category,
            i.status,
            i.created_at,
            i.updated_at,
            e.image_embedding,
            e.text_embedding,
            1 - (e.text_embedding <=> query_embedding) AS similarity
        FROM public.items i
        JOIN public.embeddings e ON e.item_id = i.id
        WHERE i.type = match_type
          AND i.status = 'active'
          AND e.text_embedding IS NOT NULL
        ORDER BY e.text_embedding <=> query_embedding
        LIMIT match_count;

    ELSE
        RAISE EXCEPTION 'Invalid embedding column: %', embedding_column;
    END IF;
END;
$$;
