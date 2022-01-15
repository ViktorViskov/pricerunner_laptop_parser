# libs
from pydantic import BaseModel

# Class for laptop
class Laptop(BaseModel):
    data_stamp:str
    title:str
    description:str
    link:str
    price:float
    image_link:str
    cpu:str
    battery:str
    resolution:str

class CPU(BaseModel):
    title:str
    single:float = 0
    multi:float = 0