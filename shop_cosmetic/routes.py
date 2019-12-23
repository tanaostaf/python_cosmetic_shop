from flask import render_template, url_for, flash, redirect, request, abort,jsonify
from shop_cosmetic import app, db, bcrypt
from shop_cosmetic.forms import RegistrationForm, LoginForm, UpdateAccountForm, ProductForm
from shop_cosmetic.models import User, Product, Cart, association_table, Order
from flask_login import login_user, current_user, logout_user, login_required
import os
import secrets
from PIL import Image
from functools import wraps


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/images', picture_fn)

    output_size = (200, 200)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


def admin_login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_admin():
            return abort(403)
        return func(*args, **kwargs)
    return decorated_view


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=4)
    return render_template('home.html', products=products)


@app.route("/cart", methods=['GET', 'POST'])
@login_required
def cart():
    cart = Cart.query.filter_by(ordered=False, user_id=current_user.id).first()
    if request.method == 'POST':
        if not cart:
            cart = Cart(user_id=current_user.id, ordered=False)   
        db.session.add(cart)
        db.session.commit()        
        product_id = request.form.get('product_id')  
        statement = association_table.insert().values(cart_id=cart.id, product_id=int(product_id))
        db.session.execute(statement)
        db.session.commit()                  
    return render_template('cart.html', cart=cart)



@app.route("/order", methods=['POST'])
@login_required
def order():
    if request.method != 'POST':
        redirect(url_for('cart'))
    cart_id = request.form.get('cart_id')  
    cart = Cart.query.filter_by(id=int(cart_id), user_id=current_user.id).first()
    return render_template('order.html', cart=cart)


@app.route("/submit", methods=['POST'])
@login_required
def submit_order():
    if request.method != 'POST':
        redirect(url_for('cart'))
    cart_id = request.form.get('cart_id', '')
    firstname = request.form.get('firstname', '')
    lastname = request.form.get('lastname', '')      
    address = request.form.get('address', '')
    order = Order(cart_id=int(cart_id), first_name=firstname, last_name=lastname,
                  shipping_address=address)
    cart = Cart.query.get(int(cart_id))
    cart.ordered = True
    db.session.add(cart)
    db.session.add(order)
    db.session.commit()
    return render_template('submit_order.html')


@app.route("/orders", methods=['GET', 'POST'])
@admin_login_required
def orders():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        order = Order.query.get(int(order_id))
        if order:
            order.closed = True
            db.session.add(order)
            db.session.commit()
    orders = Order.query.filter_by(closed=False).all()
    return render_template('orders_admin.html', orders=orders)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('home'))


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if bcrypt.check_password_hash(current_user.password, form.old_pass.data):
            hashed_password = bcrypt.generate_password_hash(form.new_pass.data).decode('utf-8')
            current_user.password = hashed_password
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template('account.html', title='Account', form=form)

@app.route('/admin')
@admin_login_required
def home_admin():
    return


@app.route("/product/new", methods=['GET', 'POST'])
@admin_login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.picture.data)
        product = Product(p_name=form.p_name.data, description=form.description.data, price=form.price.data, image=picture_file)
        db.session.add(product)
        db.session.commit()
        flash('Product has been added!', 'success')
        return redirect(url_for('home'))
    return render_template('add_product.html', title='Add Product', form=form, legend='Add Product')


@app.route("/product/<int:product_id>")
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', p_name=product.p_name, product=product)


@app.route("/product/<int:product_id>/update", methods=['GET', 'POST'])
@admin_login_required
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    if form.validate_on_submit():
        product.p_name = form.p_name.data
        product.description = form.description.data
        product.price = form.price.data
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            product.image = picture_file
        db.session.commit()
        flash('Your product has been updated!', 'success')
        return redirect(url_for('product', product_id=product.id))
    elif request.method == 'GET':
        form.p_name.data = product.p_name
        form.description.data = product.description
        form.price.data = product.price
        form.picture.data = product.image
    return render_template('add_product.html', title='Update', form=form, legend='Update')


@app.route("/product/<int:product_id>/delete", methods=['GET'])
@admin_login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    #product = Product.query.filter_by(id=product_id).first()
    db.session.delete(product)
    db.session.commit()
    flash('Your product has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route('/products', methods=['GET'])
def get_all_products_api():
    products = Product.query.all()
    output = []
    for product in products:
        product_data = {}
        product_data['id'] = product.id
        product_data['username'] = product.p_name
        product_data['password'] = product.description
        product_data['admin'] = product.image
        product_data['admin'] = product.price
        output.append(product_data)
    return jsonify({'products': output})


@app.route('/products/<id>', methods=['GET'])
def get_one_product_api(id):
    product = Product.query.filter_by(id=id).first()
    if not product:
        return jsonify({'message': 'No product was found!'})
    product_data = {}
    product_data['id'] = product.id
    product_data['username'] = product.p_name
    product_data['password'] = product.description
    product_data['admin'] = product.image
    product_data['admin'] = product.price

    return jsonify({'user': product_data})


@app.route('/products', methods=['POST'])
def create_product_api():
    data = request.get_json()
    new_product = Product(p_name=data['p_name'], description=data['description'], price=data['price'])
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'New product was created!'})

@app.route('/products/<id>', methods=['PUT'])
def update_product_api(id):
    product = Product.query.filter_by(id=id).first()
    if not product:
        return jsonify({'message': 'No product was found!'})
    product.price = product.price * 1.1
    db.session.commit()
    return jsonify({'message': 'The product has been updated!'})


@app.route('/products/<id>',methods=['DELETE'])
def delete_product_api(id):
    product = Product.query.filter_by(id=id).first()
    
    if not product:
        return jsonify({'message': 'No product was found!'})
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'The product has been deleted!'})