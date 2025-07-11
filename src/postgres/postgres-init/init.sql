CREATE DATABASE carts;
\c carts;
CREATE TABLE cart_items (
  userId text,
  productId text,
  quantity int,
  PRIMARY KEY(userId, productId)
);
CREATE INDEX cartItemsByUserId ON cart_items(userId);

CREATE DATABASE products;
\c products;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE catalog_items (
  id TEXT PRIMARY KEY,
  name TEXT,
  description TEXT,
  picture TEXT,
  price_usd_currency_code TEXT,
  price_usd_units INTEGER,
  price_usd_nanos BIGINT,
  categories TEXT,
  product_embedding VECTOR(384),
  embed_model TEXT
);
