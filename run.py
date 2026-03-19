# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("Starting E-Store Application")
    print("=" * 50)
    print("\n📍 Local URL: http://127.0.0.1:5000")
    print("📍 Admin URL: http://127.0.0.1:5000/admin/login")
    print("\nPress CTRL+C to stop the server\n")
    app.run(debug=True, host='127.0.0.1', port=5000)