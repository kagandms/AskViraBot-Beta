-- =============================================
-- VIRA BOT - DATABASE SCHEMA (FIXED & ROBUST)
-- Supabase (PostgreSQL) için temiz ve kapsamlı şema
-- Bu script, mevcut tabloları koruyarak eksik sütunları ekler.
-- =============================================

-- =============================================
-- 1. USERS - Kullanıcı bilgileri
-- =============================================
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    lang TEXT DEFAULT 'tr',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Eksik sütunları güvenli şekilde ekle (Migration)
ALTER TABLE users ADD COLUMN IF NOT EXISTS state TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS state_data JSONB;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_model TEXT DEFAULT 'deepseek';

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- =============================================
-- 2. NOTES - Kullanıcı notları
-- =============================================
CREATE TABLE IF NOT EXISTS notes (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notes_user_id ON notes(user_id);

-- =============================================
-- 3. REMINDERS - Hatırlatıcılar
-- =============================================
CREATE TABLE IF NOT EXISTS reminders (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    reminder_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Eksik sütunları ekle (Hata kaynağı burasıydı)
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS reminder_time TIMESTAMPTZ;
ALTER TABLE reminders ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT FALSE;

-- Sütun eklendikten sonra index oluştur
CREATE INDEX IF NOT EXISTS idx_reminders_user_id ON reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_reminders_time ON reminders(reminder_time);

-- =============================================
-- 4. AI USAGE - AI kullanım istatistikleri
-- =============================================
CREATE TABLE IF NOT EXISTS ai_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    usage_date DATE NOT NULL DEFAULT CURRENT_DATE,
    message_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    UNIQUE(user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_user_date ON ai_usage(user_id, usage_date);

-- =============================================
-- 5. GAME SCORES - Web oyun skorları (Yeni!)
-- Tüm web oyunları için merkezi skor tablosu
-- =============================================
CREATE TABLE IF NOT EXISTS game_scores (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    game_type TEXT NOT NULL,                    -- snake, 2048, flappy, runner, sudoku, xox
    score INTEGER NOT NULL DEFAULT 0,
    difficulty TEXT,                            -- easy, medium, hard (varsa)
    duration_seconds INTEGER,                   -- Oyun süresi (varsa)
    metadata JSONB,                             -- Ekstra veri (level, moves vs.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_game_scores_user ON game_scores(user_id);
CREATE INDEX IF NOT EXISTS idx_game_scores_type ON game_scores(game_type);
CREATE INDEX IF NOT EXISTS idx_game_scores_score ON game_scores(score DESC);

-- =============================================
-- 6. GAME HIGHSCORES - En yüksek skorlar (View)
-- =============================================
CREATE OR REPLACE VIEW game_highscores AS
SELECT 
    user_id,
    game_type,
    MAX(score) as high_score,
    COUNT(*) as total_games,
    AVG(score)::INTEGER as avg_score
FROM game_scores
GROUP BY user_id, game_type;

-- =============================================
-- 7. LOG TABLES - Oyun kayıtları
-- =============================================
-- XOX
CREATE TABLE IF NOT EXISTS xox_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    winner TEXT NOT NULL,
    difficulty TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_xox_logs_user ON xox_logs(user_id);

-- TKM
CREATE TABLE IF NOT EXISTS tkm_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    user_move TEXT NOT NULL,
    bot_move TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tkm_logs_user ON tkm_logs(user_id);

-- Dice
CREATE TABLE IF NOT EXISTS dice_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_dice_logs_user ON dice_logs(user_id);

-- Coinflip
CREATE TABLE IF NOT EXISTS coinflip_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    result TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_coinflip_logs_user ON coinflip_logs(user_id);

-- Tool Usage
CREATE TABLE IF NOT EXISTS tool_usage (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    action TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tool_usage_user ON tool_usage(user_id);

-- Metro Favorites
CREATE TABLE IF NOT EXISTS metro_favorites (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    line_id TEXT NOT NULL,
    station_name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, line_id)
);
CREATE INDEX IF NOT EXISTS idx_metro_favorites_user ON metro_favorites(user_id);

-- =============================================
-- 8. HELPER FUNCTIONS
-- =============================================

-- Oyun skoru kaydetme fonksiyonu
CREATE OR REPLACE FUNCTION save_game_score(
    p_user_id TEXT,
    p_game_type TEXT,
    p_score INTEGER,
    p_difficulty TEXT DEFAULT NULL,
    p_duration INTEGER DEFAULT NULL,
    p_metadata JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
    INSERT INTO game_scores (user_id, game_type, score, difficulty, duration_seconds, metadata)
    VALUES (p_user_id, p_game_type, p_score, p_difficulty, p_duration, p_metadata);
END;
$$ LANGUAGE plpgsql;

-- En yüksek skoru getirme fonksiyonu
CREATE OR REPLACE FUNCTION get_high_score(
    p_user_id TEXT,
    p_game_type TEXT
) RETURNS INTEGER AS $$
DECLARE
    high_score INTEGER;
BEGIN
    SELECT MAX(score) INTO high_score
    FROM game_scores
    WHERE user_id = p_user_id AND game_type = p_game_type;
    
    RETURN COALESCE(high_score, 0);
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- 9. TRIGGERS
-- =============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_notes_updated_at ON notes;
CREATE TRIGGER update_notes_updated_at
    BEFORE UPDATE ON notes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
