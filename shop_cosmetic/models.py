from shop_cosmetic import db, login_manager
from flask_login import UserMixin
from wtforms import widgets, TextAreaField


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


def add_children(parent):
    p = session.query(Parent).filter(Parent.id == p1.id).all()
    if len(p) == 0:
        db.session.add(p1)
        db.session.commit()
    else:
        update_children = parent.children[:]
        parent.chlidren = []
        for c in updateChildren:
            c.parent_gid = parent.gid

        db.session.add_all(updateChildren)
        db.session.commit()


class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	admin = db.Column(db.Boolean())

	def __init__(self, username, password, email, admin=False):
		self.username = username
		self.admin = admin
		self.password = password
		self.email = email

	def is_admin(self):
		return self.admin

	def __repr__(self):
		return f"User('{self.username}', '{self.email}')"


class Product(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	p_name = db.Column(db.String(100), nullable=False)
	description = db.Column(db.UnicodeText, nullable=False)
	image = db.Column(db.String(20), nullable=False, default='default.jpg')
	price = db.Column(db.Float, nullable=False)

	def __repr__(self):
		return f"Product('{self.p_name}','{self.description}','{self.price}','{self.image}')"


association_table = db.Table('cart_products', db.Model.metadata,
    db.Column('cart_id', db.Integer, db.ForeignKey('cart.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'))
)    


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)
    user = db.relationship('User', backref='user', lazy=True, uselist=False)
    products = db.relationship('Product', secondary=association_table, backref='products', lazy=True)
    ordered = db.Column(db.Boolean, default=False)
    
    @property
    def total_price(self):
        return sum([i.price for i in self.products])
    
    def __repr__(self):
        return '\n'.join([i.__repr__ for i in self.products])


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'),
        nullable=False)
    cart = db.relationship('Cart', backref='cart', lazy=True, uselist=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    shipping_address = db.Column(db.String(100), nullable=False)
    closed = db.Column(db.Boolean, default=False)
