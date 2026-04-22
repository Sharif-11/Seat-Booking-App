CREATE TABLE bookings (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL REFERENCES users(id),
    show_id             BIGINT NOT NULL REFERENCES shows(id),

    status              VARCHAR(20) NOT NULL, 
    -- PENDING, CONFIRMED, CANCELLED, EXPIRED

    total_amount        DECIMAL(10,2),

    idempotency_key     VARCHAR(100),
    expires_at          TIMESTAMP,

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE (idempotency_key)
);
CREATE TABLE booking_seats (
    id              BIGSERIAL PRIMARY KEY,
    booking_id      BIGINT NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    seat_id         BIGINT NOT NULL REFERENCES seats(id),

    UNIQUE (seat_id)  -- prevents double booking globally
);