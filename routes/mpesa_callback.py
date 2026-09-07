from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from rate_limit import strict_limit, moderate_limit, low_limit

from models import get_db, Order

import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/mpesa/callback")
async def mpesa_callback(
    request: Request,
    session: Session = Depends(get_db)
):
    try:

        # =================================================
        # READ RAW CALLBACK
        # =================================================

        data = await request.json()

        logger.info(
            "========== M-PESA CALLBACK RECEIVED =========="
        )

        logger.info(
            "M-Pesa callback body: %s",
            data
        )

        # =================================================
        # EXTRACT STK CALLBACK
        # =================================================

        stk_callback = (
            data
            .get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = stk_callback.get(
            "CheckoutRequestID"
        )

        merchant_request_id = stk_callback.get(
            "MerchantRequestID"
        )

        result_code = stk_callback.get(
            "ResultCode"
        )

        result_description = stk_callback.get(
            "ResultDesc",
            ""
        )

        logger.info(
            "CheckoutRequestID: %s",
            checkout_request_id
        )

        logger.info(
            "MerchantRequestID: %s",
            merchant_request_id
        )

        logger.info(
            "ResultCode: %s",
            result_code
        )

        logger.info(
            "ResultDesc: %s",
            result_description
        )

        # =================================================
        # VALIDATE CHECKOUT REQUEST ID
        # =================================================

        if not checkout_request_id:

            logger.error(
                "M-Pesa callback missing CheckoutRequestID"
            )

            return {
                "ResultCode": 1,
                "ResultDesc": "Missing CheckoutRequestID"
            }

        # =================================================
        # FIND ORDER
        # =================================================

        order = (
            session.query(Order)
            .filter(
                Order.checkout_request_id
                == checkout_request_id
            )
            .first()
        )

        if not order:

            logger.error(
                "NO ORDER FOUND for CheckoutRequestID: %s",
                checkout_request_id
            )

            return {
                "ResultCode": 1,
                "ResultDesc": "Order not found"
            }

        logger.info(
            "Order found: %s",
            order.id
        )

        logger.info(
            "Current payment status: %s",
            order.payment_status
        )

        # =================================================
        # IDEMPOTENCY
        # =================================================

        if order.payment_status == "Paid":

            logger.info(
                "Order %s is already Paid. Ignoring duplicate callback.",
                order.id
            )

            return {
                "ResultCode": 0,
                "ResultDesc": "Already processed"
            }

        # =================================================
        # PAYMENT SUCCESS
        # =================================================

        if str(result_code) == "0":

            logger.info(
                "PAYMENT SUCCESS for order %s",
                order.id
            )

            callback_metadata = (
                stk_callback.get(
                    "CallbackMetadata",
                    {}
                )
            )

            items = callback_metadata.get(
                "Item",
                []
            )

            mpesa_receipt_number = None

            # =================================================
            # EXTRACT RECEIPT
            # =================================================

            for item in items:

                if item.get("Name") == "MpesaReceiptNumber":

                    mpesa_receipt_number = (
                        item.get("Value")
                    )

                    break

            logger.info(
                "M-Pesa receipt: %s",
                mpesa_receipt_number
            )

            # =================================================
            # MARK ORDER PAID
            # =================================================

            order.payment_status = "Paid"

            order.status = "Processing"

            order.mpesa_receipt_number = (
                mpesa_receipt_number
            )

            # =================================================
            # FINALIZE STOCK
            # =================================================

            for order_item in order.items:

                product = order_item.product

                if not product:

                    logger.error(
                        "Product missing for OrderItem %s",
                        order_item.id
                    )

                    continue

                logger.info(
                    "Finalizing stock: product=%s quantity=%s",
                    product.id,
                    order_item.quantity
                )

                product.stock -= (
                    order_item.quantity
                )

                product.reserved_stock -= (
                    order_item.quantity
                )

                if product.stock < 0:
                    product.stock = 0

                if product.reserved_stock < 0:
                    product.reserved_stock = 0

            # =================================================
            # COMMIT
            # =================================================

            session.commit()

            logger.info(
                "SUCCESSFULLY MARKED ORDER %s AS PAID",
                order.id
            )

            return {
                "ResultCode": 0,
                "ResultDesc": "Payment processed successfully"
            }

        # =================================================
        # PAYMENT FAILED
        # =================================================

        logger.warning(
            "PAYMENT FAILED for order %s",
            order.id
        )

        logger.warning(
            "ResultCode: %s",
            result_code
        )

        logger.warning(
            "ResultDesc: %s",
            result_description
        )

        order.payment_status = "Failed"

        # =================================================
        # RELEASE RESERVED STOCK
        # =================================================

        for order_item in order.items:

            product = order_item.product

            if not product:
                continue

            product.reserved_stock -= (
                order_item.quantity
            )

            if product.reserved_stock < 0:
                product.reserved_stock = 0

        session.commit()

        return {
            "ResultCode": 0,
            "ResultDesc": "Payment failure processed"
        }

    except Exception as error:

        session.rollback()

        logger.exception(
            "M-Pesa callback processing error: %s",
            error
        )

        # Return HTTP 200 with Safaricom response structure
        # rather than allowing an unexpected server error.

        return {
            "ResultCode": 1,
            "ResultDesc": "Callback processing failed"
        }