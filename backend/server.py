from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import praw
import pymongo
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta
import uuid
from dotenv import load_dotenv
import logging
import jwt
import bcrypt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from emergentintegrations.llm.chat import LlmChat, UserMessage
import csv
import io
import pandas as pd
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7  # 1 week

# Initialize VADER sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Initialize MongoDB
mongo_url = os.getenv("MONGO_URL")
db_name = os.getenv("DB_NAME", "reddit_social_listener")

try:
    mongo_client = MongoClient(mongo_url)
    db = mongo_client[db_name]
    
    # Collections
    users_collection = db["users"]
    keywords_collection = db["keywords"]
    posts_collection = db["posts"]
    searches_collection = db["searches"]
    trackers_collection = db["trackers"]
    
    # Create indexes for better performance
    users_collection.create_index("email", unique=True)
    keywords_collection.create_index([("user_id", 1), ("keyword", 1), ("subreddit", 1)])
    posts_collection.create_index("id", unique=True)
    searches_collection.create_index([("user_id", 1), ("timestamp", -1)])
    
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

# Initialize Gemini API for summarization
gemini_api_key = os.getenv("GEMINI_API_KEY")
summary_chat = None

if gemini_api_key:
    try:
        summary_chat = LlmChat(
            api_key=gemini_api_key,
            session_id="reddit-summary-session",
            system_message="You are an expert at creating concise summaries of Reddit posts and comments. Provide clear, brief summaries that capture the main points in 2-3 sentences maximum."
        ).with_model("gemini", "gemini-2.0-flash-lite")
        logger.info("Gemini API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")

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
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str
    is_active: bool = True

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
    sentiment_score: Optional[float] = None
    summary: Optional[str] = None

class SearchFilters(BaseModel):
    min_upvotes: Optional[int] = 0
    min_comments: Optional[int] = 0
    max_upvotes: Optional[int] = None
    max_comments: Optional[int] = None
    subreddit: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_sentiment: Optional[float] = None
    max_sentiment: Optional[float] = None

class SavedKeyword(BaseModel):
    id: str
    user_id: str
    keyword: str
    subreddit: str
    created_at: str
    active: bool = True

class TrackerDashboard(BaseModel):
    id: str
    user_id: str
    keyword: str
    subreddit: str
    created_at: str
    last_checked: Optional[str] = None
    total_posts: int = 0
    avg_sentiment: Optional[float] = None
    trending_score: Optional[float] = None

class SummaryRequest(BaseModel):
    content: str

# Authentication functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def calculate_sentiment_score(text: str) -> float:
    """Calculate sentiment score using VADER (0-10 scale)"""
    if not text:
        return 5.0  # Neutral
    
    scores = sentiment_analyzer.polarity_scores(text)
    # Convert compound score (-1 to 1) to 0-10 scale
    sentiment_score = ((scores['compound'] + 1) / 2) * 10
    return round(sentiment_score, 2)

def calculate_trending_score(upvotes: int, comments: int, age_hours: float) -> float:
    """Calculate trending score based on engagement and time"""
    if age_hours <= 0:
        age_hours = 0.1
    
    # Simple trending formula: (upvotes + comments * 2) / age_hours
    trending_score = (upvotes + comments * 2) / age_hours
    return round(trending_score, 2)

# API Routes
@app.get("/")
async def root():
    return {"message": "Reddit Social Listening Tool API"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "reddit_api": reddit is not None,
        "database": db is not None,
        "gemini_api": summary_chat is not None
    }

# Authentication routes
@app.post("/api/register")
async def register(user_data: UserRegister):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Check if user already exists
        existing_user = users_collection.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        hashed_password = hash_password(user_data.password)
        
        new_user = {
            "id": user_id,
            "email": user_data.email,
            "password": hashed_password,
            "full_name": user_data.full_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        
        users_collection.insert_one(new_user)
        
        # Create access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "user": User(
                id=user_id,
                email=user_data.email,
                full_name=user_data.full_name,
                created_at=new_user["created_at"]
            ),
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Error creating user")

@app.post("/api/login")
async def login(login_data: UserLogin):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        user = users_collection.find_one({"email": login_data.email})
        if not user or not verify_password(login_data.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is disabled")
        
        access_token = create_access_token(data={"sub": user["id"]})
        
        return {
            "user": User(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                created_at=user["created_at"],
                is_active=user.get("is_active", True)
            ),
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail="Error logging in")

@app.get("/api/me", response_model=User)
async def get_current_user_info(current_user: str = Depends(get_current_user)):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        user = users_collection.find_one({"id": current_user}, {"password": 0, "_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(**user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        raise HTTPException(status_code=500, detail="Error fetching user info")

# Enhanced Reddit API routes
@app.post("/api/search-posts", response_model=List[RedditPost])
async def search_posts(request: KeywordRequest, current_user: str = Depends(get_current_user)):
    """Search Reddit for posts containing the specified keyword with sentiment analysis"""
    if not reddit:
        raise HTTPException(status_code=500, detail="Reddit API not available")
    
    try:
        keyword = request.keyword.strip()
        subreddit = request.subreddit or "all"
        limit = min(request.limit or 25, 100)
        
        logger.info(f"User {current_user} searching for keyword '{keyword}' in r/{subreddit} (limit: {limit})")
        
        submissions = reddit.subreddit(subreddit).search(
            keyword, 
            limit=limit,
            sort="new"
        )
        
        posts = []
        search_timestamp = datetime.now(timezone.utc).isoformat()
        
        for submission in submissions:
            try:
                # Calculate sentiment score
                text_content = f"{submission.title} {submission.selftext if hasattr(submission, 'selftext') else ''}"
                sentiment_score = calculate_sentiment_score(text_content)
                
                # Calculate age in hours
                post_age_hours = (datetime.now().timestamp() - submission.created_utc) / 3600
                
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
                    search_timestamp=search_timestamp,
                    sentiment_score=sentiment_score
                )
                posts.append(post)
            except Exception as e:
                logger.warning(f"Error processing submission {submission.id}: {e}")
                continue
        
        # Store search results in database
        if db is not None:
            try:
                search_record = {
                    "id": str(uuid.uuid4()),
                    "user_id": current_user,
                    "keyword": keyword,
                    "subreddit": subreddit,
                    "timestamp": search_timestamp,
                    "post_count": len(posts),
                    "avg_sentiment": sum(p.sentiment_score for p in posts if p.sentiment_score) / len(posts) if posts else None
                }
                searches_collection.insert_one(search_record)
                
                # Store individual posts
                for post in posts:
                    post_dict = post.model_dump()
                    post_dict["user_id"] = current_user
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

@app.post("/api/summarize")
async def summarize_content(request: SummaryRequest, current_user: str = Depends(get_current_user)):
    """Generate AI summary of Reddit content using Gemini"""
    if not summary_chat:
        raise HTTPException(status_code=500, detail="Summarization service not available")
    
    try:
        content = request.content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        # Limit content length to avoid excessive API costs
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        user_message = UserMessage(
            text=f"Please provide a brief summary of this Reddit content: {content}"
        )
        
        response = await summary_chat.send_message(user_message)
        
        return {"summary": response.strip()}
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Error generating summary")

@app.post("/api/filter-posts", response_model=List[RedditPost])
async def filter_posts(posts: List[RedditPost], filters: SearchFilters, current_user: str = Depends(get_current_user)):
    """Filter posts based on various criteria including date range and sentiment"""
    filtered_posts = []
    
    # Parse date filters
    start_date = None
    end_date = None
    if filters.start_date:
        start_date = datetime.fromisoformat(filters.start_date.replace('Z', '+00:00')).timestamp()
    if filters.end_date:
        end_date = datetime.fromisoformat(filters.end_date.replace('Z', '+00:00')).timestamp()
    
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
        
        # Check date range filter
        if start_date and post.created_utc < start_date:
            continue
        if end_date and post.created_utc > end_date:
            continue
        
        # Check sentiment filter
        if filters.min_sentiment is not None and (post.sentiment_score is None or post.sentiment_score < filters.min_sentiment):
            continue
        if filters.max_sentiment is not None and (post.sentiment_score is None or post.sentiment_score > filters.max_sentiment):
            continue
            
        filtered_posts.append(post)
    
    return filtered_posts

@app.post("/api/save-keyword", response_model=SavedKeyword)
async def save_keyword(request: KeywordRequest, current_user: str = Depends(get_current_user)):
    """Save a keyword for tracking"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        keyword_id = str(uuid.uuid4())
        saved_keyword = SavedKeyword(
            id=keyword_id,
            user_id=current_user,
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
async def get_saved_keywords(current_user: str = Depends(get_current_user)):
    """Get all saved keywords for the current user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        keywords = list(keywords_collection.find(
            {"user_id": current_user, "active": True}, 
            {"_id": 0}
        ))
        return [SavedKeyword(**keyword) for keyword in keywords]
    except Exception as e:
        logger.error(f"Error fetching keywords: {e}")
        return []

@app.delete("/api/saved-keywords/{keyword_id}")
async def delete_keyword(keyword_id: str, current_user: str = Depends(get_current_user)):
    """Delete a saved keyword"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        result = keywords_collection.update_one(
            {"id": keyword_id, "user_id": current_user},
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
async def get_search_history(current_user: str = Depends(get_current_user)):
    """Get recent search history for the current user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        searches = list(searches_collection.find(
            {"user_id": current_user},
            {"_id": 0}
        ).sort("timestamp", -1).limit(50))
        
        return searches
    except Exception as e:
        logger.error(f"Error fetching search history: {e}")
        return []

@app.get("/api/dashboard")
async def get_dashboard_data(current_user: str = Depends(get_current_user)):
    """Get dashboard analytics for the current user"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        logger.info(f"Fetching dashboard data for user: {current_user}")
        
        # Get recent searches
        recent_searches = list(searches_collection.find(
            {"user_id": current_user},
            {"_id": 0}
        ).sort("timestamp", -1).limit(10))
        
        logger.info(f"Found {len(recent_searches)} recent searches")
        
        # Get sentiment trends (simplified)
        sentiment_data = []
        try:
            posts_with_sentiment = list(posts_collection.find(
                {"user_id": current_user, "sentiment_score": {"$exists": True, "$ne": None}},
                {"sentiment_score": 1, "search_timestamp": 1}
            ).limit(100))
            
            # Group by date manually
            date_groups = {}
            for post in posts_with_sentiment:
                if post.get("search_timestamp"):
                    try:
                        date_key = post["search_timestamp"][:10]  # Get YYYY-MM-DD
                        if date_key not in date_groups:
                            date_groups[date_key] = {"scores": [], "count": 0}
                        date_groups[date_key]["scores"].append(post["sentiment_score"])
                        date_groups[date_key]["count"] += 1
                    except Exception as e:
                        logger.warning(f"Error parsing date: {e}")
                        continue
            
            # Convert to list format
            for date_key, data in date_groups.items():
                avg_sentiment = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 5.0
                sentiment_data.append({
                    "_id": date_key,
                    "avg_sentiment": round(avg_sentiment, 2),
                    "post_count": data["count"]
                })
            
            # Sort by date descending
            sentiment_data.sort(key=lambda x: x["_id"], reverse=True)
            sentiment_data = sentiment_data[:30]  # Keep last 30 days
            
        except Exception as e:
            logger.error(f"Error calculating sentiment trends: {e}")
            sentiment_data = []
        
        logger.info(f"Found {len(sentiment_data)} sentiment trend data points")
        
        # Get keyword performance (simplified)
        keyword_stats = []
        try:
            keyword_aggregation = list(searches_collection.aggregate([
                {"$match": {"user_id": current_user}},
                {"$group": {
                    "_id": "$keyword",
                    "search_count": {"$sum": 1},
                    "total_posts": {"$sum": "$post_count"},
                    "avg_sentiment": {"$avg": "$avg_sentiment"},
                    "last_search": {"$max": "$timestamp"}
                }},
                {"$sort": {"search_count": -1}},
                {"$limit": 10}
            ]))
            keyword_stats = keyword_aggregation
        except Exception as e:
            logger.error(f"Error calculating keyword stats: {e}")
            # Fallback: get keyword stats manually
            search_docs = list(searches_collection.find({"user_id": current_user}))
            keyword_counts = {}
            for search in search_docs:
                keyword = search.get("keyword", "unknown")
                if keyword not in keyword_counts:
                    keyword_counts[keyword] = {
                        "_id": keyword,
                        "search_count": 0,
                        "total_posts": 0,
                        "avg_sentiment": None,
                        "last_search": search.get("timestamp")
                    }
                keyword_counts[keyword]["search_count"] += 1
                keyword_counts[keyword]["total_posts"] += search.get("post_count", 0)
                if search.get("timestamp") and (not keyword_counts[keyword]["last_search"] or search.get("timestamp") > keyword_counts[keyword]["last_search"]):
                    keyword_counts[keyword]["last_search"] = search.get("timestamp")
            
            keyword_stats = sorted(keyword_counts.values(), key=lambda x: x["search_count"], reverse=True)[:10]
        
        logger.info(f"Found {len(keyword_stats)} keyword stats")
        
        # Calculate summary stats
        total_searches = len(recent_searches) if len(recent_searches) < 10 else searches_collection.count_documents({"user_id": current_user})
        total_posts = posts_collection.count_documents({"user_id": current_user})
        
        result = {
            "recent_searches": recent_searches,
            "sentiment_trends": sentiment_data,
            "keyword_stats": keyword_stats,
            "summary_stats": {
                "total_searches": total_searches,
                "total_posts": total_posts,
                "avg_sentiment": sum(item["avg_sentiment"] for item in sentiment_data if item.get("avg_sentiment")) / len(sentiment_data) if sentiment_data else None
            }
        }
        
        logger.info(f"Dashboard data prepared successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        # Return empty data instead of error to prevent UI breaks
        return {
            "recent_searches": [],
            "sentiment_trends": [],
            "keyword_stats": [],
            "summary_stats": {
                "total_searches": 0,
                "total_posts": 0,
                "avg_sentiment": None
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        return {"recent_searches": [], "sentiment_trends": [], "keyword_stats": []}

@app.get("/api/export/csv")
async def export_to_csv(
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    current_user: str = Depends(get_current_user)
):
    """Export search results to CSV"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    
    try:
        # Build query
        query = {"user_id": current_user}
        if keyword:
            query["keyword_searched"] = keyword
        if start_date or end_date:
            date_filter = {}
            if start_date:
                date_filter["$gte"] = start_date
            if end_date:
                date_filter["$lte"] = end_date
            query["search_timestamp"] = date_filter
        
        # Get posts
        posts = list(posts_collection.find(query, {"_id": 0}))
        
        if not posts:
            raise HTTPException(status_code=404, detail="No data found for export")
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            'id', 'title', 'author', 'subreddit', 'upvotes', 'comments',
            'created_utc', 'permalink', 'keyword_searched', 'sentiment_score'
        ])
        writer.writeheader()
        
        for post in posts:
            # Convert timestamp to readable date
            if 'created_utc' in post:
                post['created_utc'] = datetime.fromtimestamp(post['created_utc']).isoformat()
            writer.writerow({k: v for k, v in post.items() if k in writer.fieldnames})
        
        # Return CSV file
        csv_content = output.getvalue()
        output.close()
        
        return {
            "filename": f"reddit_posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "content": csv_content,
            "content_type": "text/csv"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise HTTPException(status_code=500, detail="Error exporting data")

@app.get("/debug")
async def debug_page():
    """Serve debug HTML page"""
    return FileResponse("/app/debug.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)