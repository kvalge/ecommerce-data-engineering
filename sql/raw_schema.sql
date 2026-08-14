-- Raw layer schema for the e-commerce pipeline.
-- Products: upsert by id (external API catalog).
-- Users / orders / order_items: SCD Type 2 (id = version PK, entity_id = business key).

CREATE SCHEMA IF NOT EXISTS raw;

-- ---------------------------------------------------------------------------
-- products (no versioning; full refresh / upsert from FakeStore API)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.products (
    id              INTEGER PRIMARY KEY,
    title           TEXT NOT NULL,
    price           NUMERIC(12, 2) NOT NULL,
    description     TEXT,
    category        TEXT,
    image           TEXT,
    rating_rate     NUMERIC(3, 2),
    rating_count    INTEGER
);

-- ---------------------------------------------------------------------------
-- users (SCD Type 2)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.users (
    id                  INTEGER PRIMARY KEY,
    entity_id           INTEGER NOT NULL,
    first_name          TEXT NOT NULL,
    last_name           TEXT NOT NULL,
    email               TEXT NOT NULL,
    telephone           TEXT,
    age                 INTEGER,
    gender              TEXT,
    city                TEXT,
    registration_date   DATE,
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_raw_users_entity_id
    ON raw.users (entity_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_users_current_entity
    ON raw.users (entity_id)
    WHERE valid_until IS NULL;

-- ---------------------------------------------------------------------------
-- orders (SCD Type 2); user_id references users.entity_id (logical, not FK)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.orders (
    id                  INTEGER PRIMARY KEY,
    entity_id           INTEGER NOT NULL,
    user_id             INTEGER NOT NULL,
    order_date          DATE NOT NULL,
    status              TEXT NOT NULL,
    payment_method      TEXT NOT NULL,
    shipping_city       TEXT NOT NULL,
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_raw_orders_entity_id
    ON raw.orders (entity_id);

CREATE INDEX IF NOT EXISTS idx_raw_orders_user_id
    ON raw.orders (user_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_orders_current_entity
    ON raw.orders (entity_id)
    WHERE valid_until IS NULL;

-- ---------------------------------------------------------------------------
-- order_items (SCD Type 2); order_id references orders.entity_id (logical)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw.order_items (
    id                  INTEGER PRIMARY KEY,
    entity_id           INTEGER NOT NULL,
    order_id            INTEGER NOT NULL,
    product_id          INTEGER NOT NULL,
    quantity            INTEGER NOT NULL,
    unit_price          NUMERIC(12, 2) NOT NULL,
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_until         TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_entity_id
    ON raw.order_items (entity_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_order_id
    ON raw.order_items (order_id);

CREATE INDEX IF NOT EXISTS idx_raw_order_items_product_id
    ON raw.order_items (product_id);

CREATE UNIQUE INDEX IF NOT EXISTS uq_raw_order_items_current_entity
    ON raw.order_items (entity_id)
    WHERE valid_until IS NULL;
