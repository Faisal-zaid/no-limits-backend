import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(database_url)

with engine.begin() as connection:

    # Check whether user_id already exists
    result = connection.execute(text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'user_id'
    """))

    user_id_exists = result.fetchone()

    if not user_id_exists:
        print("Adding user_id column to orders...")

        connection.execute(text("""
            ALTER TABLE orders
            ADD COLUMN user_id INTEGER
        """))

        connection.execute(text("""
            ALTER TABLE orders
            ADD CONSTRAINT fk_orders_user_id
            FOREIGN KEY (user_id)
            REFERENCES users(id)
        """))

        print("user_id added successfully.")

    else:
        print("user_id already exists. Nothing to do.")