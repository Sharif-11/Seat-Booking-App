-- =========================
-- USERS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id              BIGSERIAL PRIMARY KEY,
    phone_number    VARCHAR(15) UNIQUE NOT NULL,
    is_verified     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- =========================
-- OTP VERIFICATIONS TABLE
-- =========================
CREATE TABLE IF NOT EXISTS otp_verifications (
    id              BIGSERIAL PRIMARY KEY,
    phone_number    VARCHAR(15) UNIQUE NOT NULL,
    otp_code        VARCHAR(6) NOT NULL,
    expires_at      TIMESTAMP NOT NULL,
    verified        BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
    
);

-- =========================
-- INDEXES (IMPORTANT for performance)
-- =========================
-- we need index by phone no in both tables for quick lookups
CREATE INDEX IF NOT EXISTS idx_users_phone_number
ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_otp_phone_number
ON otp_verifications(phone_number);

CREATE INDEX IF NOT EXISTS idx_otp_expires_at
ON otp_verifications(expires_at);

-- =========================
-- OPTIONAL: Foreign relation (if you want strict linking later)
-- NOTE: only enable if you guarantee user exists before OTP insert
-- =========================
-- ALTER TABLE otp_verifications
-- ADD CONSTRAINT fk_user_phone
-- FOREIGN KEY (phone_number)
-- REFERENCES users(phone_number)
-- ON DELETE CASCADE;