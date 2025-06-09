import requests
import json
import sys

def test_dashboard_api():
    """Test the dashboard API functionality"""
    # Use the public endpoint from frontend/.env
    base_url = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"
    
    # Test user credentials
    test_email = "test_user@example.com"
    test_password = "Test123!"
    
    print("\n🔍 Testing Dashboard API...")
    
    # Step 1: Login to get auth token
    print("\n1. Logging in to get auth token...")
    login_payload = {
        "email": test_email,
        "password": test_password
    }
    
    login_response = requests.post(
        f"{base_url}/api/login", 
        json=login_payload
    )
    
    print(f"Login response status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Login failed with status {login_response.status_code}")
        print(f"Response: {login_response.text}")
        return False
    
    login_data = login_response.json()
    auth_token = login_data["access_token"]
    print(f"Login successful, token: {auth_token[:20]}...")
    
    # Step 2: Test dashboard API
    print("\n2. Testing dashboard API...")
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    dashboard_response = requests.get(
        f"{base_url}/api/dashboard",
        headers=headers
    )
    
    print(f"Dashboard response status: {dashboard_response.status_code}")
    
    if dashboard_response.status_code != 200:
        print(f"Dashboard API failed with status {dashboard_response.status_code}")
        print(f"Response: {dashboard_response.text}")
        return False
    
    dashboard_data = dashboard_response.json()
    
    # Verify dashboard data structure
    required_fields = ["recent_searches", "sentiment_trends", "keyword_stats", "summary_stats"]
    for field in required_fields:
        if field not in dashboard_data:
            print(f"❌ Missing required field: {field}")
            return False
        print(f"✅ Found required field: {field}")
    
    # Verify summary stats
    summary_stats = dashboard_data["summary_stats"]
    summary_fields = ["total_searches", "total_posts", "avg_sentiment"]
    for field in summary_fields:
        if field not in summary_stats:
            print(f"❌ Missing summary stat: {field}")
            return False
        print(f"✅ Found summary stat: {field}")
    
    # Print summary stats
    print("\nSummary Stats:")
    print(f"- Total Searches: {summary_stats['total_searches']}")
    print(f"- Total Posts: {summary_stats['total_posts']}")
    print(f"- Avg Sentiment: {summary_stats['avg_sentiment']}")
    
    # Check recent searches
    recent_searches = dashboard_data["recent_searches"]
    print(f"\nRecent Searches: {len(recent_searches)} found")
    if recent_searches:
        print(f"Sample recent search: {json.dumps(recent_searches[0], indent=2)}")
    
    # Check sentiment trends
    sentiment_trends = dashboard_data["sentiment_trends"]
    print(f"\nSentiment Trends: {len(sentiment_trends)} found")
    if sentiment_trends:
        print(f"Sample sentiment trend: {json.dumps(sentiment_trends[0], indent=2)}")
    
    # Check keyword stats
    keyword_stats = dashboard_data["keyword_stats"]
    print(f"\nKeyword Stats: {len(keyword_stats)} found")
    if keyword_stats:
        print(f"Sample keyword stat: {json.dumps(keyword_stats[0], indent=2)}")
    
    print("\n✅ Dashboard API test completed successfully")
    return True

if __name__ == "__main__":
    success = test_dashboard_api()
    sys.exit(0 if success else 1)