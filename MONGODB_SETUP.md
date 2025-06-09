# MongoDB Atlas Setup Guide

## 1. Create MongoDB Atlas Account
- Go to https://www.mongodb.com/atlas
- Sign up for free account
- Create organization and project

## 2. Create Free Cluster
- Choose "Create a deployment"
- Select "M0 Sandbox" (Free Forever)
- Choose your preferred cloud provider and region
- Name your cluster (e.g., "reddit-listener")

## 3. Create Database User
- Go to "Database Access" in left sidebar
- Click "Add New Database User"
- Choose "Password" authentication
- Username: admin (or your preferred username)
- Password: Generate secure password and save it
- Database User Privileges: "Read and write to any database"

## 4. Configure Network Access
- Go to "Network Access" in left sidebar
- Click "Add IP Address"
- For development: Click "Allow access from anywhere" (0.0.0.0/0)
- For production: Add specific IP addresses of your hosting service

## 5. Get Connection String
- Go to "Database" in left sidebar
- Click "Connect" on your cluster
- Choose "Connect your application"
- Copy the connection string:
  mongodb+srv://admin:<password>@reddit-listener.xxxxx.mongodb.net/?retryWrites=true&w=majority

## 6. Update Connection String
Replace <password> with your actual password:
mongodb+srv://admin:yourpassword@reddit-listener.xxxxx.mongodb.net/reddit_social_listener?retryWrites=true&w=majority

## Example Environment Variables:
MONGO_URL=mongodb+srv://admin:yourpassword@reddit-listener.xxxxx.mongodb.net/reddit_social_listener?retryWrites=true&w=majority
DB_NAME=reddit_social_listener