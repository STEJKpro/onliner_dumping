from data_schemas.data_model import Product, Positions, Position, Shop
from typing import List
from decimal import Decimal
import requests
import models.onliner_dumping as db
from database import Session
from sqlalchemy import select, and_, desc, update
from sqlalchemy.dialects.sqlite import insert
import uuid
from sqlalchemy.orm import lazyload
from email_module.sender import send_email, generate_message
from config import config
from progress.bar import IncrementalBar
from price_update_module.updater import update_price

task_id = uuid.uuid4()

def get_product_data_url(url: str) -> str:
    return "https://catalog.onliner.by/sdapi/catalog.api/products/" + url.rsplit('/', 1)[-1]

def get_product_info(product_url: str) -> Product:
    json_data = requests.get(
        url=get_product_data_url(product_url)
    ).text
    product = Product.model_validate_json(json_data)
    return product

def get_positions_info(positions_url: str) -> List[Position]:
    data = requests.get(
        url=positions_url
    )\
        .json()\
            .get("positions")\
                .get("primary")
    
    positions = Positions.validate_python(data)
    return positions

def get_shop_info(shop_url:str) -> Shop:
    json_data = requests.get(
        url=shop_url
    ).text
    shop = Shop.model_validate_json(json_data)
    return shop

def send_notification_emails(task_id):
    with Session() as session:
        stmt = select(db.Violation.shop_id).where(db.Violation.task_id == task_id).distinct()
        for shop_id in session.scalars(stmt):
            print (shop_id)
            stmt = select(db.Violation).options(lazyload(db.Violation.shop)).filter(and_(db.Violation.task_id == task_id, db.Violation.shop_id ==shop_id))
            violations = session.scalars(stmt).all()
            context = [ {
                         'product':i.product.__dict__, 
                         'shop': i.shop.__dict__,
                         'shop_price': i.shop_price,
                         'base_price': i.base_price,
                         'product_name':i.onliner_product_info.get("full_name"),
                         'email': i.email
                         }
                            for i in violations]
            msg = generate_message('email_templates/violations_notifier.html', context=context)

            send_email(recipient_email=violations[0].email, message_text= msg)
            # send_email(recipient_emails=['sd.bravat@gmail.com', 'dk.pravim@mail.ru'], message_text= msg)
            

def send_admin_email(task_id):
    # print(task_id)
    with Session() as session:
        stmt = select(db.Violation).options(lazyload(db.Violation.shop)).filter(db.Violation.task_id == task_id).order_by(desc(1-db.Violation.shop_price/db.Violation.base_price))
        violations = session.scalars(stmt)
        context = [ {
                        'product':i.product.__dict__, 
                        'shop': i.shop.__dict__,
                        'shop_price': i.shop_price,
                        'base_price': i.base_price,
                        'product_name':i.onliner_product_info.get("full_name")
                        }
                        for i in violations]
    msg = generate_message('email_templates/admin_violations_report.html', context=context)
    send_email(recipient_emails= config['EMAIL']['ADMIN_EMAIL'].replace(' ','').split(','), message_text= msg, msg_id=task_id)

def update_products_price():
    with Session() as session:
        session.execute(
            update(Product),
            ... #Список словарей
        )

if __name__ =='__main__':
    print ("Обновляем прайс")
    #Update products price from google sheet
    update_price()
    print (task_id)
    violating_stores ={}
    with Session() as session:
        check_list = session.query(db.Product).all()
        #Adding progress bar
        progrss_bar = IncrementalBar('Обработка товаров', max= len(check_list))
        
        for check_product in check_list:

            product = get_product_info(
                get_product_data_url(check_product.onliner_url)
            )
            if product.prices and product.prices.price_min.amount/check_product.price<= 1-check_product.dumping_category.dumping_percentage:
                for position in get_positions_info(product.positions_url):
                    if position.position_price.amount/check_product.price <= 1-check_product.dumping_category.dumping_percentage:
                        shop = violating_stores.get(position.shop_full_info_url)
                        if not shop:
                            #Добавление или обновление информации о магазине в БД
                            shop = get_shop_info(position.shop_full_info_url)
                            session.execute(
                                insert(db.Shop).values({
                                    'id': shop.id,
                                    'title': shop.title,
                                    'shop_full_info_url': shop.full_info_url,
                                    'shop_info_json': shop.model_dump()
                                }).on_conflict_do_update(
                                    index_elements=[db.Shop.id],
                                    set_={
                                        'id': shop.id,
                                        'title': shop.title,
                                        'shop_full_info_url': shop.full_info_url,
                                        'shop_info_json': shop.model_dump()
                                    }
                                )
                            )
                            violating_stores[position.shop_full_info_url] = shop
                        #Добавление "нарушения"
                        session.add(
                            db.Violation(
                                task_id=str(task_id),
                                product_id = check_product.vendor_code,
                                shop_id = shop.id,
                                shop_price = position.position_price.amount,
                                base_price = check_product.price,
                                shop_email = shop.addresses[0].email,
                                onliner_product_info = product.model_dump()
                            )
                        )
            progrss_bar.next()
        session.commit()
        
    # send_notification_emails(str(task_id))
    send_admin_email(str(task_id))