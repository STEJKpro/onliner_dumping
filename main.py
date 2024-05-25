import argparse
import logging
import uuid
from decimal import Decimal
from typing import List

import requests
from progress.bar import IncrementalBar
from sqlalchemy import and_, desc, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import lazyload

import models.onliner_dumping as db
from config import config
from data_schemas.data_model import Position, Positions, Product, Shop
from database import Session
from email_module.sender import generate_message, send_email
from price_update_module.updater import update_price

logging.basicConfig(filename='logs/degub.log', filemode='a+', level=logging.DEBUG, encoding='utf-8')

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument ("--admin_email", help="Send admin email report", action="store_true")
arg_parser.add_argument ("--notify_emails", help="Send notyfy email for sellers", action="store_true")
arg_parser.add_argument ("--without_price_update", action="store_true")
arg_parser.add_argument ("--admin_email_by_id",)


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
            stmt = select(db.Violation).options(lazyload(db.Violation.shop)).filter(and_(db.Violation.task_id == task_id, db.Violation.shop_id ==shop_id))
            violations = session.scalars(stmt).all()
            if violations[0].email == 'IGNORE':
                logging.info(f'Сообщение для {violations[0].shop.title} не отправлено. Email - EGNORE')
            else:
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
                send_email(recipient_emails=[violations[0].email,], message_text= msg)
                logging.info(f'Сообщение для {violations[0].shop.title} отправлено на {violations[0].email}')
            
def send_admin_email(task_id):
    with Session() as session:
        stmt = select(db.Violation).options(lazyload(db.Violation.shop)).filter(db.Violation.task_id == task_id).order_by(desc(1-db.Violation.shop_price/db.Violation.base_price))
        violations = session.scalars(stmt)
        context = [ {
                        'product':i.product.__dict__, 
                        'shop': i.shop.__dict__,
                        'shop_price': i.shop_price,
                        'base_price': i.base_price,
                        'product_name':i.onliner_product_info.get("full_name"),
                        'email': i.email
                        }
                        for i in violations]
        if context: 
            msg = generate_message('email_templates/admin_violations_report.html', context=context)
            send_email(recipient_emails= config['EMAIL']['ADMIN_EMAIL'].replace(' ','').split(','), message_text= msg, msg_id=task_id)
            logging.info(f"Отчет администратора отправлен {config['EMAIL']['ADMIN_EMAIL'].replace(' ','').split(',')}")
        else:
            logging.info(f"Отправка отчета админу пропущено, т.к. отсутствуют нарушения. Отправка пустого уведомительного письма; {config['EMAIL']['ADMIN_EMAIL'].replace(' ','').split(',')}")
            send_email(recipient_emails= config['EMAIL']['ADMIN_EMAIL'].replace(' ','').split(','), message_text= "НАРУШЕНИЙ НЕ ОБНАРУЖЕНО", msg_id=task_id)
            return

def update_products_price():
    with Session() as session:
        session.execute(
            update(Product),
            ... #Список словарей
        )

if __name__ =='__main__':
    args = arg_parser.parse_args()
    if args.admin_email_by_id:
        send_admin_email(args.admin_email_by_id)
        exit()
    
    #Update products price from google sheet
    if args.without_price_update:
        logging.debug('Установлен флаг "--without_price_update". Обновления прайса пропущено')
    else:
        update_price()

    violating_stores ={}
    with Session() as session:
        check_list = session.query(db.Product).all()
        #Adding progress bar
        progrss_bar = IncrementalBar('Обработка товаров', max= len(check_list))
        
        for check_product in check_list:

            product = get_product_info(
                get_product_data_url(check_product.onliner_url)
            )
            if product.prices and check_product.price > 0 and product.prices.price_min.amount/check_product.price<= 1-check_product.dumping_category.dumping_percentage:
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
    
    if args.admin_email:
        logging.info("Запуск отправки отчета администратору")
        send_admin_email(str(task_id))
    if args.notify_emails:
        logging.info("Запуск отправки писем нарушителям")
        send_notification_emails(str(task_id))
    