# Backend Deployment Guide - Reddit Social Listening Tool

## 🎯 Deployment Options (Choose One)

### Option 1: Railway (Recommended - Easiest)

#### Step 1: Setup Repository
1. Push your code to GitHub (including the new railway.dockerfile)
2. Make sure all files are committed

#### Step 2: Deploy to Railway
1. Go to https://railway.app
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the dockerfile

#### Step 3: Configure Environment Variables
Add these in Railway dashboard:
```
REDDIT_CLIENT_ID=I11HMqB3lvnXiGvP5AL7GA
REDDIT_CLIENT_SECRET=s19QFPqW3yiZak0UocNxIBVQWrHc3w
REDDIT_USER_AGENT=RedditSocialListener/1.0
GEMINI_API_KEY=AIzaSyDMYeVjVCmfxtMg1pJt_g5wehZVJiEsbFA
JWT_SECRET_KEY=your-super-secret-jwt-key-make-this-random
MONGO_URL=your-mongodb-atlas-connection-string
DB_NAME=reddit_social_listener
```

#### Step 4: Deploy
- Railway will automatically deploy
- Copy the deployment URL (e.g., https://your-app.railway.app)

### Option 2: Render (Free Tier Available)

#### Step 1: Setup
1. Go to https://render.com
2. Connect your GitHub account
3. Create new "Web Service"
4. Select your repository

#### Step 2: Configure Build
```
Build Command: pip install -r backend/requirements.txt
Start Command: cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
```

#### Step 3: Environment Variables
Add the same variables as Railway

### Option 3: Heroku

#### Step 1: Create Heroku App
```bash
# Install Heroku CLI
npm install -g heroku

# Login
heroku login

# Create app
heroku create your-reddit-api

# Set buildpack
heroku buildpacks:set heroku/python
```

#### Step 2: Configure for Heroku
Create Procfile:
```
web: cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT
```

#### Step 3: Set Environment Variables
```bash
heroku config:set REDDIT_CLIENT_ID=I11HMqB3lvnXiGvP5AL7GA
heroku config:set REDDIT_CLIENT_SECRET=s19QFPqW3yiZak0UocNxIBVQWrHc3w
heroku config:set REDDIT_USER_AGENT=RedditSocialListener/1.0
heroku config:set GEMINI_API_KEY=AIzaSyDMYeVjVCmfxtMg1pJt_g5wehZVJiEsbFA
heroku config:set JWT_SECRET_KEY=your-super-secret-jwt-key
heroku config:set MONGO_URL=your-mongodb-connection-string
heroku config:set DB_NAME=reddit_social_listener
```

## 🗄️ Database Setup

### MongoDB Atlas (Required)
1. Follow MONGODB_SETUP.md instructions
2. Create free M0 cluster
3. Get connection string
4. Add to MONGO_URL environment variable

### ⚠️ Important Note about Neon
Neon is a PostgreSQL service, but our app requires MongoDB. You'll need to use MongoDB Atlas instead.

## 🔄 Complete Deployment Process

### Step 1: Database Setup
1. Set up MongoDB Atlas (see MONGODB_SETUP.md)
2. Get your connection string

### Step 2: Backend Deployment
1. Choose a platform (Railway recommended)
2. Deploy backend with environment variables
3. Test backend URL: https://your-backend-url.com/api/health

### Step 3: Update Frontend
1. Update Netlify environment variable:
   ```
   REACT_APP_BACKEND_URL=https://your-backend-url.com
   ```
2. Redeploy Netlify site

### Step 4: Test Complete System
1. Visit your Netlify frontend URL
2. Test user registration/login
3. Test Reddit search functionality
4. Test dashboard analytics

## 🛠️ Troubleshooting

### Common Issues:

#### Backend won't start:
- Check all environment variables are set
- Verify MongoDB connection string
- Check deployment logs

#### CORS errors:
- Ensure frontend URL is in CORS origins
- Check REACT_APP_BACKEND_URL is correct

#### Authentication errors:
- Verify JWT_SECRET_KEY is set
- Check Reddit API credentials

### Testing Backend Deployment:
```bash
# Test health endpoint
curl https://your-backend-url.com/api/health

# Should return:
# {"status":"healthy","reddit_api":true,"database":true,"gemini_api":true}
```

## 📞 Quick Start Commands

### For Railway:
1. `git push origin main` (push to GitHub)
2. Connect GitHub repo to Railway
3. Add environment variables
4. Deploy automatically

### For Render:
1. Connect GitHub repo
2. Set build/start commands
3. Add environment variables
4. Deploy

## 🎯 Final Checklist
- [ ] MongoDB Atlas cluster created
- [ ] Backend deployed with all environment variables
- [ ] Backend health check returns success
- [ ] Frontend REACT_APP_BACKEND_URL updated
- [ ] Frontend redeployed on Netlify
- [ ] Full app functionality tested

Your Reddit Social Listening Tool will be fully deployed! 🚀