from flask import Blueprint, session, jsonify, request, render_template, redirect, url_for, flash
from models import Product, db, Order, OrderItem
from flask_login import login_required, current_user
from forms import CheckoutForm
from mpesa import MPesa
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    orders = db.relationship('Order', backref='customer', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image = db.Column(db.String(200))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(30), default='pending')  # pending, dispatched, delivered
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')

cart_bp = Blueprint('cart', __name__, template_folder='../templates/cart')

def _get_cart():
    return session.setdefault('cart', {})

@cart_bp.route('/')
@login_required
def view_cart():
    cart = _get_cart()
    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            subtotal = p.price * qty
            items.append({'product': p, 'qty': qty, 'subtotal': subtotal})
            total += subtotal
    return render_template('cart.html', items=items, total=total)

@cart_bp.route('/add', methods=['POST'])
def add_item():
    data = request.get_json() or request.form
    pid = str(data.get('product_id'))
    qty = int(data.get('quantity', 1))
    cart = _get_cart()
    cart[pid] = cart.get(pid, 0) + qty
    session.modified = True
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@cart_bp.route('/update', methods=['POST'])
def update_item():
    data = request.get_json() or request.form
    pid = str(data.get('product_id'))
    qty = int(data.get('quantity', 0))
    cart = _get_cart()
    if qty <= 0:
        cart.pop(pid, None)
    else:
        cart[pid] = qty
    session.modified = True
    return jsonify({'success': True, 'cart_count': sum(cart.values())})

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    form = CheckoutForm()
    cart = _get_cart()
    if not cart:
        flash('Cart is empty', 'warning')
        return redirect(url_for('products.list_products'))

    items = []
    total = 0.0
    for pid, qty in cart.items():
        p = Product.query.get(int(pid))
        if p:
            items.append((p, qty))
            total += p.price * qty

    if form.validate_on_submit():
        order = Order(user_id=current_user.id, status='pending', total_amount=total)
        db.session.add(order)
        db.session.flush()
        for p, qty in items:
            oi = OrderItem(order_id=order.id, product_id=p.id, quantity=qty, price=p.price)
            db.session.add(oi)
            p.stock = max(p.stock - qty, 0)
        db.session.commit()
        # initiate MPesa payment (sandbox stub)
        mp = MPesa(MPesa._config if hasattr(MPesa, '_config') else {})
        # Note: MPesa usage in live app requires proper callback & config handling
        session.pop('cart', None)
        return render_template('order_confirmation.html', order=order)

    return render_template('checkout.html', form=form, items=items, total=total)