import os
from sqlalchemy import create_engine, text

database_url = os.getenv("DATABASE_URL")

if not database_url:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(database_url)

checks = {
    "categories.subheading": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'categories'
        AND column_name = 'subheading'
    """,

    "orders.payment_status": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'payment_status'
    """,

    "orders.checkout_request_id": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'checkout_request_id'
    """,

    "orders.merchant_request_id": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'merchant_request_id'
    """,

    "orders.mpesa_receipt_number": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'mpesa_receipt_number'
    """,

    "products.stock": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'products'
        AND column_name = 'stock'
    """,

    "products.reserved_stock": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'products'
        AND column_name = 'reserved_stock'
    """,

    "orders.user_id": """
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'orders'
        AND column_name = 'user_id'
    """
}

with engine.connect() as connection:

    for name, query in checks.items():
        result = connection.execute(text(query))

        if result.fetchone():
            print(f"{name}: EXISTS")
        else:
            print(f"{name}: MISSING")

with engine.connect() as connection:
    result = connection.execute(
        text("SELECT version_num FROM alembic_version")
    )

    row = result.fetchone()

    if row:
        print(f"Alembic current revision: {row[0]}")
    else:
        print("Alembic version table is empty")            