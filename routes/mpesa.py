
import os
import base64
import requests

from datetime import datetime

from rate_limit import strict_limit, moderate_limit, low_limit

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
    logger.info("========== STK PUSH START ==========")
    logger.info("Order ID: %s", data.order_id)
    logger.info("Phone received: %s", data.phone_number)

    # =================================================
    # FIND ORDER
    # =================================================

    order = (
        session.query(Order)
        .filter(Order.id == data.order_id)
        .first()
    )

    if not order:
        logger.error("Order %s not found", data.order_id)

        raise HTTPException(
            status_code=404,
            detail="Order not found."
        )

    logger.info(
        "Order found: id=%s amount=%s payment_status=%s",
        order.id,
        order.total_price,
        order.payment_status
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

    if order.total_price is None:
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

    try:
        phone_number = normalize_phone_number(
            data.phone_number
        )

    except HTTPException:
        raise

    except Exception as error:
        logger.exception(
            "Phone normalization error"
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid phone number."
        )

    logger.info(
        "Normalized phone: %s",
        phone_number
    )

    # =================================================
    # GET ACCESS TOKEN
    # =================================================

    try:
        logger.info("Requesting M-Pesa access token...")

        access_token = get_mpesa_access_token()

        logger.info(
            "M-Pesa access token obtained successfully."
        )

    except Exception as error:
        logger.exception(
            "M-Pesa authentication error"
        )

        raise HTTPException(
            status_code=500,
            detail="Could not connect to M-Pesa."
        )

    # =================================================
    # GENERATE PASSWORD
    # =================================================

    try:
        password, timestamp = generate_password()

    except Exception:
        logger.exception(
            "Could not generate M-Pesa password."
        )

        raise HTTPException(
            status_code=500,
            detail="Could not prepare M-Pesa payment."
        )

    # =================================================
    # VALIDATE REQUIRED ENVIRONMENT VARIABLES
    # =================================================

    missing_variables = []

    if not MPESA_SHORTCODE:
        missing_variables.append("MPESA_SHORTCODE")

    if not MPESA_PASSKEY:
        missing_variables.append("MPESA_PASSKEY")

    if not MPESA_CALLBACK_URL:
        missing_variables.append("MPESA_CALLBACK_URL")

    if missing_variables:
        logger.error(
            "Missing M-Pesa environment variables: %s",
            missing_variables
        )

        raise HTTPException(
            status_code=500,
            detail="M-Pesa configuration is incomplete."
        )

    # =================================================
    # STK PUSH PAYLOAD
    # =================================================

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(order.total_price),
        "PartyA": phone_number,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": f"ORDER-{order.id}",
        "TransactionDesc": f"Payment for order {order.id}"
    }

    logger.info(
        "Sending STK push for order %s",
        order.id
    )

    logger.info(
        "STK callback URL: %s",
        MPESA_CALLBACK_URL
    )

    # =================================================
    # SEND STK PUSH
    # =================================================

    try:

        response = requests.post(
            f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            timeout=30
        )

        logger.info(
            "M-Pesa HTTP status: %s",
            response.status_code
        )

        logger.info(
            "M-Pesa raw response: %s",
            response.text
        )

    except requests.RequestException:
        logger.exception(
            "M-Pesa STK HTTP request failed."
        )

        raise HTTPException(
            status_code=502,
            detail="Could not connect to M-Pesa."
        )

    # =================================================
    # PARSE RESPONSE
    # =================================================

    try:
        response_data = response.json()

    except Exception:
        logger.exception(
            "M-Pesa returned invalid JSON."
        )

        raise HTTPException(
            status_code=502,
            detail="Invalid response from M-Pesa."
        )

    logger.info(
        "M-Pesa parsed response: %s",
        response_data
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
            detail=response_data.get(
                "errorMessage",
                "M-Pesa payment request failed."
            )
        )

    response_code = response_data.get(
        "ResponseCode"
    )

    checkout_request_id = response_data.get(
        "CheckoutRequestID"
    )

    merchant_request_id = response_data.get(
        "MerchantRequestID"
    )

    # =================================================
    # MAKE SURE M-PESA ACTUALLY ACCEPTED REQUEST
    # =================================================

    if response_code != "0":
        logger.error(
            "M-Pesa rejected STK request: %s",
            response_data
        )

        raise HTTPException(
            status_code=400,
            detail=response_data.get(
                "ResponseDescription",
                "M-Pesa rejected the payment request."
            )
        )

    if not checkout_request_id:

        logger.error(
            "M-Pesa did not return CheckoutRequestID: %s",
            response_data
        )

        raise HTTPException(
            status_code=502,
            detail="M-Pesa did not return a CheckoutRequestID."
        )

    # =================================================
    # SAVE REQUEST IDS
    # =================================================

    try:

        order.checkout_request_id = (
            checkout_request_id
        )

        order.merchant_request_id = (
            merchant_request_id
        )

        order.payment_status = "Pending"

        session.commit()

        logger.info(
            "Saved M-Pesa request IDs for order %s",
            order.id
        )

    except Exception:

        session.rollback()

        logger.exception(
            "Database error while saving M-Pesa request IDs."
        )

        raise HTTPException(
            status_code=500,
            detail="Could not save payment information."
        )

    # =================================================
    # RETURN RESPONSE
    # =================================================

    result = {
        "success": True,
        "message": response_data.get(
            "CustomerMessage",
            "STK Push sent successfully."
        ),
        "order_id": order.id,
        "merchant_request_id": merchant_request_id,
        "checkout_request_id": checkout_request_id,
        "response_code": response_code
    }

    logger.info(
        "========== STK PUSH RETURNING =========="
    )

    logger.info(
        "Response to frontend: %s",
        result
    )

    return result

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


