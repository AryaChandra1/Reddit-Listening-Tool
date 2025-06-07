import requests
import json
import sys

def test_json_parse_error():
    """Test if we can reproduce the JSON parse error"""
    print("\n🔍 Testing JSON Parse Error Reproduction...")
    
    # Test parsing undefined
    try:
        result = json.loads(None)
        print("✅ JSON.parse(null) succeeded (unexpected)")
    except Exception as e:
        print(f"❌ JSON.parse(null) failed with error: {str(e)}")
    
    # Test parsing empty string
    try:
        result = json.loads("")
        print("✅ JSON.parse('') succeeded (unexpected)")
    except Exception as e:
        print(f"❌ JSON.parse('') failed with error: {str(e)}")
    
    # Test parsing valid JSON
    try:
        result = json.loads('{"test": "valid"}')
        print(f"✅ JSON.parse('{{\"test\": \"valid\"}}') succeeded: {result}")
    except Exception as e:
        print(f"❌ JSON.parse('{{\"test\": \"valid\"}}') failed with error: {str(e)}")

def test_api_endpoints():
    """Test all API endpoints to check for undefined responses"""
    base_url = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"
    
    endpoints = [
        {"method": "GET", "url": "/api/health", "name": "Health Check"},
        {"method": "GET", "url": "/api/test", "name": "Test Endpoint"},
        {"method": "GET", "url": "/api/saved-keywords", "name": "Get Saved Keywords"},
        {"method": "GET", "url": "/api/search-history", "name": "Get Search History"},
        {"method": "POST", "url": "/api/search-posts", "name": "Search Posts", "data": {"keyword": "python", "subreddit": "all", "limit": 10}},
        {"method": "POST", "url": "/api/filter-posts", "name": "Filter Posts", "data": {"posts": [], "filters": {"min_upvotes": 0}}},
        {"method": "POST", "url": "/api/save-keyword", "name": "Save Keyword", "data": {"keyword": "test_keyword", "subreddit": "all"}},
    ]
    
    print("\n🔍 Testing API Endpoints for undefined responses...")
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint['name']} ({endpoint['method']} {endpoint['url']})...")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{base_url}{endpoint['url']}")
            else:
                response = requests.post(f"{base_url}{endpoint['url']}", json=endpoint.get('data', {}))
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                # Check if response is empty
                if not response.text:
                    print("⚠️ WARNING: Empty response")
                    continue
                
                # Try to parse JSON
                try:
                    data = response.json()
                    print(f"✅ Response parsed successfully: {type(data)}")
                except Exception as e:
                    print(f"❌ Failed to parse response: {str(e)}")
                    print(f"Raw response: {response.text[:100]}...")
            else:
                print(f"❌ Request failed with status code {response.status_code}")
                print(f"Response: {response.text[:100]}...")
        
        except Exception as e:
            print(f"❌ Request failed with error: {str(e)}")

def test_debug_page():
    """Test the debug page to see if it's working"""
    base_url = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"
    
    print("\n🔍 Testing Debug Page...")
    
    try:
        response = requests.get(f"{base_url}/debug")
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            # Check if response contains expected HTML
            if "Reddit Social Listening Tool - Debug" in response.text:
                print("✅ Debug page loaded successfully")
            else:
                print("⚠️ WARNING: Debug page loaded but content is unexpected")
                print(f"First 100 chars: {response.text[:100]}...")
        else:
            print(f"❌ Failed to load debug page: {response.status_code}")
            print(f"Response: {response.text[:100]}...")
    
    except Exception as e:
        print(f"❌ Request failed with error: {str(e)}")

def main():
    test_json_parse_error()
    test_api_endpoints()
    test_debug_page()
    return 0

if __name__ == "__main__":
    sys.exit(main())