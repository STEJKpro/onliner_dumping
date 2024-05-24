from config import config
import pandas as pd
import requests
from io import BytesIO
from database import Session
from sqlalchemy import select
from models import onliner_dumping as db
import logging

def get_price_df() -> pd.DataFrame:
    df = pd.DataFrame()
    file_url = config['PRICE']['PRICE_URL']
    response = requests.get(file_url)
    xlsx_file = pd.ExcelFile(BytesIO(response.content))
    book = xlsx_file.book
    for sheet in book:
        for cell in sheet[1]:
            if "ррц" in str(cell.value).lower() or "розничная" in str(cell.value).lower():
                new_df = xlsx_file.parse(
                    sheet.title,
                    usecols=['Артикул', str(cell.value)],
                    index_col='Артикул',
                )
                new_df = new_df.rename(
                    columns={
                        str(cell.value): 'price',
                        'Артикул': 'vendor_code',
                        
                    }
                )
                new_df['price'] = pd.to_numeric(new_df['price'], errors='coerce')
                df = df = pd.concat([df, new_df])
    return df
    
       
def update_price():
    logging.debug("Start price update")
    df = get_price_df()
    with Session() as session:
        products = session.execute(select(db.Product)).scalars().all()
        for product in products:
            try:
                product.price = df.loc[product.vendor_code, 'price']
            except KeyError: product.price = 0
        session.commit()
    logging.debug("Price update successfully")
    