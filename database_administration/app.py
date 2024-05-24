from flask import Flask, abort, redirect, render_template, request
from flask import url_for

from database import Session
from models.onliner_dumping import (Base, DumpingCategory, Product, Shop,
                                    ShopCustomContacts, Violation)
from price_update_module.updater import update_price


app = Flask(__name__)
app.secret_key = 'UkE0GSI0lxNRJ83n6Dul'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'

# Создание движка SQLAlchemy
# engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
# Base.metadata.bind = engine

# Создание сессии
session = Session()


# @app.route('/add_violation', methods=['POST'])
# def add_violation():
#     task_id = request.form.get('task_id')
#     product_id = request.form.get('product_id')
#     shop_id = request.form.get('shop_id')
#     shop_price = request.form.get('shop_price')
#     base_price = request.form.get('base_price')
#     shop_email = request.form.get('shop_email')
#     onliner_product_info = request.form.get('onliner_product_info')
#     new_violation = Violation(
#         task_id=task_id,
#         product_id=product_id,
#         shop_id=shop_id,
#         shop_price=shop_price,
#         base_price=base_price,
#         shop_email=shop_email,
#         onliner_product_info=onliner_product_info
#     )
#     session.add(new_violation)
#     session.commit()
#     return redirect(url_for('index'))

# @app.route('/delete_violation/<int:id>')
# def delete_violation(id):
#     violation = session.query(Violation).get(id)
#     session.delete(violation)
#     session.commit()
#     return redirect(url_for('index'))
@app.route('/')
def index():
    violations = session.query(Violation).all()
    products = session.query(Product).all()
    categories = session.query(DumpingCategory).all()
    shops = session.query(Shop).all()
    contacts = session.query(ShopCustomContacts).all()
    return render_template('index.html', violations=violations, products=products, categories=categories, shops=shops, contacts=contacts)

# Product routes
@app.route('/add_product', methods=['POST'])
def add_product():
    vendor_code = request.form.get('vendor_code')
    onliner_url = request.form.get('onliner_url')
    price = request.form.get('price')
    dumping_category_id = request.form.get('dumping_category_id')
    new_product = Product(
        vendor_code=vendor_code,
        onliner_url=onliner_url,
        price=price,
        dumping_category_id=dumping_category_id
    )
    session.add(new_product)
    session.commit()
    return redirect(url_for('index'))

@app.route('/delete_product/<string:vendor_code>')
def delete_product(vendor_code):
    product = session.query(Product).get(vendor_code)
    session.delete(product)
    session.commit()
    return redirect(url_for('index'))

@app.route('/edit_product/<string:vendor_code>', methods=['GET', 'POST'])
def edit_product(vendor_code):
    product = session.query(Product).get(vendor_code)
    if request.method == 'POST':
        product.onliner_url = request.form.get('onliner_url')
        product.price = request.form.get('price')
        product.dumping_category_id = request.form.get('dumping_category_id')
        session.commit()
        return redirect(url_for('index'))
    return render_template('edit_product.html', product=product)

# Category routes
@app.route('/add_category', methods=['POST'])
def add_category():
    dumping_percentage = request.form.get('dumping_percentage')
    description = request.form.get('description')
    new_category = DumpingCategory(
        dumping_percentage=dumping_percentage,
        description=description
    )
    session.add(new_category)
    session.commit()
    return redirect(url_for('index'))

@app.route('/delete_category/<int:id>')
def delete_category(id):
    category = session.query(DumpingCategory).get(id)
    session.delete(category)
    session.commit()
    return redirect(url_for('index'))

@app.route('/edit_category/<int:id>', methods=['GET', 'POST'])
def edit_category(id):
    category = session.query(DumpingCategory).get(id)
    if request.method == 'POST':
        category.dumping_percentage = request.form.get('dumping_percentage')
        category.description = request.form.get('description')
        session.commit()
        return redirect(url_for('index'))
    return render_template('edit_category.html', category=category)

# ShopCustomContacts routes
@app.route('/add_contact', methods=['POST'])
def add_contact():
    shop_id = request.form.get('shop_id')
    email = request.form.get('email')
    phone = request.form.get('phone')
    new_contact = ShopCustomContacts(
        id=shop_id,
        email=email,
        phone=phone
    )
    session.add(new_contact)
    session.commit()
    return redirect(url_for('index'))

@app.route('/delete_contact/<int:id>')
def delete_contact(id):
    contact = session.query(ShopCustomContacts).get(id)
    session.delete(contact)
    session.commit()
    return redirect(url_for('index'))

@app.route('/edit_contact/<int:id>', methods=['GET', 'POST'])
def edit_contact(id):
    contact = session.query(ShopCustomContacts).get(id)
    if request.method == 'POST':
        contact.email = request.form.get('email')
        contact.phone = request.form.get('phone')
        session.commit()
        return redirect(url_for('index'))
    return render_template('edit_contact.html', contact=contact)

@app.route('/update_products_price', methods=['GET'])
def update_products_price():
    try:
        update_price()
    except: 
        return abort(500)
    
    return redirect(url_for('index'))

def main():
    # port = 5000 + random.randint(0, 999)
    port = 5000
    url = "http://127.0.0.1:{0}".format(port)
    app.run(host="127.0.0.1", port=port, debug=True)

if __name__ == '__main__':
    main()