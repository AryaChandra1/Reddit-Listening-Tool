import requests
import unittest
import sys
import json
import time
import uuid
from datetime import datetime, timedelta

class RedditSocialListenerAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RedditSocialListenerAPITest, self).__init__(*args, **kwargs)
        # Use the public endpoint from frontend/.env
        self.base_url = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"
        self.test_keyword = "python"
        self.test_subreddit = "programming"
        self.saved_keyword_id = None
        
        # Test user credentials - use a fixed email for consistency
        self.test_email = "test_user@example.com"
        self.test_password = "Test123!"
        self.test_full_name = "Test User"
        
        # Auth token
        self.auth_token = None
        self.user_id = None

    def test_01_health_check(self):
        """Test the health check endpoint to verify Reddit API and database connections"""
        print("\n🔍 Testing API Health Check...")
        
        try:
            response = requests.get(f"{self.base_url}/api/health")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Health check response: {data}")
            
            self.assertIn("status", data)
            self.assertIn("reddit_api", data)
            self.assertIn("database", data)
            self.assertIn("gemini_api", data)
            
            self.assertEqual(data["status"], "healthy")
            
            if not data["reddit_api"]:
                print("⚠️ WARNING: Reddit API connection is not healthy")
            
            if not data["database"]:
                print("⚠️ WARNING: Database connection is not healthy")
                
            if not data["gemini_api"]:
                print("⚠️ WARNING: Gemini API connection is not healthy")
                
            print("✅ Health check test passed")
        except Exception as e:
            print(f"❌ Health check test failed: {str(e)}")
            raise

    def test_02_register_and_login(self):
        """Test user registration and login"""
        print("\n🔍 Testing User Registration and Login...")
        
        try:
            # Try to register the user
            reg_payload = {
                "email": self.test_email,
                "password": self.test_password,
                "full_name": self.test_full_name
            }
            
            reg_response = requests.post(
                f"{self.base_url}/api/register", 
                json=reg_payload
            )
            
            print(f"Registration response status: {reg_response.status_code}")
            print(f"Registration response body: {reg_response.text}")
            
            # If registration fails with 400 (user already exists), try login
            if reg_response.status_code == 400:
                print("User already exists, trying login instead")
            elif reg_response.status_code == 200:
                reg_data = reg_response.json()
                self.auth_token = reg_data["access_token"]
                self.user_id = reg_data["user"]["id"]
                print(f"Registration successful, token: {self.auth_token[:20]}...")
                print(f"User ID: {self.user_id}")
                return
            else:
                print(f"Registration response body: {reg_response.text}")
                self.fail(f"Registration failed with status {reg_response.status_code}")
            
            # Login with the same credentials
            login_payload = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            login_response = requests.post(
                f"{self.base_url}/api/login", 
                json=login_payload
            )
            
            print(f"Login response status: {login_response.status_code}")
            print(f"Login response body: {login_response.text}")
            
            self.assertEqual(login_response.status_code, 200)
            
            login_data = login_response.json()
            print(f"Login response: {json.dumps(login_data, indent=2)}")
            
            self.assertIn("user", login_data)
            self.assertIn("access_token", login_data)
            self.assertIn("token_type", login_data)
            
            self.assertEqual(login_data["user"]["email"], self.test_email)
            self.assertEqual(login_data["token_type"], "bearer")
            
            # Save token for subsequent tests
            self.auth_token = login_data["access_token"]
            self.user_id = login_data["user"]["id"]
            
            print(f"Login successful, token: {self.auth_token[:20]}...")
            print(f"User ID: {self.user_id}")
            
            print("✅ User login successful")
        except Exception as e:
            print(f"❌ User authentication test failed: {str(e)}")
            raise

    def test_03_get_current_user(self):
        """Test getting current user info"""
        print("\n🔍 Testing Get Current User...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.base_url}/api/me",
                headers=headers
            )
            
            print(f"Get current user response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Current user response: {json.dumps(data, indent=2)}")
            
            self.assertEqual(data["email"], self.test_email)
            self.assertEqual(data["full_name"], self.test_full_name)
            self.assertEqual(data["id"], self.user_id)
            
            print("✅ Get current user test passed")
        except Exception as e:
            print(f"❌ Get current user test failed: {str(e)}")
            raise

    def test_04_search_posts_with_auth(self):
        """Test the search posts endpoint with authentication and verify sentiment scores"""
        print("\n🔍 Testing Search Posts API with Authentication...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "keyword": self.test_keyword,
                "subreddit": self.test_subreddit,
                "limit": 10
            }
            
            response = requests.post(
                f"{self.base_url}/api/search-posts", 
                json=payload,
                headers=headers
            )
            
            print(f"Search posts response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            posts = response.json()
            print(f"Found {len(posts)} posts for keyword '{self.test_keyword}'")
            
            if len(posts) > 0:
                # Verify post structure including sentiment score
                sample_post = posts[0]
                required_fields = ["id", "title", "author", "subreddit", "upvotes", 
                                  "comments", "permalink", "sentiment_score"]
                
                for field in required_fields:
                    self.assertIn(field, sample_post, f"Field '{field}' missing from post")
                
                # Verify sentiment score is in the expected range (0-10)
                self.assertIsNotNone(sample_post["sentiment_score"])
                self.assertGreaterEqual(sample_post["sentiment_score"], 0)
                self.assertLessEqual(sample_post["sentiment_score"], 10)
                
                print(f"Sample post with sentiment score: {json.dumps(sample_post, indent=2)}")
            else:
                print("⚠️ WARNING: No posts found for the test keyword")
            
            print("✅ Search posts with auth test passed")
        except Exception as e:
            print(f"❌ Search posts with auth test failed: {str(e)}")
            raise

    def test_05_filter_posts(self):
        """Test filtering posts by various criteria including sentiment"""
        print("\n🔍 Testing Filter Posts API...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # First get some posts to filter
            search_payload = {
                "keyword": "technology",  # Using a broader keyword to get more results
                "subreddit": "all",
                "limit": 20
            }
            
            search_response = requests.post(
                f"{self.base_url}/api/search-posts", 
                json=search_payload,
                headers=headers
            )
            
            print(f"Search for filter response status: {search_response.status_code}")
            
            self.assertEqual(search_response.status_code, 200)
            posts = search_response.json()
            
            if len(posts) == 0:
                print("⚠️ WARNING: No posts found to filter")
                return
            
            # Now test filtering
            filter_payload = {
                "min_upvotes": 5,
                "min_sentiment": 5.0,  # Filter for neutral to positive sentiment
                "start_date": (datetime.now() - timedelta(days=30)).isoformat()
            }
            
            filter_response = requests.post(
                f"{self.base_url}/api/filter-posts", 
                json={"posts": posts, "filters": filter_payload},
                headers=headers
            )
            
            print(f"Filter posts response status: {filter_response.status_code}")
            
            self.assertEqual(filter_response.status_code, 200)
            
            filtered_posts = filter_response.json()
            print(f"Original posts: {len(posts)}, Filtered posts: {len(filtered_posts)}")
            
            # Verify filters were applied
            for post in filtered_posts:
                self.assertGreaterEqual(post["upvotes"], filter_payload["min_upvotes"])
                self.assertGreaterEqual(post["sentiment_score"], filter_payload["min_sentiment"])
                post_date = datetime.fromtimestamp(post["created_utc"])
                filter_date = datetime.fromisoformat(filter_payload["start_date"].replace('Z', '+00:00'))
                self.assertGreaterEqual(post_date, filter_date)
            
            print("✅ Filter posts test passed")
        except Exception as e:
            print(f"❌ Filter posts test failed: {str(e)}")
            raise

    def test_06_summarize_content(self):
        """Test the Gemini AI summarization feature"""
        print("\n🔍 Testing Gemini AI Summarization...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create test content to summarize
            test_content = """
            Python is a high-level, interpreted programming language known for its readability and versatility.
            It was created by Guido van Rossum and first released in 1991. Python's design philosophy emphasizes
            code readability with its notable use of significant whitespace. Its language constructs and
            object-oriented approach aim to help programmers write clear, logical code for small and large-scale
            projects. Python is dynamically typed and garbage-collected. It supports multiple programming paradigms,
            including structured, object-oriented, and functional programming.
            """
            
            payload = {"content": test_content}
            
            response = requests.post(
                f"{self.base_url}/api/summarize", 
                json=payload,
                headers=headers
            )
            
            print(f"Summarize response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Summarization response: {json.dumps(data, indent=2)}")
            
            self.assertIn("summary", data)
            self.assertTrue(len(data["summary"]) > 0)
            
            print("✅ Summarization test passed")
        except Exception as e:
            print(f"❌ Summarization test failed: {str(e)}")
            raise

    def test_07_save_keyword_with_auth(self):
        """Test saving a keyword with authentication"""
        print("\n🔍 Testing Save Keyword API with Authentication...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "keyword": self.test_keyword,
                "subreddit": self.test_subreddit
            }
            
            response = requests.post(
                f"{self.base_url}/api/save-keyword", 
                json=payload,
                headers=headers
            )
            
            print(f"Save keyword response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Saved keyword response: {json.dumps(data, indent=2)}")
            
            self.assertIn("id", data)
            self.assertIn("keyword", data)
            self.assertIn("subreddit", data)
            self.assertIn("created_at", data)
            self.assertIn("user_id", data)
            
            self.assertEqual(data["keyword"], self.test_keyword)
            self.assertEqual(data["subreddit"], self.test_subreddit)
            self.assertEqual(data["user_id"], self.user_id)
            
            # Save the keyword ID for later tests
            self.saved_keyword_id = data["id"]
            
            print("✅ Save keyword with auth test passed")
        except Exception as e:
            print(f"❌ Save keyword with auth test failed: {str(e)}")
            raise

    def test_08_get_saved_keywords_with_auth(self):
        """Test retrieving saved keywords with authentication"""
        print("\n🔍 Testing Get Saved Keywords API with Authentication...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.base_url}/api/saved-keywords",
                headers=headers
            )
            
            print(f"Get saved keywords response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            keywords = response.json()
            print(f"Found {len(keywords)} saved keywords")
            
            if len(keywords) > 0:
                # Check if our test keyword is in the list
                found = False
                for keyword in keywords:
                    if self.saved_keyword_id and keyword["id"] == self.saved_keyword_id:
                        found = True
                        self.assertEqual(keyword["user_id"], self.user_id)
                        break
                
                if self.saved_keyword_id:
                    self.assertTrue(found, "Saved keyword not found in the list")
                
                print(f"Sample saved keyword: {json.dumps(keywords[0], indent=2)}")
            
            print("✅ Get saved keywords with auth test passed")
        except Exception as e:
            print(f"❌ Get saved keywords with auth test failed: {str(e)}")
            raise

    def test_09_get_dashboard_data(self):
        """Test retrieving dashboard analytics data"""
        print("\n🔍 Testing Dashboard Analytics API...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(
                f"{self.base_url}/api/dashboard",
                headers=headers
            )
            
            print(f"Dashboard response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Dashboard data: {json.dumps(data, indent=2)}")
            
            self.assertIn("recent_searches", data)
            self.assertIn("sentiment_trends", data)
            self.assertIn("keyword_stats", data)
            
            print("✅ Dashboard analytics test passed")
        except Exception as e:
            print(f"❌ Dashboard analytics test failed: {str(e)}")
            raise

    def test_10_export_to_csv(self):
        """Test exporting search results to CSV"""
        print("\n🔍 Testing Export to CSV API...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # First perform a search to have data to export
            search_payload = {
                "keyword": self.test_keyword,
                "subreddit": self.test_subreddit,
                "limit": 5
            }
            
            search_response = requests.post(
                f"{self.base_url}/api/search-posts", 
                json=search_payload,
                headers=headers
            )
            
            print(f"Search for export response status: {search_response.status_code}")
            
            self.assertEqual(search_response.status_code, 200)
            
            # Now test export
            response = requests.get(
                f"{self.base_url}/api/export/csv?keyword={self.test_keyword}",
                headers=headers
            )
            
            print(f"Export response status: {response.status_code}")
            
            # Check if we have data to export
            if response.status_code == 404:
                print("⚠️ WARNING: No data found for export")
                return
                
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Export response: {json.dumps(data, indent=2)}")
            
            self.assertIn("filename", data)
            self.assertIn("content", data)
            self.assertIn("content_type", data)
            
            self.assertEqual(data["content_type"], "text/csv")
            self.assertTrue(len(data["content"]) > 0)
            
            # Verify CSV content has headers and data
            csv_lines = data["content"].strip().split('\n')
            self.assertGreaterEqual(len(csv_lines), 2)  # At least header + 1 data row
            
            print("✅ Export to CSV test passed")
        except Exception as e:
            print(f"❌ Export to CSV test failed: {str(e)}")
            raise

    def test_11_delete_keyword_with_auth(self):
        """Test deleting a saved keyword with authentication"""
        print("\n🔍 Testing Delete Keyword API with Authentication...")
        
        if not self.saved_keyword_id:
            print("⚠️ Skipping delete keyword test as no keyword was saved")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.delete(
                f"{self.base_url}/api/saved-keywords/{self.saved_keyword_id}",
                headers=headers
            )
            
            print(f"Delete keyword response status: {response.status_code}")
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Delete keyword response: {json.dumps(data, indent=2)}")
            
            self.assertIn("message", data)
            
            # Verify the keyword was deleted
            response = requests.get(
                f"{self.base_url}/api/saved-keywords",
                headers=headers
            )
            keywords = response.json()
            
            found = False
            for keyword in keywords:
                if keyword["id"] == self.saved_keyword_id:
                    found = True
                    break
            
            self.assertFalse(found, "Keyword was not properly deleted")
            
            print("✅ Delete keyword with auth test passed")
        except Exception as e:
            print(f"❌ Delete keyword with auth test failed: {str(e)}")
            raise

def run_tests():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add tests in order
    suite.addTest(RedditSocialListenerAPITest('test_01_health_check'))
    suite.addTest(RedditSocialListenerAPITest('test_02_register_and_login'))
    suite.addTest(RedditSocialListenerAPITest('test_03_get_current_user'))
    suite.addTest(RedditSocialListenerAPITest('test_04_search_posts_with_auth'))
    suite.addTest(RedditSocialListenerAPITest('test_05_filter_posts'))
    suite.addTest(RedditSocialListenerAPITest('test_06_summarize_content'))
    suite.addTest(RedditSocialListenerAPITest('test_07_save_keyword_with_auth'))
    suite.addTest(RedditSocialListenerAPITest('test_08_get_saved_keywords_with_auth'))
    suite.addTest(RedditSocialListenerAPITest('test_09_get_dashboard_data'))
    suite.addTest(RedditSocialListenerAPITest('test_10_export_to_csv'))
    suite.addTest(RedditSocialListenerAPITest('test_11_delete_keyword_with_auth'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
