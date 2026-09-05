
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List

from models import (
    get_db,
    Product,
    ProductField,
    Order,
    OrderItem,
    OrderItemFieldValue
)


router = APIRouter()


# =====================================================
# SCHEMAS
# =====================================================

class FieldValueSchema(BaseModel):
    product_field_id: int
    value: str


class CheckoutItemSchema(BaseModel):
    product_id: int
    quantity: int
    fields: List[FieldValueSchema] = Field(
        default_factory=list
    )


class CheckoutSchema(BaseModel):
    customer_name: str
    customer_email: str
    customer_phone: str
    items: List[CheckoutItemSchema]


# =====================================================
# CHECKOUT
# =====================================================

@router.post("/checkout")
def checkout(
    data: CheckoutSchema,
    session=Depends(get_db)
):

    # =================================================
    # BASIC VALIDATION
    # =================================================

    if not data.items:
        raise HTTPException(
            status_code=400,
            detail="Your cart is empty."
        )

    # =================================================
    # AGGREGATE QUANTITIES
    #
    # This protects us if the same product somehow
    # appears multiple times in the cart.
    # =================================================

    requested_quantities = {}

    for item in data.items:

        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than zero."
            )

        requested_quantities[item.product_id] = (
            requested_quantities.get(
                item.product_id,
                0
            )
            + item.quantity
        )

    # =================================================
    # LOAD PRODUCTS WITH ROW LOCKS
    #
    # with_for_update() prevents two customers from
    # purchasing the same remaining stock at the same
    # time.
    # =================================================

    products = {}

    try:

        for product_id in sorted(
            requested_quantities.keys()
        ):

            product = (
                session.query(Product)
                .filter(
                    Product.id == product_id
                )
                .with_for_update()
                .first()
            )

            if not product:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"Product with id "
                        f"{product_id} not found."
                    )
                )

            requested_quantity = (
                requested_quantities[
                    product_id
                ]
            )

            # =========================================
            # STOCK CHECK
            # =========================================

            if product.stock < requested_quantity:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Not enough stock for "
                        f"{product.name}. "
                        f"Available: {product.stock}, "
                        f"requested: "
                        f"{requested_quantity}."
                    )
                )

            # =========================================
            # PRICE CHECK
            # =========================================

            if product.base_price is None:

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Product '{product.name}' "
                        f"has no price."
                    )
                )

            products[product_id] = product

        # =================================================
        # CALCULATE TOTAL FROM DATABASE
        # =================================================

        total_price = 0

        for item in data.items:

            product = products[
                item.product_id
            ]

            total_price += (
                product.base_price
                * item.quantity
            )

        # =================================================
        # CREATE ORDER
        # =================================================

        order = Order(
            customer_name=data.customer_name.strip(),
            customer_email=data.customer_email.strip(),
            customer_phone=data.customer_phone.strip(),
            status="Pending",
            total_price=total_price
        )

        session.add(order)

        # Get order.id before creating OrderItems
        session.flush()

        # =================================================
        # CREATE ORDER ITEMS
        # =================================================

        for item in data.items:

            product = products[
                item.product_id
            ]

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity
            )

            session.add(order_item)

            # Get order_item.id
            session.flush()

            # =============================================
            # VALIDATE AND SAVE CUSTOM FIELDS
            # =============================================

            for field in item.fields:

                product_field = (
                    session.query(ProductField)
                    .filter(
                        ProductField.id ==
                        field.product_field_id
                    )
                    .first()
                )

                if not product_field:

                    raise HTTPException(
                        status_code=404,
                        detail=(
                            f"Product field "
                            f"{field.product_field_id} "
                            f"not found."
                        )
                    )

                # =========================================
                # MAKE SURE FIELD BELONGS TO PRODUCT
                # =========================================

                if (
                    product_field.product_id
                    != product.id
                ):

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"Product field "
                            f"{field.product_field_id} "
                            f"does not belong to "
                            f"{product.name}."
                        )
                    )

                # =========================================
                # SAVE FIELD VALUE
                # =========================================

                field_value = OrderItemFieldValue(
                    order_item_id=order_item.id,
                    product_field_id=(
                        product_field.id
                    ),
                    value=field.value
                )

                session.add(field_value)

            # =============================================
            # DEDUCT STOCK
            # =============================================

            product.stock -= item.quantity

        # =================================================
        # COMMIT EVERYTHING
        # =================================================

        session.commit()

        session.refresh(order)

        return {
            "message": "Order placed successfully.",
            "order_id": order.id,
            "total_price": order.total_price,
            "status": order.status
        }

    except HTTPException:

        session.rollback()
        raise

    except Exception as error:

        session.rollback()

        print(
            "CHECKOUT ERROR:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not complete checkout."
            )
        )

