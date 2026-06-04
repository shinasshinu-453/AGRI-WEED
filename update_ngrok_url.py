"""
Script to fetch the current ngrok URL and update .env files.
Run this after starting server.py --ngrok to sync the environment variables.
"""
import requests
import re
import os
from pathlib import Path

def get_current_ngrok_url():
    """Fetch the current ngrok tunnel URL from ngrok's local API."""
    try:
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get("tunnels", [])
            for tunnel in tunnels:
                if tunnel.get("proto") == "https":
                    return tunnel.get("public_url")
        return None
    except Exception as e:
        print(f"❌ Error fetching ngrok URL: {e}")
        return None

def update_env_file(filepath, new_url):
    """Update the VITE_API_URL in an environment file."""
    if not os.path.exists(filepath):
        print(f"⚠️  File not found: {filepath}")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Replace the VITE_API_URL line
    new_content = re.sub(
        r'VITE_API_URL=.*',
        f'VITE_API_URL={new_url}',
        content
    )
    
    with open(filepath, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Updated {filepath}")
    return True

def main():
    print("🔍 Fetching current ngrok URL...")
    ngrok_url = get_current_ngrok_url()
    
    if not ngrok_url:
        print("❌ Could not retrieve ngrok URL. Make sure:")
        print("   1. Python server is running with --ngrok flag")
        print("   2. Ngrok tunnel is active")
        print("   3. Ngrok web interface is accessible at http://localhost:4040")
        return
    
    print(f"✅ Found ngrok URL: {ngrok_url}")
    
    # Update both .env and .env.local files
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    env_local_file = project_root / '.env.local'
    
    updated = False
    if env_file.exists():
        updated |= update_env_file(env_file, ngrok_url)
    
    if env_local_file.exists():
        updated |= update_env_file(env_local_file, ngrok_url)
    
    if updated:
        print("\n✅ Environment files updated successfully!")
        print("⚠️  IMPORTANT: Restart your dev server (npm run dev) to apply changes")
        print(f"   Current URL: {ngrok_url}")
    else:
        print("❌ No files were updated")

if __name__ == "__main__":
    main()
