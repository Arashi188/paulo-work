from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Product, Order, HeroSlide
from app.forms import OrderForm
from app import db
import cloudinary.uploader
import cloudinary.utils
import os
from urllib.parse import quote

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage with featured products and hero slideshow"""
    try:
        featured_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    except:
        featured_products = []
    
    # Get active hero slides ordered by the 'order' field
    try:
        hero_slides = HeroSlide.query.filter_by(is_active=True).order_by(HeroSlide.order).all()
    except:
        hero_slides = []
    
    # If no slides in database, use default slides
    if not hero_slides:
        hero_slides = [
            {
                'title': 'Welcome to E-Store',
                'subtitle': 'Discover amazing products at unbeatable prices. Shop now and enjoy exclusive deals!',
                'button_text': 'Shop Now',
                'button_link': 'main.products',
                'image_url': url_for('static', filename='images/Slide 1.jpg')
            },
            {
                'title': 'New Arrivals',
                'subtitle': 'Check out our latest products with special introductory prices!',
                'button_text': 'View New Items',
                'button_link': 'main.products',
                'image_url': url_for('static', filename='images/Slide 2.jpg')
            },
            {
                'title': 'Special Offers',
                'subtitle': 'Get up to 30% off on selected items. Limited time only!',
                'button_text': 'Shop Sale',
                'button_link': 'main.products',
                'image_url': url_for('static', filename='images/Slide 3.jpg')
            }
        ]
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         hero_slides=hero_slides)

@main_bp.route('/products')
def products():
    """Product listing page with search and pagination"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 9
    
    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') | Product.description.ilike(f'%{search}%'))
    
    pagination = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    return render_template('products.html', 
                         products=products, 
                         pagination=pagination,
                         search=search)

@main_bp.route('/product/<int:id>')
def product_detail(id):
    """Product detail page"""
    product = Product.query.get_or_404(id)
    form = OrderForm()
    return render_template('product.html', product=product, form=form)

@main_bp.route('/order/<int:product_id>', methods=['POST'])
def create_order(product_id):
    """Create order and redirect to WhatsApp"""
    product = Product.query.get_or_404(product_id)
    form = OrderForm()
    
    if form.validate_on_submit():
        # Create order in database
        order = Order(
            product_id=product.id,
            customer_name=form.customer_name.data,
            customer_email=form.customer_email.data,
            phone=form.phone.data,
            quantity=form.quantity.data,
            status='pending'
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Store order in session for cart
        if 'cart' not in session:
            session['cart'] = []
        
        # Flash success message
        flash(f'Order #{order.id} created successfully! You will be redirected to WhatsApp.', 'success')
        
        # Prepare WhatsApp message
        product_url = url_for('main.product_detail', id=product.id, _external=True)
        message = f"Hello, I want to order this product: {product.name} (₦{product.price:,.2f}). My order ID is {order.id}. Product link: {product_url}"
        
        # URL encode the message
        encoded_message = quote(message)
        
        # Redirect to WhatsApp
        whatsapp_number = os.environ.get('WHATSAPP_NUMBER', '2347088028747')
        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
        return redirect(whatsapp_url)
    
    # If form validation fails
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'danger')
    
    return redirect(url_for('main.product_detail', id=product_id))

@main_bp.route('/cart')
def view_cart():
    """View shopping cart"""
    return render_template('cart.html')

@main_bp.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    quantity = request.form.get('quantity', 1, type=int)
    
    if 'cart' not in session:
        session['cart'] = []
    
    # Check if product already in cart
    cart_item = None
    for item in session['cart']:
        if item['product_id'] == product_id:
            cart_item = item
            break
    
    if cart_item:
        cart_item['quantity'] += quantity
    else:
        session['cart'].append({
            'product_id': product_id,
            'name': product.name,
            'price': float(product.price),
            'quantity': quantity,
            'image_url': product.image_url
        })
    
    session.modified = True
    flash(f'{product.name} added to cart!', 'success')
    return redirect(url_for('main.view_cart'))

@main_bp.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    """Remove item from cart"""
    if 'cart' in session:
        session['cart'] = [item for item in session['cart'] if item['product_id'] != product_id]
        session.modified = True
        flash('Item removed from cart.', 'success')
    return redirect(url_for('main.view_cart'))

@main_bp.route('/checkout')
def checkout():
    """Checkout page"""
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('main.products'))
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('checkout.html', cart_items=cart_items, total=total)

@main_bp.route('/place-order', methods=['POST'])
def place_order():
    """Place order from cart"""
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty!', 'warning')
        return redirect(url_for('main.products'))
    
    name = request.form.get('customer_name')
    email = request.form.get('customer_email')
    phone = request.form.get('phone')
    
    if not name or not phone:
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('main.checkout'))
    
    # Create orders for each cart item
    orders = []
    for item in cart_items:
        order = Order(
            product_id=item['product_id'],
            customer_name=name,
            customer_email=email,
            phone=phone,
            quantity=item['quantity'],
            status='pending'
        )
        db.session.add(order)
        orders.append(order)
    
    db.session.commit()
    
    # Clear cart
    session.pop('cart', None)
    
    # Prepare WhatsApp message for first item (or combine all)
    first_item = cart_items[0]
    product = Product.query.get(first_item['product_id'])
    product_url = url_for('main.product_detail', id=product.id, _external=True)
    
    if len(cart_items) > 1:
        message = f"Hello, I want to order multiple items. My first item is: {product.name} (₦{product.price:,.2f}). Total items: {len(cart_items)}. Order IDs: {', '.join([str(o.id) for o in orders])}. Product link: {product_url}"
    else:
        message = f"Hello, I want to order this product: {product.name} (₦{product.price:,.2f}). My order ID is {orders[0].id}. Product link: {product_url}"
    
    encoded_message = quote(message)
    whatsapp_number = os.environ.get('WHATSAPP_NUMBER', '2347088028747')
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
    
    flash(f'Orders placed successfully! You will be redirected to WhatsApp.', 'success')
    return redirect(whatsapp_url)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        # Here you would typically send an email or save to database
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # For now, just show a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@main_bp.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main_bp.route('/faq')
def faq():
    """FAQ page"""
    return render_template('faq.html')

@main_bp.route('/terms')
def terms():
    """Terms and conditions page"""
    return render_template('terms.html')

@main_bp.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@main_bp.route('/shipping')
def shipping():
    """Shipping information page"""
    return render_template('shipping.html')

@main_bp.route('/returns')
def returns():
    """Returns policy page"""
    return render_template('returns.html')

@main_bp.route('/sitemap')
def sitemap():
    """Sitemap page"""
    # Get all products for sitemap
    try:
        all_products = Product.query.order_by(Product.name).all()
    except:
        all_products = []
    return render_template('sitemap.html', all_products=all_products)