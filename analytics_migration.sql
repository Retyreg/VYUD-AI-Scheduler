-- Миграция: создание таблицы post_analytics
-- Выполнить в Supabase SQL Editor

CREATE TABLE IF NOT EXISTS post_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('telegram', 'linkedin', 'vk')),
    views INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    raw_response JSONB,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_analytics_post_id ON post_analytics(post_id);
CREATE INDEX IF NOT EXISTS idx_post_analytics_user_id ON post_analytics(user_id);

ALTER TABLE post_analytics ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own analytics" ON post_analytics FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own analytics" ON post_analytics FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete own analytics" ON post_analytics FOR DELETE USING (auth.uid() = user_id);

-- Добавляем поле platform_post_id в posts если нет
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'posts' AND column_name = 'platform_post_id') THEN
        ALTER TABLE posts ADD COLUMN platform_post_id TEXT;
    END IF;
END $$;
