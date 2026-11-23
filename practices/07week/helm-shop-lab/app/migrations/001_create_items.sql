CREATE TABLE IF NOT EXISTS items (
    id         SERIAL PRIMARY KEY,
    name       TEXT    NOT NULL,
    price      INTEGER NOT NULL CHECK (price >= 0),
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO items (name, price) VALUES ('kubernetes-mug', 12000), ('helm-sticker', 3000);
