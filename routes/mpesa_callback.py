
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from models import (
    get_db,
    Order
)

import logging

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/mpesa/callback")
async def mpesa_callback(
    request: Request,
    session: Session = Depends(get_db)
):
    try:
        data = await request.json()

        logger.info("M-Pesa callback received: %s", data)

        stk_callback = (
            data
            .get("Body", {})
            .get("stkCallback", {})
        )

        checkout_request_id = stk_callback.get(
            "CheckoutRequestID"
        )

        result_code = stk_callback.get(
            "ResultCode"
        )

        result_description = stk_callback.get(
            "ResultDesc",
            ""
        )

        if not checkout_request_id:
            logger.error(
                "M-Pesa callback missing CheckoutRequestID"
            )

            return {
                "ResultCode": 1,
                "ResultDesc": "Missing CheckoutRequestID"
            }

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
                "No order found for CheckoutRequestID: %s",
                checkout_request_id
            )

            return {
                "ResultCode": 1,
                "ResultDesc": "Order not found"
            }

        
        # IDEMPOTENCY
        
        # If we already processed this payment,
        # don't process it again.

        if order.payment_status == "Paid":
            logger.info(
                "Order %s already paid. Ignoring duplicate callback.",
                order.id
            )

            return {
                "ResultCode": 0,
                "ResultDesc": "Callback already processed"
            }

        
        # PAYMENT SUCCESSFUL
        

        if result_code == 0:

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

            for item in items:
                if item.get("Name") == "MpesaReceiptNumber":
                    mpesa_receipt_number = item.get("Value")
                    break

            
            # MARK PAYMENT AS PAID
            

            order.payment_status = "Paid"
            order.status = "Processing"

            order.mpesa_receipt_number = (
                mpesa_receipt_number
            )

            
            # FINALIZE STOCK
            

            for order_item in order.items:

                product = order_item.product

                if not product:
                    logger.error(
                        "Product missing for order item %s",
                        order_item.id
                    )
                    continue

                product.stock -= order_item.quantity
                product.reserved_stock -= order_item.quantity

                # Safety protection
                if product.stock < 0:
                    product.stock = 0

                if product.reserved_stock < 0:
                    product.reserved_stock = 0

            session.commit()

            logger.info(
                "Payment successful for order %s. "
                "M-Pesa receipt: %s",
                order.id,
                mpesa_receipt_number
            )

            return {
                "ResultCode": 0,
                "ResultDesc": "Payment processed successfully"
            }

        
        # PAYMENT FAILED / CANCELLED
        

        logger.info(
            "M-Pesa payment failed for order %s: %s",
            order.id,
            result_description
        )

        order.payment_status = "Failed"

        
        # RELEASE RESERVED STOCK
        

        for order_item in order.items:

            product = order_item.product

            if not product:
                continue

            product.reserved_stock -= order_item.quantity

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

        return {
            "ResultCode": 1,
            "ResultDesc": "Callback processing failed"
        }

