CREATE TABLE payments (
    id                  BIGSERIAL PRIMARY KEY,
    booking_id          BIGINT NOT NULL REFERENCES bookings(id),

    wallet_name        VARCHAR(20),
    wallet_phone        VARCHAR(20),
    transaction_id      VARCHAR(100) UNIQUE,

    amount              DECIMAL(10,2),
    status              VARCHAR(20),  -- INITIATED, SUCCESS, FAILED

    idempotency_key     VARCHAR(100),

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE (idempotency_key)
);
CREATE TABLE refunds (
    id              BIGSERIAL PRIMARY KEY,
    payment_id      BIGINT NOT NULL REFERENCES payments(id),

    amount          DECIMAL(10,2),
    status          VARCHAR(20),  -- INITIATED, SUCCESS, FAILED

    created_at      TIMESTAMP DEFAULT NOW()
);