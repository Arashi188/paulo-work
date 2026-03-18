# force_system_dns.py
import socket
import subprocess
import os

print("Forcing Python to use system DNS...")
print("=" * 60)

# Get system DNS servers
try:
    result = subprocess.run(['nslookup', 'google.com'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    for line in lines:
        if 'Address:' in line and '#' not in line:
            dns_server = line.split('Address:')[1].strip()
            print(f"System DNS server: {dns_server}")
            break
except:
    print("Could not detect system DNS")

# Test with different DNS servers
dns_servers = [
    '8.8.8.8',        # Google DNS
    '1.1.1.1',        # Cloudflare DNS
    '208.67.222.222', # OpenDNS
]

hostname = "db.jhnpanznxoanclyrzvqx.supabase.co"

for dns in dns_servers:
    print(f"\nTesting with DNS: {dns}")
    
    # Set environment variable for some resolvers
    os.environ['RES_OPTIONS'] = f'ndots:0 timeout:2 attempts:2'
    
    try:
        # Try to resolve using custom DNS
        import subprocess
        result = subprocess.run(['nslookup', hostname, dns], capture_output=True, text=True)
        if 'Address:' in result.stdout and 'Name:' in result.stdout:
            print(f"✅ nslookup with {dns} succeeded:")
            for line in result.stdout.split('\n'):
                if 'Address:' in line and '#' not in line:
                    print(f"   {line.strip()}")
        else:
            print(f"❌ nslookup with {dns} failed")
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)