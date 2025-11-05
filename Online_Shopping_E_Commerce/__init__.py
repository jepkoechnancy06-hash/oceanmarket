"""
The flask application package.
"""

from flask import Flask, session
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year for static assets

@app.template_filter('kes')
def kes(value):
    try:
        return f"KSh {float(value):,.0f}"
    except (ValueError, TypeError):
        return "KSh -"

@app.context_processor
def inject_globals():
    cart = session.get('cart', {}) if isinstance(session.get('cart', {}), dict) else {}
    cart_count = sum(cart.values()) if cart else 0
    return {
        'cart_count': cart_count,
        'year': datetime.now().year,
        'GA4_ID': os.environ.get('GA4_ID'),
        'META_PIXEL_ID': os.environ.get('META_PIXEL_ID'),
        'SITE_NAME': os.environ.get('SITE_NAME', 'Ocean Market'),
        'SITE_URL': os.environ.get('SITE_URL', ''),
    }

import Online_Shopping_E_Commerce.views
