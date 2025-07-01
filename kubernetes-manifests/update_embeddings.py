import os
import psycopg2
from sentence_transformers import SentenceTransformer
import numpy as np

# Config da env (o default locali)
PGHOST = os.getenv("DB_HOST", "postgres")
PGPORT = os.getenv("DB_PORT", "5432")
PGUSER = os.getenv("DB_USER", "postgres")
PGPASSWORD = os.getenv("DB_PASSWORD", "yourlocalpassword")
PGDB = os.getenv("DB_NAME", "products")

# Connect to PostgreSQL
conn = psycopg2.connect(
    dbname=PGDB,
    user=PGUSER,
    password=PGPASSWORD,
    host=PGHOST,
    port=PGPORT
)

# Embedding model
model_name = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(model_name)

# Cursor
cur = conn.cursor()
cur.execute("SELECT id, description FROM catalog_items")
rows = cur.fetchall()

# Update each row
for pid, desc in rows:
    emb = model.encode(desc).tolist()
    cur.execute(
        "UPDATE catalog_items SET product_embedding = %s, embed_model = %s WHERE id = %s",
        (emb, model_name, pid)
    )

# Commit changes
conn.commit()
cur.close()
conn.close()

print("✅ Embeddings updated.")
