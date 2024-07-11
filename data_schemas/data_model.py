from dataclasses import dataclass
from typing import List, Any, Optional, Annotated
from decimal import Decimal
from pydantic import BaseModel, EmailStr, TypeAdapter, PlainSerializer


class Product(BaseModel):
    pass


class Dumper(BaseModel):
    products: List[Product]
    shop_name: str
    email: EmailStr
    
 
 
#######################
"""
    Модели для Предложений (Positions) от магазинов
"""
class PositionPrice(BaseModel):
    amount: Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float, when_used='always')]
    currency: str


class Commission(BaseModel):
    amount: Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float, when_used='always')]
    currency: str


class Position(BaseModel):
    id: str
    shop_id: int
    position_price: PositionPrice
    comment: str
    producer: str
    importer: str
    service_centers: str
    date_update: str
    # commission: Commission
    product_url: str
    shop_url: str
    shop_full_info_url: str

Positions = TypeAdapter(List[Position])
    


#########################
"""
    Модели для Product
"""
class MinPricesMedian(BaseModel):
    amount: Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float, when_used='always')]
    currency: str

class Sale(BaseModel):
    is_on_sale: bool
    discount: int
    min_prices_median: MinPricesMedian
    subscribed: bool
    can_be_subscribed: bool


class PriceMin(BaseModel):
    amount: Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float, when_used='always')]
    currency: str


class PriceMax(BaseModel):
    amount: Annotated[Decimal, PlainSerializer(lambda x: float(x), return_type=float, when_used='always')]
    currency: str
    

class Offers(BaseModel):
    count: int

class Prices(BaseModel):
    price_min: PriceMin
    price_max: PriceMax
    offers: Offers
    html_url: str
    url: str #Positions url

class Product(BaseModel):
    id: int
    key: str
    name: str
    full_name: str
    name_prefix: str
    extended_name: str
    status: str
    parent_key: str
    sale: Sale
    certification_required: bool
    color_code: Any
    url: str
    prices: Optional[Prices] = None
    
    @property
    def positions_url(self) -> str:
        return None if not self.prices else self.prices.url
    @property
    def price_min(self) -> Decimal:
        return self.prices.price_min.amount
    
    
    
    
    
#####################################
        """Модели для магазинов (Shop)
        """
        


class SchemaPhone(BaseModel):
    schema_id: int
    phones: List[str]


class Customer(BaseModel):
    """
    Юридическая информация
    """
    title: str
    unp: str
    egr: str
    address: str
    registration_date: str
    registration_agency: str
    complaint_book: Any


class Town(BaseModel):
    id: int
    key: str
    title: str
    prepositional_case: str

class Address(BaseModel):
    town: Town
    address: str
    email: str | None
    skype: str | None
    viber: str | None
    telegram: str | None
    whats_app: str | None
    phones: List[str]


class WarrantyContacts(BaseModel):
    phones: List[str]
    email: str | None
    skype: str | None
    viber: str | None
    telegram: str | None
    whatsApp: str | None


class Shop(BaseModel):
    id: int
    url: str
    full_info_url: str
    html_url: str
    title: str
    logo: str
    is_new_shop: bool
    schema_phones: List[SchemaPhone]
    registration_date: str
    customer: Customer
    addresses: List[Address]
    warranty_contacts: WarrantyContacts | None = None
