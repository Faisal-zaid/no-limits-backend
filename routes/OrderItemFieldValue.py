from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from models import OrderItemFieldValue, get_db, ProductField
from pydantic import BaseModel
import cloudinary.uploader
import cloudinary_config



router = APIRouter()

# UPLOAD_FOLDER = "uploads"

# os.makedirs(UPLOAD_FOLDER, exist_ok=True)  #creates a folder called uploads within project repo

#validation

class OrderItemFieldValueSchema(BaseModel):
    order_item_id: int
    product_field_id: int
    value: str

#create rooute

@router.post("/orderitemfieldvalue")
def create_order_item_field_value(
    data: OrderItemFieldValueSchema,
    session=Depends(get_db)
):

    new_value = OrderItemFieldValue(
        order_item_id=data.order_item_id,
        product_field_id=data.product_field_id,
        value=data.value
    )

    session.add(new_value)

    session.commit()

    session.refresh(new_value)

    return {
        "message": "Order item field value created successfully",
        "order_item_field_value_id": new_value.id
    }

#get all items

@router.get("/orderitemfieldvalue")
def get_order_item_field_values(
    session=Depends(get_db)
):

    values = session.query(
        OrderItemFieldValue
    ).all()

    return values

# GET ONE ORDER ITEM FIELD VALUE

@router.get("/orderitemfieldvalue/{value_id}")
def get_order_item_field_value(
    value_id: int,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    return value

#get one item

@router.get("/orderitemfieldvalue/orderitem/{order_item_id}")
def get_values_by_order_item(
    order_item_id: int,
    session=Depends(get_db)
):

    values = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.order_item_id == order_item_id
    ).all()

    result = []

    for value in values:

        result.append({
            "id": value.id,
            "order_item_id": value.order_item_id,
            "product_field_id": value.product_field_id,
            "field_label": value.product_field.label,
            "field_type": value.product_field.field_type,
            "value": value.value
        })    #from result.append is possible because models.py has access to product

    return result

# UPDATE ORDER ITEM FIELD VALUE

@router.patch("/orderitemfieldvalue/{value_id}")
def update_order_item_field_value(
    value_id: int,
    data: OrderItemFieldValueSchema,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    value.order_item_id = data.order_item_id
    value.product_field_id = data.product_field_id
    value.value = data.value

    session.commit()

    session.refresh(value)

    return {
        "message": "Order item field value updated successfully"
    }

#delte items

@router.delete("/orderitemfieldvalue/{value_id}")
def delete_order_item_field_value(
    value_id: int,
    session=Depends(get_db)
):

    value = session.query(
        OrderItemFieldValue
    ).filter(
        OrderItemFieldValue.id == value_id
    ).first()

    if not value:
        return {
            "message": "Order item field value not found"
        }

    session.delete(value)

    session.commit()

    return {
        "message": "Order item field value deleted successfully"
    }

@router.post("/orderitemfieldvalue/image")
async def upload_order_item_image(
    order_item_id: int = Form(...),
    product_field_id: int = Form(...),
    image: UploadFile = File(...),
    session=Depends(get_db)
):

    product_field = (
        session.query(ProductField)
        .filter(ProductField.id == product_field_id)
        .first()
    )

    if not product_field:
        raise HTTPException(
            status_code=404,
            detail="Product field not found"
        )

    if product_field.field_type != "image":
        raise HTTPException(
            status_code=400,
            detail="This field does not accept images"
        )

    # if not image.content_type.startswith("image/"):
    #             raise HTTPException(
    #             status_code=400,
    #             detail="Only image files are allowed"
    #         )

        

    # #from the start of this to .......

    # file_extension = image.filename.split(".")[-1]

    # filename = f"{uuid.uuid4()}.{file_extension}"

    # file_path = os.path.join(
    #     UPLOAD_FOLDER,
    #     filename
    # )

    # #the edn of line above assigns a unique id to files 

    # with open(file_path, "wb") as buffer:
    #     buffer.write(await image.read())

#check file type 

    if not image.content_type:
     raise HTTPException(
                 status_code=400,
                 detail="File type could not be determined"
             )
        

    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Only image files are allowed"
        )

    try:
            upload_result = cloudinary.uploader.upload(
                    image.file,
                    folder="nolimit/customer_customizations"
                )
    


    
       

    except Exception as error:
        print("Cloudinary upload error:", error)
    
        raise HTTPException(
                status_code=500,
                detail="upload images of type png,jpg,jpeg"
            )

        

 # GET CLOUDINARY URL

    image_url = upload_result["secure_url"]


    new_value = OrderItemFieldValue(
        order_item_id=order_item_id,
        product_field_id=product_field_id,
        value=image_url
    )

    session.add(new_value)

    session.commit()

    session.refresh(new_value)

    return {
        "message": "Image uploaded successfully",
        "image_url": image_url,
        "value_id": new_value.id
    }    

