from fastapi import FastAPI, HTTPException
from tortoise.contrib.fastapi import register_tortoise
from models import (supplier_pydantic, supplier_pydanticIn, Supplier, product_Pydantic, product_pydanticIn, Product)

#email
from typing import List
from fastapi import BackgroundTasks, FastAPI
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from pydantic import BaseModel, EmailStr
from starlette.responses import JSONResponse
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

#adding cors headers
from fastapi.middleware.cors import CORSMiddleware

# Get environment variables with error handling
email = os.getenv("EMAIL")
password = os.getenv("PASS")

app = FastAPI()

#adding cors urls
origins = [
    'http://localhost:3000'
]

#add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def index():
    return {"Msg": "Hello, World!"}

@app.post("/suppliers/")
async def add_supplier(supplier_info: supplier_pydanticIn):
    supplier_obj = await Supplier.create(**supplier_info.dict(exclude_unset=True))
    response = await supplier_pydantic.from_tortoise_orm(supplier_obj)
    return {"status": "ok", "data": response}

@app.get("/suppliers/")
async def get_all_suppliers():
    response = await supplier_pydantic.from_queryset(Supplier.all())
    return {"status": "ok", "data": response}

@app.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int):
    supplier = await Supplier.get_or_none(id=supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    response = await supplier_pydantic.from_tortoise_orm(supplier)
    return {"status": "ok", "data": response}

@app.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: int, update_info: supplier_pydanticIn):
    supplier = await Supplier.get(id=supplier_id)
    update_info = update_info.dict(exclude_unset=True)
    
    # Update only if the field exists in the update_info
    if "name" in update_info:
        supplier.name = update_info["name"]
    if "company" in update_info:
        supplier.company = update_info["company"]
    if "email" in update_info:
        supplier.email = update_info["email"]
    if "phone" in update_info:
        supplier.phone = update_info["phone"]
    
    await supplier.save()
    response = await supplier_pydantic.from_tortoise_orm(supplier)
    return {"status": "ok", "data": response}

@app.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: int):
    supplier = await Supplier.get(id=supplier_id)
    await supplier.delete()
    return {"status": "ok", "data": "Supplier deleted successfully!"}

@app.post("/product/{supplier_id}")
async def add_product(supplier_id: int, product_details: product_pydanticIn):
    supplier = await Supplier.get(id=supplier_id)
    product_details = product_details.dict(exclude_unset=True)
    product_details['revenue'] = product_details['quantity_sold'] * product_details['unit_price']
    product_obj = await Product.create(**product_details, supplied_by=supplier)
    response = await product_Pydantic.from_tortoise_orm(product_obj)
    return {"status": "ok", "data": response}

@app.get("/product/")
async def get_all_products():
    response = await product_Pydantic.from_queryset(Product.all())
    return {"status": "ok", "data": response}

@app.get("/product/{product_id}")
async def get_product(product_id: int):
    response = await product_Pydantic.from_queryset_single(Product.get(id=product_id))
    return {"status": "ok", "data": response}

@app.put('/product/{product_id}')
async def update_product(product_id: int, update_info: product_pydanticIn):
    product = await Product.get(id=product_id)
    update_info = update_info.dict(exclude_unset=True)
    # Update only if the field exists in the update_info
    if "name" in update_info:
        product.name = update_info["name"]
    if "quantity_in_stock" in update_info:
        product.quantity_in_stock = update_info["quantity_in_stock"]
    if "unit_price" in update_info:
        product.unit_price = update_info["unit_price"]
    if "supplied_by" in update_info:
        product.supplied_by = update_info["supplied_by"]
    if "revenue" in update_info:
        product.revenue = update_info["revenue"]
    if "quantity_sold" in update_info:
        product.quantity_sold += update_info["quantity_sold"]
    await product.save()
    response = await product_Pydantic.from_tortoise_orm(product)
    return {"status": "ok", "data": response}

@app.delete("/product/{product_id}")
async def delete_product(product_id: int):
    product = await Product.get(id=product_id)
    await product.delete()
    return {"status": "ok", "data": "Product deleted successfully!"}


class EmailSchema(BaseModel):
    email: List[EmailStr]

class EmailContent(BaseModel):
    message: str
    subject: str

if not email or not password:
    raise ValueError("Email and password must be set in environment variables")

conf = ConnectionConfig(
    MAIL_USERNAME=email,
    MAIL_PASSWORD=password,
    MAIL_FROM=email,  # Using the same email as username
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

@app.post("/email/{product_id}")
async def send_email(product_id: int, content: EmailContent):
    try:
        product = await Product.get(id=product_id)
        supplier = await product.supplied_by
        supplier_email = [supplier.email]

        html = f"""
        <h5>John Does Business LTD</h5>
        <br>
        <p>{content.subject}</p>
        <p>{content.message}</p>
        <h5>Best Regards</h5>
        <h6>John Doe</h6>
        """

        message = MessageSchema(
            subject=content.subject,  # Remove the curly braces
            recipients=supplier_email,
            body=html,
            subtype=MessageType.html  # Fix the subtype parameter
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        return {"status": "ok", "data": "Email sent successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Database setup
register_tortoise(
    app,
    db_url='sqlite://database.sqlite3',
    modules={'models': ['models']},
    generate_schemas=True,
    add_exception_handlers=True
)
