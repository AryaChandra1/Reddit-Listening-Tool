import requests
import unittest
import sys
import json
import time

class RedditSocialListenerAPITest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(RedditSocialListenerAPITest, self).__init__(*args, **kwargs)
        # Use the public endpoint from frontend/.env
        self.base_url = "https://68b19118-d393-4742-8fd9-8aedc0c31471.preview.emergentagent.com"
        self.test_keyword = "python"
        self.test_subreddit = "programming"
        self.saved_keyword_id = None

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
            
            self.assertEqual(data["status"], "healthy")
            
            if not data["reddit_api"]:
                print("⚠️ WARNING: Reddit API connection is not healthy")
            
            if not data["database"]:
                print("⚠️ WARNING: Database connection is not healthy")
                
            print("✅ Health check test passed")
        except Exception as e:
            print(f"❌ Health check test failed: {str(e)}")
            raise

    def test_02_search_posts(self):
        """Test the search posts endpoint with a simple keyword"""
        print("\n🔍 Testing Search Posts API...")
        
        try:
            payload = {
                "keyword": self.test_keyword,
                "subreddit": self.test_subreddit,
                "limit": 10
            }
            
            response = requests.post(
                f"{self.base_url}/api/search-posts", 
                json=payload
            )
            
            self.assertEqual(response.status_code, 200)
            
            posts = response.json()
            print(f"Found {len(posts)} posts for keyword '{self.test_keyword}'")
            
            if len(posts) > 0:
                # Verify post structure
                sample_post = posts[0]
                required_fields = ["id", "title", "author", "subreddit", "upvotes", "comments", "permalink"]
                
                for field in required_fields:
                    self.assertIn(field, sample_post, f"Field '{field}' missing from post")
                
                print(f"Sample post: {json.dumps(sample_post, indent=2)}")
            else:
                print("⚠️ WARNING: No posts found for the test keyword")
            
            print("✅ Search posts test passed")
        except Exception as e:
            print(f"❌ Search posts test failed: {str(e)}")
            raise

    def test_03_save_keyword(self):
        """Test saving a keyword"""
        print("\n🔍 Testing Save Keyword API...")
        
        try:
            payload = {
                "keyword": self.test_keyword,
                "subreddit": self.test_subreddit
            }
            
            response = requests.post(
                f"{self.base_url}/api/save-keyword", 
                json=payload
            )
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Saved keyword response: {data}")
            
            self.assertIn("id", data)
            self.assertIn("keyword", data)
            self.assertIn("subreddit", data)
            self.assertIn("created_at", data)
            
            self.assertEqual(data["keyword"], self.test_keyword)
            self.assertEqual(data["subreddit"], self.test_subreddit)
            
            # Save the keyword ID for later tests
            self.saved_keyword_id = data["id"]
            
            print("✅ Save keyword test passed")
        except Exception as e:
            print(f"❌ Save keyword test failed: {str(e)}")
            raise

    def test_04_get_saved_keywords(self):
        """Test retrieving saved keywords"""
        print("\n🔍 Testing Get Saved Keywords API...")
        
        try:
            response = requests.get(f"{self.base_url}/api/saved-keywords")
            
            self.assertEqual(response.status_code, 200)
            
            keywords = response.json()
            print(f"Found {len(keywords)} saved keywords")
            
            if len(keywords) > 0:
                # Check if our test keyword is in the list
                found = False
                for keyword in keywords:
                    if self.saved_keyword_id and keyword["id"] == self.saved_keyword_id:
                        found = True
                        break
                
                if self.saved_keyword_id:
                    self.assertTrue(found, "Saved keyword not found in the list")
                
                print(f"Sample saved keyword: {json.dumps(keywords[0], indent=2)}")
            
            print("✅ Get saved keywords test passed")
        except Exception as e:
            print(f"❌ Get saved keywords test failed: {str(e)}")
            raise

    def test_05_get_search_history(self):
        """Test retrieving search history"""
        print("\n🔍 Testing Get Search History API...")
        
        try:
            response = requests.get(f"{self.base_url}/api/search-history")
            
            self.assertEqual(response.status_code, 200)
            
            history = response.json()
            print(f"Found {len(history)} search history entries")
            
            if len(history) > 0:
                # Verify history entry structure
                sample_entry = history[0]
                required_fields = ["id", "keyword", "subreddit", "timestamp", "post_count"]
                
                for field in required_fields:
                    self.assertIn(field, sample_entry, f"Field '{field}' missing from history entry")
                
                print(f"Sample history entry: {json.dumps(sample_entry, indent=2)}")
            
            print("✅ Get search history test passed")
        except Exception as e:
            print(f"❌ Get search history test failed: {str(e)}")
            raise

    def test_06_delete_keyword(self):
        """Test deleting a saved keyword"""
        print("\n🔍 Testing Delete Keyword API...")
        
        if not self.saved_keyword_id:
            print("⚠️ Skipping delete keyword test as no keyword was saved")
            return
        
        try:
            response = requests.delete(
                f"{self.base_url}/api/saved-keywords/{self.saved_keyword_id}"
            )
            
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            print(f"Delete keyword response: {data}")
            
            self.assertIn("message", data)
            
            # Verify the keyword was deleted
            response = requests.get(f"{self.base_url}/api/saved-keywords")
            keywords = response.json()
            
            found = False
            for keyword in keywords:
                if keyword["id"] == self.saved_keyword_id:
                    found = True
                    break
            
            self.assertFalse(found, "Keyword was not properly deleted")
            
            print("✅ Delete keyword test passed")
        except Exception as e:
            print(f"❌ Delete keyword test failed: {str(e)}")
            raise

def run_tests():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    
    # Add tests in order
    suite.addTest(RedditSocialListenerAPITest('test_01_health_check'))
    suite.addTest(RedditSocialListenerAPITest('test_02_search_posts'))
    suite.addTest(RedditSocialListenerAPITest('test_03_save_keyword'))
    suite.addTest(RedditSocialListenerAPITest('test_04_get_saved_keywords'))
    suite.addTest(RedditSocialListenerAPITest('test_05_get_search_history'))
    suite.addTest(RedditSocialListenerAPITest('test_06_delete_keyword'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
