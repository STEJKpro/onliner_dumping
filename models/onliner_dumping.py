from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, DECIMAL, JSON, Float
from datetime import datetime
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import column_property


from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

class Violation(Base):
    __tablename__ = 'violations'

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer)
    product_id = Column(String, ForeignKey('products.vendor_code'), nullable=False)
    shop_id = Column(Integer,ForeignKey('shops.id'), nullable=False)
    shop_price = Column(DECIMAL(7, 2))
    base_price = Column(DECIMAL(7, 2))
    shop_email = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    onliner_product_info = Column(JSON)
    __table_args__ = (
        UniqueConstraint('id', 'task_id', name='uq_id_task_id'),
    )

    shop: Mapped["Shop"] = relationship()
    product: Mapped["Product"] = relationship()

    @property
    def email(self):
        return self.shop.shop_custom_contacts.email if self.shop.shop_custom_contacts else self.shop_email



    # Опционально: определение отношений с другими таблицами, если необходимо
    # task = relationship('Task', back_populates='violations')

# Опционально: модель для задачи, если имеется отношение один-ко-многим (одна задача может иметь много нарушений)
class Product(Base):
    __tablename__ = 'products'
    vendor_code = Column(String, primary_key=True)
    onliner_url = Column(String)
    price = Column(DECIMAL(7, 2))
    dumping_category_id =  Column(Integer,ForeignKey('dumping_categories.id'), nullable=False )
    dumping_category = relationship("DumpingCategory", back_populates="product")

class Shop(Base):
    __tablename__ = 'shops'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    shop_full_info_url = Column(String)
    shop_info_json = Column(JSON)
    
    shop_custom_contacts: Mapped["ShopCustomContacts"] = relationship()

class ShopCustomContacts(Base):
    __tablename__ = 'shops_custom_contacts'
    id = Column(Integer, ForeignKey('shops.id'), nullable=False, primary_key=True)
    email = Column(String)
    phone = Column(String)
    
    # shop: Mapped["Violation"] = relationship()


class DumpingCategory(Base):
    __tablename__ = 'dumping_categories'
    
    id = Column(Integer, nullable=False, primary_key=True)
    dumping_percentage = Column(Float, nullable=False)
    description = Column(String)
    product = relationship("Product", back_populates="dumping_category", uselist=False)