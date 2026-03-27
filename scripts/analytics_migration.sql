-- Analytics migration v2.2
-- Run once in Supabase SQL editor: https://app.supabase.com → SQL Editor

-- 1. Add platform_post_id to posts table
--    Stores Telegram message_id (text) or LinkedIn post URN after publishing
ALTER TABLE posts ADD COLUMN IF NOT EXISTS platform_post_id TEXT;

-- 2. Create analytics table
CREATE TABLE IF NOT EXISTS analytics (
    id          UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    post_id     UUID REFERENCES posts(id) ON DELETE CASCADE,
    platform    TEXT NOT NULL,
    views       INTEGER DEFAULT 0,
    likes       INTEGER DEFAULT 0,
    comments    INTEGER DEFAULT 0,
    shares      INTEGER DEFAULT 0,
    subscribers INTEGER DEFAULT 0,  -- channel subscriber count (Telegram)
    post_content TEXT,               -- first 200 chars of post text for display
    fetched_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Unique constraint so scheduler can upsert (one row per post)
ALTER TABLE analytics DROP CONSTRAINT IF EXISTS analytics_post_id_key;
ALTER TABLE analytics ADD CONSTRAINT analytics_post_id_key UNIQUE (post_id);

-- 4. Indexes
CREATE INDEX IF NOT EXISTS analytics_platform_idx ON analytics (platform);
CREATE INDEX IF NOT EXISTS analytics_updated_at_idx ON analytics (updated_at DESC);

-- 5. RLS — allow service role to upsert, allow authenticated users to read
ALTER TABLE analytics ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "analytics_read" ON analytics;
CREATE POLICY "analytics_read" ON analytics
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "analytics_write" ON analytics;
CREATE POLICY "analytics_write" ON analytics
    FOR ALL USING (auth.role() = 'service_role');
