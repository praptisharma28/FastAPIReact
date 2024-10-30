from tortoise.models import Model
from tortoise import fields
from tortoise.contrib.pydantic import pydantic_model_creator

class Product(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    quantity_in_stock = fields.IntField(default=0)
    unit_price = fields.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    supplied_by = fields.ForeignKeyField('models.Supplier', related_name='goods_supplied')   
    revenue = fields.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    quantity_sold = fields.IntField(default=0)

class Supplier(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=255)
    company = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255)
    phone = fields.CharField(max_length=20)

# Create pydantic models
product_Pydantic = pydantic_model_creator(Product, name="Product")
product_pydanticIn = pydantic_model_creator(Product, name="ProductIn", exclude_readonly=True)

supplier_pydantic = pydantic_model_creator(Supplier, name="Supplier")
supplier_pydanticIn = pydantic_model_creator(Supplier, name="SupplierIn", exclude_readonly=True)