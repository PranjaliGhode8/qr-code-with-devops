from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import qrcode
import boto3
import os
import re

from io import BytesIO

# Load environment variables
load_dotenv()

app = FastAPI()

# Home Route
@app.get("/")
def home():
    return {"message": "API is working"}

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS Configuration
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

BUCKET_NAME = "qrcode-storage-devopes-capstone"

# S3 Client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
)

@app.post("/generate-qr/")
async def generate_qr(url: str):

    try:

        # Validate URL
        if not url.strip():
            raise HTTPException(
                status_code=400,
                detail="URL cannot be empty"
            )

        # Generate QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(
            fill_color="black",
            back_color="white"
        )

        # Save image into memory
        img_byte_arr = BytesIO()
        img.save(img_byte_arr)
        img_byte_arr.seek(0)

        # Create safe filename
        safe_name = re.sub(
            r"[^a-zA-Z0-9]",
            "_",
            url
        )

        file_name = f"qr_codes/{safe_name}.png"

        # Upload to S3
        s3.upload_fileobj(
            img_byte_arr,
            BUCKET_NAME,
            file_name,
            ExtraArgs={
                "ContentType": "image/png"
            }
        )

        # Generate URL
        s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{file_name}"

        print("QR Code Uploaded:", s3_url)

        return {
            "success": True,
            "message": "QR Code generated successfully",
            "qr_code_url": s3_url
        }

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        print("ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate QR code: {str(e)}"
        )