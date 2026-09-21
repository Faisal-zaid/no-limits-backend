# reset_db.py
import os
import psycopg2

db_url = os.getenv("DATABASE_URL") or os.getenv("RENDER_POSTGRES_URL")

if db_url:
    # Ensure sslmode is present for Render Postgres connections
    if "sslmode=" not in db_url:
        db_url += "?sslmode=require" if "?" not in db_url else "&sslmode=require"
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO public;")
    conn.commit()
    conn.close()
    print("Database schema reset successfully.")
else:
    print("No database URL variable found.")