import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from models import Category, Product, Session, User, engine, Base

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def create_admin(db):
    if not ADMIN_USERNAME or not ADMIN_EMAIL or not ADMIN_PASSWORD:
        print("Skipping admin creation: ADMIN_USERNAME, ADMIN_EMAIL, or ADMIN_PASSWORD not set in environment.")
        return

    existing_user = (
        db.query(User)
        .filter(User.username == ADMIN_USERNAME)
        .first()
    )

    if existing_user:
        if existing_user.role == "admin":
            print("Admin already exists.")
            return

        existing_user.role = "admin"
        db.commit()
        print(f"User '{ADMIN_USERNAME}' has been promoted to admin.")
        return

    hashed_password = pwd_context.hash(ADMIN_PASSWORD)

    admin = User(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        hashed_password=hashed_password,
        role="admin"
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    print(f"Admin '{admin.username}' created successfully.")


def seed_categories_and_products(db):
    initial_data = [
        {
            "name": "Custom Apparel",
            "subheading": "Branded Clothing & Workwear",
            "description": "High-quality custom printed and embroidered clothing for teams, brands, and events.",
            "products": [
                {
                    "name": "Custom Branded Crewneck Hoodie",
                    "description": "Premium heavy-cotton hoodie with screen-printed or embroidered logo options.",
                    "base_price": 3500,
                    "stock": 50,
                    "reserved_stock": 0,
                },
                {
                    "name": "Corporate Polo T-Shirt",
                    "description": "Breathable cotton-blend polo shirt ideal for staff uniforms and event branding.",
                    "base_price": 1800,
                    "stock": 100,
                    "reserved_stock": 0,
                },
            ],
        },
        {
            "name": "Corporate Merchandise",
            "subheading": "Promotional Items & Swag",
            "description": "Everyday branded gifts and office accessories customized with your corporate identity.",
            "products": [
                {
                    "name": "Insulated Stainless Steel Water Bottle",
                    "description": "500ml double-wall vacuum flask with laser-engraved or UV-printed logo.",
                    "base_price": 2200,
                    "stock": 75,
                    "reserved_stock": 0,
                },
                {
                    "name": "Custom Hardcover Executive Notebook",
                    "description": "A5 faux-leather notebook with foil-stamped or embossed company branding.",
                    "base_price": 1200,
                    "stock": 120,
                    "reserved_stock": 0,
                },
            ],
        },
        {
            "name": "Signage & Displays",
            "subheading": "Event & Retail Branding",
            "description": "Large format prints and banners for exhibitions, retail spaces, and corporate events.",
            "products": [
                {
                    "name": "Pull-Up Roll-Up Banner",
                    "description": "Standard 85x200cm retractable display banner with high-resolution full-color print.",
                    "base_price": 6500,
                    "stock": 30,
                    "reserved_stock": 0,
                },
                {
                    "name": "Custom Outdoor Tear-Drop Feather Flag",
                    "description": "Weather-resistant promotional flag with double-sided custom graphic printing.",
                    "base_price": 8000,
                    "stock": 20,
                    "reserved_stock": 0,
                },
            ],
        },
    ]

    for cat_data in initial_data:
        category = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not category:
            category = Category(
                name=cat_data["name"],
                subheading=cat_data["subheading"],
                description=cat_data["description"],
                image=None
            )
            db.add(category)
            db.flush()
            print(f"Category '{category.name}' created.")
        else:
            print(f"Category '{category.name}' already exists.")

        for prod_data in cat_data["products"]:
            existing_product = (
                db.query(Product)
                .filter(Product.name == prod_data["name"], Product.category_id == category.id)
                .first()
            )
            if not existing_product:
                product = Product(
                    category_id=category.id,
                    name=prod_data["name"],
                    description=prod_data["description"],
                    base_price=prod_data["base_price"],
                    stock=prod_data["stock"],
                    reserved_stock=prod_data["reserved_stock"],
                    image=None
                )
                db.add(product)
                print(f"  └─ Product '{product.name}' created under '{category.name}'.")
            else:
                print(f"  └─ Product '{prod_data['name']}' already exists.")

    db.commit()


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        print("Starting database seeding...")
        create_admin(db)
        seed_categories_and_products(db)
        print("Database seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()