# test_reports.py
from app import create_app
from app.models import Order, Product
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    print("Testing Reports Function...")
    print("=" * 50)
    
    # Check if there are any orders
    orders = Order.query.all()
    print(f"Total orders in database: {len(orders)}")
    
    if orders:
        print("\nSample order data:")
        for order in orders[:3]:
            print(f"  Order #{order.id}: {order.customer_name} - {order.product.name} - {order.status}")
    else:
        print("\nNo orders found! Create some test orders first.")
    
    # Check products
    products = Product.query.all()
    print(f"\nTotal products: {len(products)}")
    
    print("\n" + "=" * 50)