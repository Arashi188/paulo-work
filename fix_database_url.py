# fix_database_url.py
import os

# Your correct credentials
correct_host = "db.jhnpanznxoanclyrzvqx.supabase.co"
password = "mFxwM5qnfYFABSD9"
port = "5432"
database = "postgres"
user = "postgres"

# Construct the correct URL
correct_url = f"postgresql://{user}:{password}@{correct_host}:{port}/{database}"

print("=" * 50)
print("DATABASE URL FIX")
print("=" * 50)
print(f"\n✅ Correct Database URL:")
print(correct_url)
print("\n")

# Check config.py
config_path = "config.py"
if os.path.exists(config_path):
    with open(config_path, 'r') as f:
        content = f.read()
    
    if "jhnpanznxconcylryzvqx" in content:
        print("❌ Found incorrect hostname in config.py")
        print("Please update it manually with the correct URL above")
    else:
        print("✅ config.py looks good")

# Check .env file
env_path = ".env"
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
    
    if "jhnpanznxconcylryzvqx" in content:
        print("❌ Found incorrect hostname in .env file")
        print("Please update it manually with the correct URL above")
    else:
        print("✅ .env file looks good")

print("\n" + "=" * 50)
print("Copy this correct URL:")
print(correct_url)
print("=" * 50)

# Optional: Auto-fix config.py
fix = input("\nAuto-fix config.py? (y/n): ")
if fix.lower() == 'y':
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace incorrect URL with correct one
        import re
        pattern = r"postgresql://[^']+"
        replacement = correct_url
        new_content = re.sub(pattern, f"'{replacement}'", content)
        
        with open(config_path, 'w') as f:
            f.write(new_content)
        print("✅ config.py updated successfully!")
    except Exception as e:
        print(f"❌ Error updating config.py: {e}")