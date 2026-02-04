"""
Test script to verify Roboflow API connectivity
"""
import requests
import base64
import os

# Your Roboflow credentials
ROBOFLOW_API_KEY = "3HD9zKublJXcCejsWdgg"
ROBOFLOW_PROJECT = "my-first-project-9fmyh"
ROBOFLOW_VERSION = "6"

def test_roboflow_connection():
    """Test if we can reach Roboflow API"""
    print("=" * 60)
    print("ROBOFLOW API CONNECTION TEST")
    print("=" * 60)
    
    # Test URL
    url = f"https://detect.roboflow.com/{ROBOFLOW_PROJECT}/{ROBOFLOW_VERSION}"
    
    print(f"\n📡 Testing connection to Roboflow API...")
    print(f"   URL: {url}")
    print(f"   API Key: {ROBOFLOW_API_KEY[:10]}...")
    
    # Create a simple test (1x1 pixel image)
    test_image = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82').decode('utf-8')
    
    params = {
        "api_key": ROBOFLOW_API_KEY,
        "confidence": 40,
        "overlap": 30
    }
    
    try:
        print("\n🔄 Sending request...")
        response = requests.post(
            url,
            params=params,
            data=test_image,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"\n✅ Response received!")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"\n🎉 SUCCESS! Roboflow API is working!")
            result = response.json()
            print(f"\n   Response preview:")
            print(f"   {result}")
        elif response.status_code == 401:
            print(f"\n❌ AUTHENTICATION ERROR!")
            print(f"   Your API key might be invalid.")
            print(f"   Please check: https://app.roboflow.com/settings/api")
        elif response.status_code == 404:
            print(f"\n❌ NOT FOUND!")
            print(f"   Project: {ROBOFLOW_PROJECT}")
            print(f"   Version: {ROBOFLOW_VERSION}")
            print(f"   Please verify these are correct at: https://app.roboflow.com")
        else:
            print(f"\n⚠️  Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"\n❌ CONNECTION TIMEOUT!")
        print(f"   The request took too long. Check your internet connection.")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ CONNECTION ERROR!")
        print(f"   Cannot reach Roboflow API. Check your internet connection.")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_roboflow_connection()
