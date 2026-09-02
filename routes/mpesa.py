import os
import base64
from datetime import datetime

import httpx
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")

MPESA_BASE_URL = "https://sandbox.safaricom.co.ke"


#get mpesa access token
async def get_mpesa_access_token():

    credentials = (
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
    )

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(
            f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
            headers=headers
        )

    if response.status_code != 200:
        print("MPESA TOKEN ERROR:", response.text)

        raise HTTPException(
            status_code=500,
            detail="Could not authenticate with M-Pesa"
        )

    data = response.json()

    return data["access_token"]

#generate stk password

def generate_password(timestamp: str):

    data_to_encode = (
        f"{MPESA_SHORTCODE}"
        f"{MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        data_to_encode.encode()
    ).decode()

    return password

#generate time stamp

timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

#create stk push endpoint

@router.post("/mpesa/stkpush")
async def stk_push(
    phone_number: str,
    amount: int
):

    access_token = await get_mpesa_access_token()

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    password = generate_password(timestamp)

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": "NoLimits",
        "TransactionDesc": "No Limits Order"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers=headers
        )

    data = response.json()

    print("MPESA STK RESPONSE:", data)

    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to initiate M-Pesa payment"
        )

    return data