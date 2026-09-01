import os
from dotenv import load_dotenv
from passlib.context import CryptContext
from models import User, Session

load_dotenv()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# Get admin details from environment variables
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def create_admin():

    # Make sure all required environment variables exist
    if not ADMIN_USERNAME:
        raise ValueError("ADMIN_USERNAME is not set")

    if not ADMIN_EMAIL:
        raise ValueError("ADMIN_EMAIL is not set")

    if not ADMIN_PASSWORD:
        raise ValueError("ADMIN_PASSWORD is not set")

    db = Session()

    try:
        # Check if username already exists
        existing_user = (
            db.query(User)
            .filter(User.username == ADMIN_USERNAME)
            .first()
        )

        if existing_user:

            if existing_user.role == "admin":
                print("Admin already exists.")
                return

            # Promote existing user to admin
            existing_user.role = "admin"
            db.commit()

            print(f"User '{ADMIN_USERNAME}' has been promoted to admin.")
            return

        # Hash the admin password
        hashed_password = pwd_context.hash(ADMIN_PASSWORD)

        # Create admin
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

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()