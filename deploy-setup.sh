#!/bin/bash

echo "🚀 Starting Reddit Social Listening Tool..."

# Check if we're in the right directory
if [ ! -f "netlify.toml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
if [ ! -d "node_modules" ]; then
    yarn install
fi

# Build the frontend
echo "🔨 Building frontend..."
yarn build

echo "✅ Build complete! You can now deploy to Netlify."
echo ""
echo "📋 Next steps:"
echo "1. Commit and push your changes to GitHub"
echo "2. Connect your GitHub repo to Netlify"
echo "3. Set build settings: Base directory: frontend, Build command: yarn build, Publish directory: frontend/build"
echo "4. Add environment variable: REACT_APP_BACKEND_URL=your-backend-url"
echo "5. Deploy!"
echo ""
echo "📖 See DEPLOYMENT.md for detailed instructions"