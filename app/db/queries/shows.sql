
CREATE TABLE shows (
    id                  BIGSERIAL PRIMARY KEY,
    title               VARCHAR(150), -- bus name (e.g., Ena Poribohon)
    from_location       VARCHAR(100),
    to_location         VARCHAR(100),
    departure_time      TIMESTAMP NOT NULL,
    price               DECIMAL(10,2) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);
CREATE TABLE seats (
    id              BIGSERIAL PRIMARY KEY,
    show_id         BIGINT NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    seat_label      VARCHAR(10) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),

    UNIQUE (show_id, seat_label)
);



