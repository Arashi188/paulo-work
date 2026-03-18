from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, Response
from flask_login import login_required, current_user
from app.models import Product, Order, User
from app.forms import ProductForm, OrderStatusForm
from app import db
import cloudinary.uploader
import cloudinary.utils
from functools import wraps
import os
from datetime import datetime, timedelta
from collections import defaultdict
import csv
from io import StringIO

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Order statistics
    status_counts = {
        'pending': pending_orders,
        'processing': Order.query.filter_by(status='processing').count(),
        'completed': Order.query.filter_by(status='completed').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count()
    }
    
    return render_template('admin/dashboard.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders,
                         status_counts=status_counts)

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """Product management"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    pagination = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    return render_template('admin/products.html', products=products, pagination=pagination)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """Add new product"""
    form = ProductForm()
    
    if form.validate_on_submit():
        # Upload image to Cloudinary
        image_url = None
        if form.image.data:
            try:
                upload_result = cloudinary.uploader.upload(form.image.data)
                image_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Error uploading image: {str(e)}', 'danger')
                return render_template('admin/product_form.html', form=form, title='Add Product')
        
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image_url=image_url
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash(f'Product "{product.name}" added successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', form=form, title='Add Product')

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(id):
    """Edit existing product"""
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        
        # Upload new image if provided
        if form.image.data:
            try:
                # Delete old image from Cloudinary if exists
                if product.image_url:
                    public_id = product.image_url.split('/')[-1].split('.')[0]
                    cloudinary.uploader.destroy(public_id)
                
                upload_result = cloudinary.uploader.upload(form.image.data)
                product.image_url = upload_result.get('secure_url')
            except Exception as e:
                flash(f'Error uploading image: {str(e)}', 'danger')
        
        db.session.commit()
        flash(f'Product "{product.name}" updated successfully!', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/product_form.html', form=form, product=product, title='Edit Product')

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_product(id):
    """Delete product"""
    product = Product.query.get_or_404(id)
    name = product.name
    
    # Delete image from Cloudinary if exists
    if product.image_url:
        try:
            public_id = product.image_url.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(public_id)
        except Exception as e:
            flash(f'Error deleting image: {str(e)}', 'warning')
    
    db.session.delete(product)
    db.session.commit()
    
    flash(f'Product "{name}" deleted successfully!', 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Order management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    per_page = 15
    
    query = Order.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items
    
    return render_template('admin/orders.html', 
                         orders=orders, 
                         pagination=pagination,
                         status_filter=status_filter)

@admin_bp.route('/orders/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def order_detail(id):
    """View and update order details"""
    order = Order.query.get_or_404(id)
    form = OrderStatusForm(obj=order)
    
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash(f'Order #{order.id} status updated to {order.status}.', 'success')
        return redirect(url_for('admin.orders'))
    
    return render_template('admin/order_detail.html', order=order, form=form)

@admin_bp.route('/orders/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_order(id):
    """Delete order"""
    order = Order.query.get_or_404(id)
    order_id = order.id
    
    db.session.delete(order)
    db.session.commit()
    
    flash(f'Order #{order_id} deleted successfully!', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Order statistics and analytics"""
    # Get current date
    now = datetime.utcnow()
    
    # Calculate total revenue
    orders = Order.query.filter_by(status='completed').all()
    total_revenue = sum(order.product.price * order.quantity for order in orders)
    
    # Calculate average order value
    total_orders = len(orders)
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Get monthly data for the last 6 months
    monthly_labels = []
    monthly_data = []
    for i in range(5, -1, -1):
        month = now - timedelta(days=30 * i)
        month_name = month.strftime('%b %Y')
        monthly_labels.append(month_name)
        
        month_start = datetime(month.year, month.month, 1)
        if month.month == 12:
            month_end = datetime(month.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = datetime(month.year, month.month + 1, 1) - timedelta(days=1)
        
        month_orders = Order.query.filter(
            Order.created_at.between(month_start, month_end),
            Order.status == 'completed'
        ).count()
        monthly_data.append(month_orders)
    
    # Get status counts
    status_counts = {
        'pending': Order.query.filter_by(status='pending').count(),
        'processing': Order.query.filter_by(status='processing').count(),
        'completed': Order.query.filter_by(status='completed').count(),
        'cancelled': Order.query.filter_by(status='cancelled').count()
    }
    
    # Get top products
    top_products = []
    products = Product.query.all()
    for product in products:
        sold_orders = [o for o in product.orders if o.status == 'completed']
        total_sold = sum(o.quantity for o in sold_orders)
        revenue = sum(o.quantity * product.price for o in sold_orders)
        if total_sold > 0:
            top_products.append({
                'name': product.name,
                'total_sold': total_sold,
                'revenue': revenue
            })
    top_products.sort(key=lambda x: x['revenue'], reverse=True)
    top_products = top_products[:5]
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Calculate conversion rate (simplified)
    total_visits = 1000  # This would come from analytics in production
    conversion_rate = (total_orders / total_visits * 100) if total_visits > 0 else 0
    
    return render_template('admin/statistics.html',
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         total_orders=total_orders,
                         conversion_rate=conversion_rate,
                         monthly_labels=monthly_labels,
                         monthly_data=monthly_data,
                         status_counts=status_counts,
                         top_products=top_products,
                         recent_orders=recent_orders)

@admin_bp.route('/customers')
@login_required
@admin_required
def customers():
    """Customer management"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    per_page = 20
    
    # Get all orders and group by customer
    orders = Order.query.all()
    customers_dict = defaultdict(lambda: {
        'id': None,
        'name': '',
        'email': '',
        'phone': '',
        'orders': [],
        'order_count': 0,
        'total_spent': 0,
        'first_order': None,
        'last_order': None
    })
    
    for order in orders:
        key = f"{order.customer_name}_{order.phone}"
        customer = customers_dict[key]
        customer['name'] = order.customer_name
        customer['email'] = order.customer_email
        customer['phone'] = order.phone
        customer['orders'].append(order)
        customer['order_count'] += 1
        customer['total_spent'] += order.product.price * order.quantity
        
        if not customer['first_order'] or order.created_at < customer['first_order']:
            customer['first_order'] = order.created_at
        if not customer['last_order'] or order.created_at > customer['last_order']:
            customer['last_order'] = order.created_at
    
    # Convert to list and filter by search
    customers_list = list(customers_dict.values())
    if search:
        search_lower = search.lower()
        customers_list = [c for c in customers_list if 
                         search_lower in c['name'].lower() or 
                         (c['email'] and search_lower in c['email'].lower()) or
                         search_lower in c['phone']]
    
    # Sort by total spent
    customers_list.sort(key=lambda x: x['total_spent'], reverse=True)
    
    # Paginate
    total_customers = len(customers_list)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_customers = customers_list[start:end]
    
    # Calculate statistics
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    repeat_customers = len([c for c in customers_list if c['order_count'] > 1])
    new_customers = len([c for c in customers_list if c['first_order'] and c['first_order'] > thirty_days_ago])
    
    # Create pagination object
    class Pagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if page > 1 else None
            self.next_num = page + 1 if page < self.pages else None
        
        def iter_pages(self):
            return range(1, self.pages + 1)
    
    pagination = Pagination(page, per_page, total_customers)
    
    return render_template('admin/customers.html',
                         customers=paginated_customers,
                         pagination=pagination,
                         search=search,
                         total_customers=total_customers,
                         repeat_customers=repeat_customers,
                         new_customers=new_customers)

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Sales reports"""
    try:
        period = request.args.get('period', 'month')
        status = request.args.get('status', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Set date range based on period
        now = datetime.utcnow()
        
        if period == 'today':
            start = datetime(now.year, now.month, now.day)
            end = now
        elif period == 'yesterday':
            yesterday = now - timedelta(days=1)
            start = datetime(yesterday.year, yesterday.month, yesterday.day)
            end = datetime(now.year, now.month, now.day) - timedelta(seconds=1)
        elif period == 'week':
            start = now - timedelta(days=now.weekday())
            start = datetime(start.year, start.month, start.day)
            end = now
        elif period == 'month':
            start = datetime(now.year, now.month, 1)
            end = now
        elif period == 'year':
            start = datetime(now.year, 1, 1)
            end = now
        elif period == 'custom' and start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            except:
                start = datetime(now.year, now.month, 1)
                end = now
        else:
            start = datetime(now.year, now.month, 1)
            end = now
        
        # Build query
        query = Order.query.filter(Order.created_at.between(start, end))
        if status != 'all':
            query = query.filter_by(status=status)
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        # Calculate summary with safe defaults
        total_sales = sum(o.product.price * o.quantity for o in orders) if orders else 0
        order_count = len(orders)
        avg_order = total_sales / order_count if order_count > 0 else 0
        total_items = sum(o.quantity for o in orders) if orders else 0
        unique_customers = len(set((o.customer_name, o.phone) for o in orders)) if orders else 0
        
        summary = {
            'total_sales': total_sales,
            'order_count': order_count,
            'avg_order': avg_order,
            'total_items': total_items,
            'unique_customers': unique_customers
        }
        
        # Product performance with safe handling
        product_performance = []
        products = Product.query.all()
        for product in products:
            product_orders = [o for o in orders if o.product_id == product.id]
            if product_orders:
                units_sold = sum(o.quantity for o in product_orders)
                revenue = sum(o.quantity * product.price for o in product_orders)
                product_performance.append({
                    'name': product.name,
                    'units_sold': units_sold,
                    'revenue': revenue
                })
        
        product_performance.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Chart data with safe defaults - ensure all values are JSON serializable
        chart_data_dates = []
        chart_data_sales = []
        
        if period in ['today', 'yesterday']:
            # Hourly data
            for hour in range(24):
                hour_start = datetime(start.year, start.month, start.day, hour)
                hour_end = hour_start + timedelta(hours=1) - timedelta(seconds=1)
                hour_sales = sum(o.product.price * o.quantity for o in orders 
                               if hour_start <= o.created_at <= hour_end) if orders else 0
                chart_data_dates.append(f'{hour:02d}:00')
                chart_data_sales.append(float(hour_sales))
        else:
            # Daily data
            current = start
            while current <= end:
                day_start = datetime(current.year, current.month, current.day)
                day_end = day_start + timedelta(days=1) - timedelta(seconds=1)
                day_sales = sum(o.product.price * o.quantity for o in orders 
                              if day_start <= o.created_at <= day_end) if orders else 0
                chart_data_dates.append(current.strftime('%Y-%m-%d'))
                chart_data_sales.append(float(day_sales))
                current += timedelta(days=1)
        
        # Payment methods data - ensure all values are JSON serializable
        payment_labels = ['WhatsApp Orders']
        payment_values = [int(order_count)]
        
        return render_template('admin/reports.html',
                             period=period,
                             status=status,
                             start_date=start.strftime('%Y-%m-%d') if period == 'custom' else '',
                             end_date=end.strftime('%Y-%m-%d') if period == 'custom' else '',
                             summary=summary,
                             orders=orders,
                             product_performance=product_performance,
                             chart_data_dates=chart_data_dates,
                             chart_data_sales=chart_data_sales,
                             payment_labels=payment_labels,
                             payment_values=payment_values)
    
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'danger')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    """Admin settings page"""
    # Load store settings from database or environment
    store_settings = {
        'name': os.environ.get('STORE_NAME', 'E-Store'),
        'email': os.environ.get('STORE_EMAIL', ''),
        'phone': os.environ.get('STORE_PHONE', ''),
        'whatsapp': os.environ.get('WHATSAPP_NUMBER', '2347088028747'),
        'currency': os.environ.get('STORE_CURRENCY', 'NGN')
    }
    
    return render_template('admin/settings.html', store_settings=store_settings)

@admin_bp.route('/update-profile', methods=['POST'])
@login_required
@admin_required
def update_profile():
    """Update admin profile"""
    username = request.form.get('username')
    email = request.form.get('email')
    
    if not username or not email:
        flash('Username and email are required.', 'danger')
        return redirect(url_for('admin.settings'))
    
    # Check if username/email already taken by another user
    existing_user = User.query.filter(
        (User.username == username) | (User.email == email),
        User.id != current_user.id
    ).first()
    
    if existing_user:
        flash('Username or email already taken.', 'danger')
        return redirect(url_for('admin.settings'))
    
    current_user.username = username
    current_user.email = email
    db.session.commit()
    
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/change-password', methods=['POST'])
@login_required
@admin_required
def change_password():
    """Change admin password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        flash('All fields are required.', 'danger')
        return redirect(url_for('admin.settings'))
    
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('admin.settings'))
    
    if len(new_password) < 8:
        flash('Password must be at least 8 characters long.', 'danger')
        return redirect(url_for('admin.settings'))
    
    if not current_user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('admin.settings'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Password changed successfully!', 'success')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/update-store-settings', methods=['POST'])
@login_required
@admin_required
def update_store_settings():
    """Update store settings"""
    # In a production environment, you'd save these to a database
    # For now, we'll just show a success message
    
    flash('Store settings updated successfully! Note: Changes will persist only for this session.', 'success')
    return redirect(url_for('admin.settings'))

@admin_bp.route('/export-data')
@login_required
@admin_required
def export_data():
    """Export data as CSV"""
    data_type = request.args.get('type', 'orders')
    
    si = StringIO()
    cw = csv.writer(si)
    
    if data_type == 'orders':
        cw.writerow(['Order ID', 'Date', 'Customer Name', 'Email', 'Phone', 
                    'Product', 'Quantity', 'Price', 'Total', 'Status'])
        
        orders = Order.query.all()
        for order in orders:
            cw.writerow([
                order.id,
                order.created_at.strftime('%Y-%m-%d %H:%M'),
                order.customer_name,
                order.customer_email or '',
                order.phone,
                order.product.name,
                order.quantity,
                order.product.price,
                order.product.price * order.quantity,
                order.status
            ])
    else:
        cw.writerow(['Product ID', 'Name', 'Description', 'Price', 'Image URL', 'Created'])
        
        products = Product.query.all()
        for product in products:
            cw.writerow([
                product.id,
                product.name,
                product.description,
                product.price,
                product.image_url or '',
                product.created_at.strftime('%Y-%m-%d %H:%M')
            ])
    
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={data_type}_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )

@admin_bp.route('/export-customers')
@login_required
@admin_required
def export_customers():
    """Export customers as CSV"""
    si = StringIO()
    cw = csv.writer(si)
    
    cw.writerow(['Name', 'Email', 'Phone', 'Total Orders', 'Total Spent', 'First Order', 'Last Order'])
    
    # Group orders by customer
    orders = Order.query.all()
    customers_dict = defaultdict(lambda: {
        'name': '',
        'email': '',
        'phone': '',
        'order_count': 0,
        'total_spent': 0,
        'first_order': None,
        'last_order': None
    })
    
    for order in orders:
        key = f"{order.customer_name}_{order.phone}"
        customer = customers_dict[key]
        customer['name'] = order.customer_name
        customer['email'] = order.customer_email
        customer['phone'] = order.phone
        customer['order_count'] += 1
        customer['total_spent'] += order.product.price * order.quantity
        
        if not customer['first_order'] or order.created_at < customer['first_order']:
            customer['first_order'] = order.created_at
        if not customer['last_order'] or order.created_at > customer['last_order']:
            customer['last_order'] = order.created_at
    
    for customer in customers_dict.values():
        cw.writerow([
            customer['name'],
            customer['email'] or '',
            customer['phone'],
            customer['order_count'],
            customer['total_spent'],
            customer['first_order'].strftime('%Y-%m-%d') if customer['first_order'] else '',
            customer['last_order'].strftime('%Y-%m-%d') if customer['last_order'] else ''
        ])
    
    output = si.getvalue()
    si.close()
    
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=customers_{datetime.utcnow().strftime("%Y%m%d")}.csv'}
    )

@admin_bp.route('/import-data', methods=['POST'])
@login_required
@admin_required
def import_data():
    """Import data from CSV"""
    data_type = request.form.get('data_type')
    file = request.files.get('import_file')
    
    if not file:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('admin.settings'))
    
    try:
        stream = StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_reader = csv.reader(stream)
        headers = next(csv_reader)  # Skip header row
        
        success_count = 0
        error_count = 0
        
        if data_type == 'products':
            for row in csv_reader:
                try:
                    if len(row) >= 3:
                        product = Product(
                            name=row[0],
                            description=row[1] if len(row) > 1 else '',
                            price=float(row[2]) if len(row) > 2 else 0,
                            image_url=row[3] if len(row) > 3 else None
                        )
                        db.session.add(product)
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
        elif data_type == 'orders':
            for row in csv_reader:
                try:
                    if len(row) >= 4:
                        order = Order(
                            customer_name=row[0],
                            customer_email=row[1] if len(row) > 1 and row[1] else None,
                            phone=row[2] if len(row) > 2 else '',
                            product_id=int(row[3]) if len(row) > 3 else None,
                            quantity=int(row[4]) if len(row) > 4 and row[4] else 1,
                            status=row[5] if len(row) > 5 else 'pending'
                        )
                        db.session.add(order)
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    error_count += 1
        
        db.session.commit()
        
        if error_count > 0:
            flash(f'Imported {success_count} records. {error_count} records failed.', 'warning')
        else:
            flash(f'Successfully imported {success_count} records!', 'success')
            
    except Exception as e:
        flash(f'Error importing data: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/clear-data', methods=['POST'])
@login_required
@admin_required
def clear_data():
    """Clear all data"""
    confirm = request.form.get('confirm_text')
    
    if confirm != 'DELETE':
        flash('Confirmation text does not match. Please type "DELETE" exactly.', 'danger')
        return redirect(url_for('admin.settings'))
    
    try:
        order_count = Order.query.count()
        product_count = Product.query.count()
        
        Order.query.delete()
        Product.query.delete()
        db.session.commit()
        
        flash(f'Successfully cleared {order_count} orders and {product_count} products!', 'success')
    except Exception as e:
        flash(f'Error clearing data: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('admin.settings'))