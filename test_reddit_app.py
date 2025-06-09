import requests
import json
import time
from datetime import datetime, timedelta

# Base URL from frontend/.env
BASE_URL = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"

# Test user credentials
TEST_EMAIL = "test_user@example.com"
TEST_PASSWORD = "Test123!"
TEST_FULL_NAME = "Test User"

# Test keyword
TEST_KEYWORD = "python"
TEST_SUBREDDIT = "programming"

def print_separator(title):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def test_health_check():
    print_separator("Testing Health Check")
    
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Health check response: {json.dumps(data, indent=2)}")
        
        if not data.get("reddit_api"):
            print("⚠️ WARNING: Reddit API connection is not healthy")
        
        if not data.get("database"):
            print("⚠️ WARNING: Database connection is not healthy")
            
        if not data.get("gemini_api"):
            print("⚠️ WARNING: Gemini API connection is not healthy")
            
        print("✅ Health check test passed")
        return True
    else:
        print(f"❌ Health check test failed: {response.text}")
        return False

def authenticate():
    print_separator("Testing Authentication")
    
    # Try to register the user
    reg_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_FULL_NAME
    }
    
    print("Attempting registration...")
    reg_response = requests.post(f"{BASE_URL}/api/register", json=reg_payload)
    print(f"Registration status: {reg_response.status_code}")
    
    # If user already exists, try login
    if reg_response.status_code == 400:
        print("User already exists, trying login...")
        login_payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
        
        login_response = requests.post(f"{BASE_URL}/api/login", json=login_payload)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            data = login_response.json()
            token = data["access_token"]
            user_id = data["user"]["id"]
            print(f"✅ Login successful, token: {token[:20]}...")
            return token, user_id
        else:
            print(f"❌ Login failed: {login_response.text}")
            return None, None
    elif reg_response.status_code == 200:
        data = reg_response.json()
        token = data["access_token"]
        user_id = data["user"]["id"]
        print(f"✅ Registration successful, token: {token[:20]}...")
        return token, user_id
    else:
        print(f"❌ Registration failed: {reg_response.text}")
        return None, None

def test_user_info(token):
    print_separator("Testing User Info")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"User info: {json.dumps(data, indent=2)}")
        print("✅ User info test passed")
        return True
    else:
        print(f"❌ User info test failed: {response.text}")
        return False

def test_search_posts(token):
    print_separator("Testing Search Posts with Sentiment Analysis")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False, []
    
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "keyword": TEST_KEYWORD,
        "subreddit": TEST_SUBREDDIT,
        "limit": 10
    }
    
    response = requests.post(f"{BASE_URL}/api/search-posts", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        posts = response.json()
        print(f"Found {len(posts)} posts")
        
        if len(posts) > 0:
            sample_post = posts[0]
            print(f"Sample post: {json.dumps(sample_post, indent=2)}")
            
            # Check for sentiment score
            if "sentiment_score" in sample_post:
                print(f"Sentiment score: {sample_post['sentiment_score']}")
                print("✅ Sentiment analysis is working")
            else:
                print("❌ Sentiment analysis is not working")
        
        print("✅ Search posts test passed")
        return True, posts
    else:
        print(f"❌ Search posts test failed: {response.text}")
        return False, []

def test_summarize_content(token):
    print_separator("Testing Gemini AI Summarization")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    test_content = """
    Python is a high-level, interpreted programming language known for its readability and versatility.
    It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes
    code readability with its notable use of significant whitespace. Its language constructs and
    object-oriented approach aim to help programmers write clear, logical code for small and large-scale
    projects. Python is dynamically typed and garbage-collected. It supports multiple programming paradigms,
    including structured, object-oriented, and functional programming.
    """
    
    payload = {"content": test_content}
    
    response = requests.post(f"{BASE_URL}/api/summarize", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Summary: {json.dumps(data, indent=2)}")
        
        if "summary" in data and data["summary"]:
            print("✅ Gemini AI summarization is working")
            return True
        else:
            print("❌ Summary is empty")
            return False
    else:
        print(f"❌ Summarization test failed: {response.text}")
        return False

def test_filter_posts(token, posts):
    print_separator("Testing Enhanced Filtering")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    if not posts:
        print("❌ No posts available to filter, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test filtering by sentiment and date
    filter_payload = {
        "min_upvotes": 1,
        "min_sentiment": 5.0,  # Neutral to positive sentiment
        "start_date": (datetime.now() - timedelta(days=30)).isoformat()
    }
    
    response = requests.post(
        f"{BASE_URL}/api/filter-posts", 
        json={"posts": posts, "filters": filter_payload},
        headers=headers
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        filtered_posts = response.json()
        print(f"Original posts: {len(posts)}, Filtered posts: {len(filtered_posts)}")
        
        if len(filtered_posts) > 0:
            print("Sample filtered post:")
            print(f"Upvotes: {filtered_posts[0]['upvotes']}")
            print(f"Sentiment: {filtered_posts[0]['sentiment_score']}")
            print(f"Date: {datetime.fromtimestamp(filtered_posts[0]['created_utc']).isoformat()}")
        
        print("✅ Enhanced filtering test passed")
        return True
    else:
        print(f"❌ Filtering test failed: {response.text}")
        return False

def test_dashboard(token):
    print_separator("Testing Analytics Dashboard")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/dashboard", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Dashboard data structure:")
        for key in data:
            print(f"- {key}: {type(data[key]).__name__}")
            if isinstance(data[key], list):
                print(f"  Items: {len(data[key])}")
        
        # Check for required dashboard components
        if "recent_searches" in data and "sentiment_trends" in data and "keyword_stats" in data:
            print("✅ Dashboard analytics test passed")
            return True
        else:
            print("❌ Dashboard is missing required components")
            return False
    else:
        print(f"❌ Dashboard test failed: {response.text}")
        return False

def test_export_csv(token):
    print_separator("Testing CSV Export")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/export/csv?keyword={TEST_KEYWORD}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        print("⚠️ No data found for export")
        return False
    elif response.status_code == 200:
        data = response.json()
        print(f"CSV filename: {data.get('filename')}")
        
        if "content" in data and data["content"]:
            csv_lines = data["content"].strip().split('\n')
            print(f"CSV header: {csv_lines[0]}")
            print(f"Total rows: {len(csv_lines)}")
            
            if "sentiment_score" in csv_lines[0]:
                print("✅ Sentiment scores included in export")
            
            print("✅ CSV export test passed")
            return True
        else:
            print("❌ CSV content is empty")
            return False
    else:
        print(f"❌ CSV export test failed: {response.text}")
        return False

def test_keyword_management(token, user_id):
    print_separator("Testing Keyword Management")
    
    if not token:
        print("❌ No auth token available, skipping test")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Save a keyword
    save_payload = {
        "keyword": TEST_KEYWORD,
        "subreddit": TEST_SUBREDDIT
    }
    
    save_response = requests.post(f"{BASE_URL}/api/save-keyword", json=save_payload, headers=headers)
    print(f"Save keyword status: {save_response.status_code}")
    
    if save_response.status_code != 200:
        print(f"❌ Save keyword failed: {save_response.text}")
        return False
    
    saved_data = save_response.json()
    keyword_id = saved_data["id"]
    print(f"Saved keyword ID: {keyword_id}")
    
    # Get saved keywords
    get_response = requests.get(f"{BASE_URL}/api/saved-keywords", headers=headers)
    print(f"Get keywords status: {get_response.status_code}")
    
    if get_response.status_code != 200:
        print(f"❌ Get keywords failed: {get_response.text}")
        return False
    
    keywords = get_response.json()
    print(f"Found {len(keywords)} saved keywords")
    
    # Verify user-specific data isolation
    for keyword in keywords:
        if keyword["user_id"] != user_id:
            print(f"❌ Found keyword belonging to another user: {keyword}")
            return False
    
    # Delete the keyword
    delete_response = requests.delete(f"{BASE_URL}/api/saved-keywords/{keyword_id}", headers=headers)
    print(f"Delete keyword status: {delete_response.status_code}")
    
    if delete_response.status_code != 200:
        print(f"❌ Delete keyword failed: {delete_response.text}")
        return False
    
    print("✅ Keyword management test passed")
    return True

def run_all_tests():
    results = {}
    
    # Test health check
    results["health_check"] = test_health_check()
    
    # Test authentication
    token, user_id = authenticate()
    results["authentication"] = bool(token)
    
    if token:
        # Test user info
        results["user_info"] = test_user_info(token)
        
        # Test search posts with sentiment analysis
        search_success, posts = test_search_posts(token)
        results["search_posts"] = search_success
        
        # Test Gemini AI summarization
        results["summarization"] = test_summarize_content(token)
        
        # Test enhanced filtering
        results["filtering"] = test_filter_posts(token, posts)
        
        # Test analytics dashboard
        results["dashboard"] = test_dashboard(token)
        
        # Test CSV export
        results["csv_export"] = test_export_csv(token)
        
        # Test keyword management
        results["keyword_management"] = test_keyword_management(token, user_id)
    
    # Print summary
    print_separator("Test Results Summary")
    for test, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test.replace('_', ' ').title()}: {status}")
    
    return results

if __name__ == "__main__":
    run_all_tests()
