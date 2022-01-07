# libs
from pydantic import BaseModel

# Class for laptop
class Laptop(BaseModel):
    data_stamp:str
    title:str
    description:str
    link:str
    discount_price:float
    price:float
    image_link:str
    cpu:str
    battery:str
    resolution:str