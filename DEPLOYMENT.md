# Reddit Social Listening Tool - Deployment Guide

## 🚀 Netlify Deployment Instructions

### Prerequisites
1. GitHub repository with your code
2. Netlify account (free tier works)
3. Deployed backend API (see Backend Deployment section)

### Frontend Deployment to Netlify

#### Option 1: Through Netlify Dashboard (Recommended)
1. **Connect GitHub Repository**:
   - Go to [Netlify Dashboard](https://app.netlify.com)
   - Click "New site from Git"
   - Choose GitHub and authorize Netlify
   - Select your repository

2. **Configure Build Settings**:
   ```
   Base directory: frontend
   Build command: yarn build
   Publish directory: frontend/build
   ```

3. **Environment Variables**:
   - Go to Site Settings → Environment Variables
   - Add: `REACT_APP_BACKEND_URL` = `your-backend-api-url`
   - Add: `GENERATE_SOURCEMAP` = `false`

4. **Deploy**:
   - Click "Deploy site"
   - Wait for build to complete

#### Option 2: Netlify CLI
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login to Netlify
netlify login

# Build the project
cd frontend
yarn build

# Deploy
netlify deploy --prod --dir=build
```

### Backend Deployment Options

#### Option 1: Railway (Recommended for FastAPI)
1. Connect GitHub repository to Railway
2. Set environment variables:
   ```
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USER_AGENT=your_app_name
   GEMINI_API_KEY=your_gemini_api_key
   JWT_SECRET_KEY=your_jwt_secret
   MONGO_URL=your_mongodb_connection_string
   ```
3. Railway will auto-deploy from your backend folder

#### Option 2: Render
1. Connect GitHub repository
2. Choose "Web Service"
3. Configure:
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn server:app --host 0.0.0.0 --port $PORT
   ```

#### Option 3: Heroku
1. Create new Heroku app
2. Set buildpack: `heroku/python`
3. Configure environment variables
4. Deploy from GitHub

### Database Setup (MongoDB)

#### Option 1: MongoDB Atlas (Free Tier)
1. Create account at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create cluster (free tier: M0 Sandbox)
3. Create database user
4. Whitelist IP addresses (0.0.0.0/0 for development)
5. Copy connection string

#### Option 2: Local MongoDB (Development)
```bash
# Install MongoDB locally
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb

# Start MongoDB
mongod
```

### Environment Variables Summary

#### Frontend (.env.production)
```
REACT_APP_BACKEND_URL=https://your-backend-domain.com
GENERATE_SOURCEMAP=false
```

#### Backend
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=YourAppName/1.0
GEMINI_API_KEY=your_gemini_api_key
JWT_SECRET_KEY=your-super-secret-jwt-key
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/database
DB_NAME=reddit_social_listener
```

### Troubleshooting Common Issues

#### 404 Errors on Netlify
- ✅ **Fixed**: `_redirects` file created
- ✅ **Fixed**: `netlify.toml` configuration added

#### Build Failures
```bash
# Clear cache and reinstall dependencies
rm -rf node_modules package-lock.json yarn.lock
yarn install
yarn build
```

#### CORS Issues
- Ensure backend CORS is configured for your Netlify domain
- Update backend CORS origins to include your Netlify URL

#### Environment Variables Not Working
- Check spelling of environment variable names
- Restart build after adding environment variables
- Ensure variables start with `REACT_APP_` for frontend

### Post-Deployment Checklist
- [ ] Frontend loads without 404 errors
- [ ] Authentication works (login/register)
- [ ] Reddit search functionality works
- [ ] Dashboard displays data
- [ ] AI summarization works
- [ ] CSV export functions properly

### Support
If you encounter issues:
1. Check Netlify build logs
2. Check browser console for errors
3. Verify all environment variables are set
4. Ensure backend is deployed and accessible

## 🎯 Quick Start
1. Deploy backend to Railway/Render/Heroku
2. Update `REACT_APP_BACKEND_URL` in Netlify environment variables
3. Deploy frontend to Netlify using GitHub integration
4. Test all functionality

Your Reddit Social Listening Tool will be live! 🚀