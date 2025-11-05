"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import render_template, request, redirect, url_for, session, flash, make_response
from Online_Shopping_E_Commerce import app

@app.route('/')
@app.route('/home')
def home():
    """Renders the home page."""
    return render_template(
        'index.html',
        title='Home Page',
        year=datetime.now().year,
    )

@app.route('/contact')
def contact():
    """Renders the contact page."""
    return render_template(
        'contact.html',
        title='Contact',
        year=datetime.now().year,
        message='Your contact page.'
    )

@app.route('/about')
def about():
    """Renders the about page."""
    return render_template(
        'about.html',
        title='About',
        year=datetime.now().year,
        message='Your application description page.'
    )

# Policy pages
@app.route('/privacy')
def privacy():
    return render_template('privacy.html', title='Privacy Policy')

@app.route('/terms')
def terms():
    return render_template('terms.html', title='Terms & Conditions')

@app.route('/returns')
def returns():
    return render_template('returns.html', title='Returns Policy')

def _catalog():
    return [
        {'id': 1, 'name': 'Wireless Headphones', 'price': 3999, 'category': 'Electronics', 'rating': 4.5},
        {'id': 2, 'name': 'Sneakers', 'price': 2999, 'category': 'Fashion', 'rating': 4.2},
        {'id': 3, 'name': 'Blender', 'price': 4599, 'category': 'Home & Living', 'rating': 4.0},
        {'id': 4, 'name': 'Smartphone', 'price': 19999, 'category': 'Electronics', 'rating': 4.7},
        {'id': 5, 'name': 'Backpack', 'price': 1990, 'category': 'Fashion', 'rating': 4.1},
        {'id': 6, 'name': 'Electric Kettle', 'price': 2499, 'category': 'Home & Living', 'rating': 4.3},
    ]

# Product Listing Page (PLP) — stubbed data with simple filters/sorting
@app.route('/products')
def products():
    # Stub dataset until real models are wired
    items = list(_catalog())

    # Query params: q (search), cat (category), sort (price_asc|price_desc|new|rating)
    q = request.args.get('q', '').strip().lower()
    cat = request.args.get('cat', '').strip()
    sort = request.args.get('sort', 'new')

    filtered = [it for it in items if (q in it['name'].lower()) and (cat == '' or it['category'] == cat)]

    if sort == 'price_asc':
        filtered.sort(key=lambda x: x['price'])
    elif sort == 'price_desc':
        filtered.sort(key=lambda x: -x['price'])
    elif sort == 'rating':
        filtered.sort(key=lambda x: -x['rating'])
    else:
        filtered.sort(key=lambda x: -x['id'])  # newest first

    categories = ['Electronics', 'Fashion', 'Home & Living']
    return render_template('products.html', title='Products', items=filtered, q=q, cat=cat, sort=sort, categories=categories)


# Product Detail Page (PDP) — stub
@app.route('/product/<int:pid>')
def product_detail(pid):
    mock = {
        1: {'id': 1, 'name': 'Wireless Headphones', 'price': 3999, 'category': 'Electronics', 'rating': 4.5, 'desc': 'Comfortable, long battery life.'},
        2: {'id': 2, 'name': 'Sneakers', 'price': 2999, 'category': 'Fashion', 'rating': 4.2, 'desc': 'Lightweight everyday sneakers.'},
        3: {'id': 3, 'name': 'Blender', 'price': 4599, 'category': 'Home & Living', 'rating': 4.0, 'desc': 'Powerful motor, easy clean jar.'},
        4: {'id': 4, 'name': 'Smartphone', 'price': 19999, 'category': 'Electronics', 'rating': 4.7, 'desc': 'Fast, great camera, long-lasting battery.'},
        5: {'id': 5, 'name': 'Backpack', 'price': 1990, 'category': 'Fashion', 'rating': 4.1, 'desc': 'Durable, multiple compartments.'},
        6: {'id': 6, 'name': 'Electric Kettle', 'price': 2499, 'category': 'Home & Living', 'rating': 4.3, 'desc': 'Auto shut-off, 1.7L capacity.'},
    }
    product = mock.get(pid)
    if not product:
        return render_template('product_detail.html', title='Product Not Found', product=None), 404
    related = [p for k, p in mock.items() if k != pid and p['category'] == product['category']][:4]
    return render_template('product_detail.html', title=product['name'], product=product, related=related)


# -----------------
# Cart & Checkout
# -----------------

def _get_cart():
    cart = session.get('cart') or {}
    if not isinstance(cart, dict):
        cart = {}
    return cart

def _set_cart(cart):
    session['cart'] = cart
    session.modified = True

def _get_product(pid):
    for p in _catalog():
        if p['id'] == pid:
            return p
    return None

@app.route('/cart')
def cart():
    cart = _get_cart()
    items = []
    subtotal = 0
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except (TypeError, ValueError):
            continue
        p = _get_product(pid)
        if p:
            line_total = p['price'] * int(qty)
            subtotal += line_total
            items.append({'product': p, 'qty': int(qty), 'line_total': line_total})
    return render_template('cart.html', title='Your Cart', items=items, subtotal=subtotal)

@app.route('/cart/add/<int:pid>')
def cart_add(pid):
    if not _get_product(pid):
        flash('Product not found', 'warning')
        return redirect(url_for('products'))
    cart = _get_cart()
    key = str(pid)
    cart[key] = int(cart.get(key, 0)) + 1
    _set_cart(cart)
    flash('Added to cart', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update', methods=['POST'])
def cart_update():
    pid = request.form.get('pid')
    qty = request.form.get('qty')
    if not pid:
        return redirect(url_for('cart'))
    cart = _get_cart()
    try:
        q = max(0, int(qty))
    except (TypeError, ValueError):
        q = 1
    if q == 0:
        cart.pop(pid, None)
    else:
        cart[pid] = q
    _set_cart(cart)
    return redirect(url_for('cart'))

KENYA_COUNTIES = [
    'Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Kiambu', 'Machakos', 'Kajiado', 'Uasin Gishu', 'Nyeri', 'Garissa'
]

def compute_shipping(county: str, option: str) -> int:
    county = (county or '').strip()
    option = (option or '').strip()
    base = 200 if county == 'Nairobi' else 400
    if option == 'pickup':
        return 0
    if option == 'same_day' and county == 'Nairobi':
        return 300
    return base

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = _get_cart()
    if not cart:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products'))

    # Build items and subtotal
    items = []
    subtotal = 0
    for pid_str, qty in cart.items():
        pid = int(pid_str)
        p = _get_product(pid)
        if p:
            lt = p['price'] * int(qty)
            subtotal += lt
            items.append({'product': p, 'qty': int(qty), 'line_total': lt})

    form = {
        'name': request.form.get('name', ''),
        'phone': request.form.get('phone', ''),
        'county': request.form.get('county', 'Nairobi'),
        'address': request.form.get('address', ''),
        'delivery': request.form.get('delivery', 'standard'),
        'payment': request.form.get('payment', 'mpesa'),
    }

    shipping = compute_shipping(form['county'], form['delivery'])
    total = subtotal + shipping

    if request.method == 'POST':
        # Minimal validation
        if not form['name'] or not form['phone']:
            flash('Please enter your name and phone number', 'warning')
            return render_template('checkout.html', title='Checkout', items=items, subtotal=subtotal, shipping=shipping, total=total, counties=KENYA_COUNTIES, form=form)

        # MPesa stub: generate a fake reference and mark as paid
        if form['payment'] == 'mpesa':
            ref = 'MPESA-' + datetime.now().strftime('%Y%m%d%H%M%S')
            status = 'paid'
        else:
            ref = 'COD-' + datetime.now().strftime('%Y%m%d%H%M%S')
            status = 'pending'

        order = {
            'order_number': datetime.now().strftime('OM-%Y%m%d-%H%M%S'),
            'name': form['name'],
            'phone': form['phone'],
            'county': form['county'],
            'address': form['address'],
            'delivery': form['delivery'],
            'payment': form['payment'],
            'payment_ref': ref,
            'status': status,
            'items': items,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
        }

        # Clear cart
        session.pop('cart', None)
        session.modified = True
        return render_template('order_confirmation.html', title='Order Confirmed', order=order)

    # GET request or failed POST validation renders checkout
    return render_template('checkout.html', title='Checkout', items=items, subtotal=subtotal, shipping=shipping, total=total, counties=KENYA_COUNTIES, form=form)

# SEO assets
@app.route('/sitemap.xml')
def sitemap():
    base = request.url_root.rstrip('/')
    urls = [
        ('/', 'daily'),
        ('/products', 'daily'),
        ('/about', 'monthly'),
        ('/contact', 'monthly'),
        ('/privacy', 'yearly'),
        ('/terms', 'yearly'),
        ('/returns', 'yearly'),
    ]
    # Include PDP URLs from stub catalog
    for p in _catalog():
        urls.append((f"/product/{p['id']}", 'weekly'))
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for path, freq in urls:
        xml_parts.append(f'<url><loc>{base}{path}</loc><changefreq>{freq}</changefreq></url>')
    xml_parts.append('</urlset>')
    resp = make_response('\n'.join(xml_parts))
    resp.headers['Content-Type'] = 'application/xml'
    return resp

@app.route('/robots.txt')
def robots():
    base = request.url_root.rstrip('/')
    content = f"""
User-agent: *
Allow: /
Sitemap: {base}/sitemap.xml
""".strip()
    resp = make_response(content)
    resp.headers['Content-Type'] = 'text/plain'
    return resp
