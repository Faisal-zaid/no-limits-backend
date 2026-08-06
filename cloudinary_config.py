import os
from dotenv import load_dotenv
import cloudinary

load_dotenv(override=True)

print("Cloud name:", os.getenv("CLOUDINARY_CLOUD_NAME"))
print("API key:", os.getenv("CLOUDINARY_API_KEY"))
print("Secret:", os.getenv("CLOUDINARY_API_SECRET"))

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)