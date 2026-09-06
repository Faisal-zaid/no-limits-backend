
import os
import base64
import requests

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel

from models import (
    get_db,
    Order
)

import logging


router = APIRouter()

logger = logging.getLogger(__name__)


# =====================================================
# ENVIRONMENT
# =====================================================

MPESA_CONSUMER_KEY = os.getenv(
    "MPESA_CONSUMER_KEY"
)

MPESA_CONSUMER_SECRET = os.getenv(
    "MPESA_CONSUMER_SECRET"
)

MPESA_SHORTCODE = os.getenv(
    "MPESA_SHORTCODE"
)

MPESA_PASSKEY = os.getenv(
    "MPESA_PASSKEY"
)

MPESA_CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL"
)

MPESA_ENVIRONMENT = os.getenv(
    "MPESA_ENVIRONMENT",
    "sandbox"
)


# =====================================================
# BASE URL
# =====================================================

if MPESA_ENVIRONMENT == "production":

    MPESA_BASE_URL = (
        "https://api.safaricom.co.ke"
    )

else:

    MPESA_BASE_URL = (
        "https://sandbox.safaricom.co.ke"
    )


# =====================================================
# REQUEST SCHEMA
# =====================================================

class STKPushRequest(BaseModel):

    order_id: int

    phone_number: str


# =====================================================
# NORMALIZE PHONE NUMBER
# =====================================================

def normalize_phone_number(
    phone_number: str
):

    phone = phone_number.strip()

    # 0712345678
    if phone.startswith("0"):

        phone = (
            "254"
            + phone[1:]
        )

    # +254712345678
    elif phone.startswith("+254"):

        phone = phone[1:]

    # 254712345678
    elif phone.startswith("254"):

        pass

    else:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid Kenyan phone number."
            )
        )

    if (
        len(phone) != 12
        or not phone.isdigit()
        or not phone.startswith("254")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid Kenyan phone number."
            )
        )

    return phone


# =====================================================
# GET ACCESS TOKEN
# =====================================================

def get_mpesa_access_token():

    if not MPESA_CONSUMER_KEY:
        raise Exception(
            "MPESA_CONSUMER_KEY is not configured."
        )

    if not MPESA_CONSUMER_SECRET:
        raise Exception(
            "MPESA_CONSUMER_SECRET is not configured."
        )

    credentials = (
        f"{MPESA_CONSUMER_KEY}:"
        f"{MPESA_CONSUMER_SECRET}"
    )

    encoded_credentials = (
        base64.b64encode(
            credentials.encode()
        ).decode()
    )

    response = requests.get(

        f"{MPESA_BASE_URL}"
        "/oauth/v1/generate"
        "?grant_type=client_credentials",

        headers={
            "Authorization":
                f"Basic {encoded_credentials}"
        },

        timeout=30
    )

    if not response.ok:

        logger.error(
            "M-Pesa token request failed: %s",
            response.text
        )

        raise Exception(
            "Could not authenticate with M-Pesa."
        )

    data = response.json()

    access_token = data.get(
        "access_token"
    )

    if not access_token:

        raise Exception(
            "M-Pesa access token was not returned."
        )

    return access_token


# =====================================================
# GENERATE STK PASSWORD
# =====================================================

def generate_password():

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    raw_password = (
        f"{MPESA_SHORTCODE}"
        f"{MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        raw_password.encode()
    ).decode()

    return password, timestamp


# =====================================================
# STK PUSH
# =====================================================

@router.post("/mpesa/stkpush")
def initiate_stk_push(
    data: STKPushRequest,
    session=Depends(get_db)
):

    # =================================================
    # FIND ORDER
    # =================================================

    order = (
        session.query(Order)
        .filter(
            Order.id == data.order_id
        )
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    # =================================================
    # CHECK PAYMENT STATUS
    # =================================================

    if order.payment_status == "Paid":

        raise HTTPException(
            status_code=400,
            detail="This order has already been paid."
        )

    # =================================================
    # CHECK AMOUNT
    # =================================================

    if not order.total_price:

        raise HTTPException(
            status_code=400,
            detail="Order has no valid total."
        )

    if order.total_price <= 0:

        raise HTTPException(
            status_code=400,
            detail="Order amount must be greater than zero."
        )

    # =================================================
    # NORMALIZE PHONE
    # =================================================

    phone_number = normalize_phone_number(
        data.phone_number
    )

    # =================================================
    # GET ACCESS TOKEN
    # =================================================

    try:

        access_token = (
            get_mpesa_access_token()
        )

    except Exception as error:

        logger.error(
            "M-Pesa authentication error: %s",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not connect to M-Pesa."
            )
        )

    # =================================================
    # GENERATE PASSWORD
    # =================================================

    password, timestamp = (
        generate_password()
    )

    # =================================================
    # STK PUSH PAYLOAD
    # =================================================

    payload = {

        "BusinessShortCode":
            MPESA_SHORTCODE,

        "Password":
            password,

        "Timestamp":
            timestamp,

        "TransactionType":
            "CustomerPayBillOnline",

        "Amount":
            int(order.total_price),

        "PartyA":
            phone_number,

        "PartyB":
            MPESA_SHORTCODE,

        "PhoneNumber":
            phone_number,

        "CallBackURL":
            MPESA_CALLBACK_URL,

        "AccountReference":
            f"ORDER-{order.id}",

        "TransactionDesc":
            f"Payment for order {order.id}"
    }

    # =================================================
    # SEND STK PUSH
    # =================================================

    try:

        response = requests.post(

            f"{MPESA_BASE_URL}"
            "/mpesa/stkpush/v1/processrequest",

            json=payload,

            headers={
                "Authorization":
                    f"Bearer {access_token}",

                "Content-Type":
                    "application/json"
            },

            timeout=30
        )

    except requests.RequestException as error:

        logger.error(
            "M-Pesa STK request error: %s",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not connect to M-Pesa."
            )
        )

    # =================================================
    # PARSE RESPONSE
    # =================================================

    try:

        response_data = (
            response.json()
        )

    except Exception:

        logger.error(
            "Invalid M-Pesa response: %s",
            response.text
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Invalid response from M-Pesa."
            )
        )

    # =================================================
    # CHECK RESPONSE
    # =================================================

    if not response.ok:

        logger.error(
            "M-Pesa STK failed: %s",
            response_data
        )

        raise HTTPException(
            status_code=400,
            detail=(
                response_data.get(
                    "errorMessage",
                    "M-Pesa payment request failed."
                )
            )
        )

    # =================================================
    # SAVE REQUEST IDS
    # =================================================

    order.checkout_request_id = (
        response_data.get(
            "CheckoutRequestID"
        )
    )

    order.merchant_request_id = (
        response_data.get(
            "MerchantRequestID"
        )
    )

    order.payment_status = "Pending"

    session.commit()

    # =================================================
    # RETURN RESPONSE
    # =================================================

    return {

        "message":
            response_data.get(
                "CustomerMessage",
                "STK Push sent successfully."
            ),

        "merchant_request_id":
            response_data.get(
                "MerchantRequestID"
            ),

        "checkout_request_id":
            response_data.get(
                "CheckoutRequestID"
            ),

        "response_code":
            response_data.get(
                "ResponseCode"
            )
    }



@router.get("/mpesa/payment-status/{order_id}")
def get_payment_status(
    order_id: int,
    session=Depends(get_db)
):
    order = (
        session.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    return {
        "order_id": order.id,
        "payment_status": order.payment_status,
        "order_status": order.status,
        "mpesa_receipt_number": order.mpesa_receipt_number
    }


