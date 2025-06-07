from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import os
import praw
import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone
import uuid
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MongoDB
mongo_url = os.getenv("MONGO_URL")
db_name = os.getenv("DB_NAME", "reddit_social_listener")

try:
    mongo_client = MongoClient(mongo_url)
    db = mongo_client[db_name]
    
    # Collections
    keywords_collection = db["keywords"]
    posts_collection = db["posts"]
    searches_collection = db["searches"]
    
    logger.info(f"Connected to MongoDB at {mongo_url}")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    db = None

# Initialize Reddit API
reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
reddit_user_agent = os.getenv("REDDIT_USER_AGENT")

try:
    reddit = praw.Reddit(
        client_id=reddit_client_id,
        client_secret=reddit_client_secret,
        user_agent=reddit_user_agent
    )
    logger.info("Reddit API client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Reddit API: {e}")
    reddit = None

app = FastAPI(title="Reddit Social Listening Tool")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models
class KeywordRequest(BaseModel):
    keyword: str
    subreddit: Optional[str] = "all"
    limit: Optional[int] = 25

class RedditPost(BaseModel):
    id: str
    title: str
    author: Optional[str]
    subreddit: str
    upvotes: int
    url: str
    comments: int
    created_utc: float
    permalink: str
    body: Optional[str] = None
    keyword_searched: Optional[str] = None
    search_timestamp: Optional[str] = None

class SearchFilters(BaseModel):
    min_upvotes: Optional[int] = 0
    min_comments: Optional[int] = 0
    max_upvotes: Optional[int] = None
    max_comments: Optional[int] = None
    subreddit: Optional[str] = None

class SavedKeyword(BaseModel):
    id: str
    keyword: str
    subreddit: str
    created_at: str
    active: bool = True

@app.get("/")
async def root():
    return {"message": "Reddit Social Listening Tool API"}

@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to debug issues"""
    return {"status": "ok", "message": "API is working", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "reddit_api": reddit is not None,
        "database": db is not None
    }

@app.post("/api/search-posts", response_model=List[RedditPost])
async def search_posts(request: KeywordRequest):
    """Search Reddit for posts containing the specified keyword"""
    if reddit is None:
        raise HTTPException(status_code=500, detail="Reddit API not available")
    
    try:
        keyword = request.keyword.strip()
        subreddit = request.subreddit or "all"
        limit = min(request.limit or 25, 100)  # Cap at 100 posts
        
        logger.info(f"Searching for keyword '{keyword}' in r/{subreddit} (limit: {limit})")
        
        # Search Reddit
        submissions = reddit.subreddit(subreddit).search(
            keyword, 
            limit=limit,
            sort="new"
        )
        
        posts = []
        search_timestamp = datetime.now(timezone.utc).isoformat()
        
        for submission in submissions:
            try:
                post = RedditPost(
                    id=submission.id,
                    title=submission.title,
                    author=str(submission.author) if submission.author else "[deleted]",
                    subreddit=str(submission.subreddit),
                    upvotes=submission.score,
                    url=submission.url,
                    comments=submission.num_comments,
                    created_utc=submission.created_utc,
                    permalink=f"https://reddit.com{submission.permalink}",
                    body=submission.selftext[:500] if hasattr(submission, 'selftext') and submission.selftext else None,
                    keyword_searched=keyword,
                    search_timestamp=search_timestamp
                )
                posts.append(post)
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {e}")
                continue
        
        # Store search results in database if available
        if db is not None:
            try:
                search_record = {
                    "id": str(uuid.uuid4()),
                    "keyword": keyword,
                    "subreddit": subreddit,
                    "timestamp": search_timestamp,
                    "post_count": len(posts),
                    "posts": [post.model_dump() for post in posts]
                }
                searches_collection.insert_one(search_record)
                
                # Store individual posts
                for post in posts:
                    post_dict = post.model_dump()
                    posts_collection.update_one(
                        {"id": post.id},
                        {"$set": post_dict},
                        upsert=True
                    )
            except Exception as e:
                logger.warning(f"Error storing search results: {e}")
        
        logger.info(f"Found {len(posts)} posts for keyword '{keyword}'")
        return posts
        
    except Exception as e:
        logger.error(f"Error searching Reddit: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching Reddit: {str(e)}")

@app.post("/api/filter-posts", response_model=List[RedditPost])
async def filter_posts(posts: List[RedditPost], filters: SearchFilters):
    """Filter posts based on upvotes, comments, and subreddit"""
    filtered_posts = []
    
    for post in posts:
        # Check upvotes filter
        if filters.min_upvotes is not None and post.upvotes < filters.min_upvotes:
            continue
        if filters.max_upvotes is not None and post.upvotes > filters.max_upvotes:
            continue
            
        # Check comments filter
        if filters.min_comments is not None and post.comments < filters.min_comments:
            continue
        if filters.max_comments is not None and post.comments > filters.max_comments:
            continue
            
        # Check subreddit filter
        if filters.subreddit and filters.subreddit.lower() not in post.subreddit.lower():
            continue
            
        filtered_posts.append(post)
    
    return filtered_posts

@app.post("/api/save-keyword", response_model=SavedKeyword)
async def save_keyword(request: KeywordRequest):
    """Save a keyword for tracking"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        keyword_id = str(uuid.uuid4())
        saved_keyword = SavedKeyword(
            id=keyword_id,
            keyword=request.keyword.strip(),
            subreddit=request.subreddit or "all",
            created_at=datetime.now(timezone.utc).isoformat(),
            active=True
        )
        
        keywords_collection.insert_one(saved_keyword.model_dump())
        return saved_keyword
        
    except Exception as e:
        logger.error(f"Error saving keyword: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving keyword: {str(e)}")

@app.get("/api/saved-keywords", response_model=List[SavedKeyword])
async def get_saved_keywords():
    """Get all saved keywords"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        keywords = list(keywords_collection.find({"active": True}, {"_id": 0}))
        result = [SavedKeyword(**keyword) for keyword in keywords]
        return result
    except Exception as e:
        logger.error(f"Error fetching keywords: {e}")
        # Return empty list instead of raising exception
        return []

@app.delete("/api/saved-keywords/{keyword_id}")
async def delete_keyword(keyword_id: str):
    """Delete a saved keyword"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        result = keywords_collection.update_one(
            {"id": keyword_id},
            {"$set": {"active": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Keyword not found")
            
        return {"message": "Keyword deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting keyword: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting keyword: {str(e)}")

@app.get("/api/search-history")
async def get_search_history():
    """Get recent search history"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        searches = list(searches_collection.find(
            {},
            {"_id": 0, "posts": 0}  # Exclude posts field for performance
        ).sort("timestamp", -1).limit(20))
        
        return searches
    except Exception as e:
        logger.error(f"Error fetching search history: {e}")
        # Return empty list instead of raising exception
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)