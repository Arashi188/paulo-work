# test_python_dns.py
import socket
import dns.resolver  # You may need to install: pip install dnspython

print("Testing DNS resolution from Python...")
print("=" * 60)

hostname = "db.jhnpanznxoanclyrzvqx.supabase.co"

# Method 1: Using socket.gethostbyname
try:
    ip = socket.gethostbyname(hostname)
    print(f"✅ socket.gethostbyname: {ip}")
except Exception as e:
    print(f"❌ socket.gethostbyname failed: {e}")

# Method 2: Using socket.getaddrinfo
try:
    addrinfo = socket.getaddrinfo(hostname, 5432, socket.AF_UNSPEC, socket.SOCK_STREAM)
    print(f"✅ socket.getaddrinfo found {len(addrinfo)} addresses:")
    for addr in addrinfo:
        print(f"   - {addr[4][0]}")
except Exception as e:
    print(f"❌ socket.getaddrinfo failed: {e}")

# Method 3: Using dnspython if available
try:
    import dns.resolver
    answers = dns.resolver.resolve(hostname, 'A')
    print(f"✅ dnspython found {len(answers)} IPv4 addresses:")
    for rdata in answers:
        print(f"   - {rdata.address}")
except ImportError:
    print("⚠️ dnspython not installed. Install with: pip install dnspython")
except Exception as e:
    print(f"❌ dnspython failed: {e}")

print("=" * 60)