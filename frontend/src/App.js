import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Auth context
const AuthContext = React.createContext();

// Date formatting helper
const formatDate = (timestamp) => {
  return new Date(timestamp * 1000).toLocaleDateString();
};

const formatTimeAgo = (timestamp) => {
  const now = new Date();
  const postDate = new Date(timestamp * 1000);
  const diffInHours = Math.floor((now - postDate) / (1000 * 60 * 60));
  
  if (diffInHours < 1) return 'Less than 1 hour ago';
  if (diffInHours < 24) return `${diffInHours} hours ago`;
  const diffInDays = Math.floor(diffInHours / 24);
  return `${diffInDays} days ago`;
};

const getSentimentColor = (score) => {
  if (score >= 7) return 'text-green-600';
  if (score >= 4) return 'text-yellow-600';
  return 'text-red-600';
};

const getSentimentLabel = (score) => {
  if (score >= 7) return 'Positive';
  if (score >= 4) return 'Neutral';
  return 'Negative';
};

// Login/Register Component
function AuthComponent({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    full_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/api/login' : '/api/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;

      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        onLogin(data.user, data.access_token);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'An error occurred');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-white font-bold text-2xl">R</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Reddit Social Listening</h1>
          <p className="text-gray-600 mt-2">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </p>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Full Name
              </label>
              <input
                type="text"
                required
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter your full name"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              required
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 transition-all"
          >
            {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Sign Up')}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [keyword, setKeyword] = useState('');
  const [subreddit, setSubreddit] = useState('all');
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savedKeywords, setSavedKeywords] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  
  // Filter states
  const [minUpvotes, setMinUpvotes] = useState('');
  const [minComments, setMinComments] = useState('');
  const [maxUpvotes, setMaxUpvotes] = useState('');
  const [maxComments, setMaxComments] = useState('');
  const [subredditFilter, setSubredditFilter] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [minSentiment, setMinSentiment] = useState('');
  const [maxSentiment, setMaxSentiment] = useState('');
  
  // UI states
  const [activeTab, setActiveTab] = useState('search');
  const [showFilters, setShowFilters] = useState(false);
  const [summarizing, setSummarizing] = useState({});

  useEffect(() => {
    // Check for existing auth
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    if (user && token) {
      fetchSavedKeywords();
      fetchSearchHistory();
      fetchDashboardData();
    }
  }, [user, token]);

  const makeAuthenticatedRequest = async (url, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers
    };

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers
    });

    if (response.status === 401) {
      // Token expired or invalid
      handleLogout();
      throw new Error('Authentication failed');
    }

    return response;
  };

  const handleLogin = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  };

  const fetchSavedKeywords = async () => {
    try {
      const response = await makeAuthenticatedRequest('/api/saved-keywords');
      if (response.ok) {
        const data = await response.json();
        setSavedKeywords(data || []);
      }
    } catch (error) {
      console.error('Error fetching saved keywords:', error);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const response = await makeAuthenticatedRequest('/api/search-history');
      if (response.ok) {
        const data = await response.json();
        setSearchHistory(data || []);
      }
    } catch (error) {
      console.error('Error fetching search history:', error);
    }
  };

  const fetchDashboardData = async () => {
    try {
      console.log('Fetching dashboard data...');
      const response = await makeAuthenticatedRequest('/api/dashboard');
      if (response.ok) {
        const data = await response.json();
        console.log('Dashboard data received:', data);
        setDashboardData(data);
      } else {
        console.error('Failed to fetch dashboard data:', response.status, response.statusText);
        // Set empty dashboard data on error
        setDashboardData({
          recent_searches: [],
          sentiment_trends: [],
          keyword_stats: [],
          summary_stats: { total_searches: 0, total_posts: 0, avg_sentiment: null }
        });
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Set empty dashboard data on error
      setDashboardData({
        recent_searches: [],
        sentiment_trends: [],
        keyword_stats: [],
        summary_stats: { total_searches: 0, total_posts: 0, avg_sentiment: null }
      });
    }
  };

  const searchPosts = async (searchKeyword = keyword, searchSubreddit = subreddit) => {
    if (!searchKeyword.trim()) {
      alert('Please enter a keyword to search');
      return;
    }

    setLoading(true);
    try {
      const response = await makeAuthenticatedRequest('/api/search-posts', {
        method: 'POST',
        body: JSON.stringify({
          keyword: searchKeyword,
          subreddit: searchSubreddit,
          limit: 50
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setPosts(Array.isArray(data) ? data : []);
        fetchSearchHistory();
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
        setPosts([]);
      }
    } catch (error) {
      console.error('Error searching posts:', error);
      alert('Error searching posts. Please check your connection.');
      setPosts([]);
    } finally {
      setLoading(false);
    }
  };

  const summarizePost = async (postId, content) => {
    setSummarizing(prev => ({ ...prev, [postId]: true }));
    
    try {
      const response = await makeAuthenticatedRequest('/api/summarize', {
        method: 'POST',
        body: JSON.stringify({ content }),
      });

      if (response.ok) {
        const data = await response.json();
        setPosts(prevPosts => prevPosts.map(post => 
          post.id === postId ? { ...post, summary: data.summary } : post
        ));
      } else {
        const errorData = await response.json();
        alert(`Error summarizing: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error summarizing:', error);
      alert('Error generating summary');
    } finally {
      setSummarizing(prev => ({ ...prev, [postId]: false }));
    }
  };

  const saveKeyword = async () => {
    if (!keyword.trim()) {
      alert('Please enter a keyword to save');
      return;
    }

    try {
      const response = await makeAuthenticatedRequest('/api/save-keyword', {
        method: 'POST',
        body: JSON.stringify({
          keyword: keyword,
          subreddit: subreddit
        }),
      });

      if (response.ok) {
        fetchSavedKeywords();
        alert('Keyword saved successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error saving keyword:', error);
      alert('Error saving keyword');
    }
  };

  const deleteKeyword = async (keywordId) => {
    try {
      const response = await makeAuthenticatedRequest(`/api/saved-keywords/${keywordId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchSavedKeywords();
        alert('Keyword deleted successfully!');
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error deleting keyword:', error);
      alert('Error deleting keyword');
    }
  };

  const exportToCSV = async () => {
    try {
      const params = new URLSearchParams();
      if (keyword) params.append('keyword', keyword);
      if (startDate) params.append('start_date', startDate);
      if (endDate) params.append('end_date', endDate);

      const response = await makeAuthenticatedRequest(`/api/export/csv?${params.toString()}`);

      if (response.ok) {
        const data = await response.json();
        
        // Create and download CSV file
        const blob = new Blob([data.content], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = data.filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const errorData = await response.json();
        alert(`Error: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('Error exporting:', error);
      alert('Error exporting data');
    }
  };

  const applyFilters = () => {
    return posts.filter(post => {
      if (minUpvotes && post.upvotes < parseInt(minUpvotes)) return false;
      if (maxUpvotes && post.upvotes > parseInt(maxUpvotes)) return false;
      if (minComments && post.comments < parseInt(minComments)) return false;
      if (maxComments && post.comments > parseInt(maxComments)) return false;
      if (subredditFilter && !post.subreddit.toLowerCase().includes(subredditFilter.toLowerCase())) return false;
      if (minSentiment && (post.sentiment_score === null || post.sentiment_score < parseFloat(minSentiment))) return false;
      if (maxSentiment && (post.sentiment_score === null || post.sentiment_score > parseFloat(maxSentiment))) return false;
      
      // Date filters
      if (startDate || endDate) {
        const postDate = new Date(post.created_utc * 1000);
        if (startDate && postDate < new Date(startDate)) return false;
        if (endDate && postDate > new Date(endDate)) return false;
      }
      
      return true;
    });
  };

  const filteredPosts = applyFilters();

  if (!user) {
    return <AuthComponent onLogin={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-600 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xl">R</span>
              </div>
              <h1 className="ml-3 text-3xl font-bold text-gray-900">Reddit Social Listening Tool</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">Welcome, {user.full_name}</span>
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('search')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === 'search' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-600 hover:text-blue-600'
                  }`}
                >
                  Search
                </button>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === 'dashboard' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-600 hover:text-blue-600'
                  }`}
                >
                  Dashboard
                </button>
                <button
                  onClick={() => setActiveTab('keywords')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === 'keywords' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-600 hover:text-blue-600'
                  }`}
                >
                  Keywords
                </button>
                <button
                  onClick={() => setActiveTab('history')}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    activeTab === 'history' 
                      ? 'bg-blue-500 text-white' 
                      : 'text-gray-600 hover:text-blue-600'
                  }`}
                >
                  History
                </button>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            {/* Search Form */}
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Search Reddit Posts</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Keyword *
                  </label>
                  <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="Enter keyword to search"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    onKeyPress={(e) => e.key === 'Enter' && searchPosts()}
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Subreddit
                  </label>
                  <input
                    type="text"
                    value={subreddit}
                    onChange={(e) => setSubreddit(e.target.value)}
                    placeholder="all (default) or specific subreddit"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  />
                </div>
                
                <div className="flex items-end">
                  <button
                    onClick={() => searchPosts()}
                    disabled={!keyword.trim() || loading}
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:from-blue-600 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                  >
                    {loading ? 'Searching...' : 'Search Reddit'}
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  onClick={saveKeyword}
                  disabled={!keyword.trim()}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Save Keyword
                </button>
                
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  {showFilters ? 'Hide Filters' : 'Show Filters'}
                </button>

                <button
                  onClick={exportToCSV}
                  disabled={posts.length === 0}
                  className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Export CSV
                </button>
              </div>
            </div>

            {/* Enhanced Filters */}
            {showFilters && (
              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Filters</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Upvotes
                    </label>
                    <input
                      type="number"
                      value={minUpvotes}
                      onChange={(e) => setMinUpvotes(e.target.value)}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Upvotes
                    </label>
                    <input
                      type="number"
                      value={maxUpvotes}
                      onChange={(e) => setMaxUpvotes(e.target.value)}
                      placeholder="No limit"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Min Comments
                    </label>
                    <input
                      type="number"
                      value={minComments}
                      onChange={(e) => setMinComments(e.target.value)}
                      placeholder="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Comments
                    </label>
                    <input
                      type="number"
                      value={maxComments}
                      onChange={(e) => setMaxComments(e.target.value)}
                      placeholder="No limit"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Date
                    </label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Date
                    </label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Sentiment (0-10)
                    </label>
                    <div className="flex gap-1">
                      <input
                        type="number"
                        min="0"
                        max="10"
                        step="0.1"
                        value={minSentiment}
                        onChange={(e) => setMinSentiment(e.target.value)}
                        placeholder="Min"
                        className="w-full px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-xs"
                      />
                      <input
                        type="number"
                        min="0"
                        max="10"
                        step="0.1"
                        value={maxSentiment}
                        onChange={(e) => setMaxSentiment(e.target.value)}
                        placeholder="Max"
                        className="w-full px-2 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-xs"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Results */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex justify-between items-center">
                  <h3 className="text-xl font-semibold text-gray-900">
                    Search Results ({filteredPosts.length} posts)
                  </h3>
                  {posts.length > 0 && filteredPosts.length !== posts.length && (
                    <span className="text-sm text-gray-500">
                      Showing {filteredPosts.length} of {posts.length} posts
                    </span>
                  )}
                </div>
              </div>
              
              <div className="max-h-screen overflow-y-auto">
                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
                    <span className="ml-3 text-gray-600">Searching Reddit...</span>
                  </div>
                ) : filteredPosts.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 text-6xl mb-4">🔍</div>
                    <p className="text-gray-500 text-lg">
                      {posts.length === 0 ? 'No search performed yet' : 'No posts match your filters'}
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {filteredPosts.map((post) => (
                      <div key={post.id} className="p-6 hover:bg-gray-50 transition-colors">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="text-lg font-semibold text-gray-900 hover:text-blue-600 cursor-pointer line-clamp-2">
                            <a href={post.permalink} target="_blank" rel="noopener noreferrer">
                              {post.title}
                            </a>
                          </h4>
                        </div>
                        
                        <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-3">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                            r/{post.subreddit}
                          </span>
                          <span>by {post.author}</span>
                          <span>{formatTimeAgo(post.created_utc)}</span>
                          <span className="inline-flex items-center">
                            <span className="text-green-600 mr-1">↑</span>
                            {post.upvotes}
                          </span>
                          <span className="inline-flex items-center">
                            <span className="mr-1">💬</span>
                            {post.comments}
                          </span>
                          {post.sentiment_score !== null && (
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(post.sentiment_score)} bg-gray-100`}>
                              😊 {post.sentiment_score.toFixed(1)} ({getSentimentLabel(post.sentiment_score)})
                            </span>
                          )}
                        </div>
                        
                        {post.body && (
                          <p className="text-gray-700 mb-3 line-clamp-3">{post.body}</p>
                        )}

                        {post.summary && (
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                            <h5 className="font-medium text-blue-900 mb-1">AI Summary:</h5>
                            <p className="text-blue-800 text-sm">{post.summary}</p>
                          </div>
                        )}
                        
                        <div className="flex gap-2 flex-wrap">
                          <a
                            href={post.permalink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-1.5 bg-orange-500 text-white text-sm rounded-lg hover:bg-orange-600 transition-colors"
                          >
                            View on Reddit →
                          </a>
                          
                          {post.url !== post.permalink && (
                            <a
                              href={post.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center px-3 py-1.5 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                            >
                              Original Link →
                            </a>
                          )}

                          {!post.summary && (
                            <button
                              onClick={() => summarizePost(post.id, `${post.title} ${post.body || ''}`)}
                              disabled={summarizing[post.id]}
                              className="inline-flex items-center px-3 py-1.5 bg-purple-500 text-white text-sm rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                              {summarizing[post.id] ? 'Summarizing...' : '🤖 Summarize'}
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Analytics Dashboard</h2>
              
              {dashboardData ? (
                <div className="space-y-6">
                  {/* Summary Stats */}
                  {dashboardData.summary_stats && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                      <div className="bg-blue-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-blue-600">{dashboardData.summary_stats.total_searches}</div>
                        <div className="text-sm text-blue-800">Total Searches</div>
                      </div>
                      <div className="bg-green-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-green-600">{dashboardData.summary_stats.total_posts}</div>
                        <div className="text-sm text-green-800">Posts Analyzed</div>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-4 text-center">
                        <div className="text-2xl font-bold text-purple-600">
                          {dashboardData.summary_stats.avg_sentiment ? dashboardData.summary_stats.avg_sentiment.toFixed(1) : 'N/A'}
                        </div>
                        <div className="text-sm text-purple-800">Avg Sentiment</div>
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {/* Recent Searches */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">Recent Searches</h3>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {dashboardData.recent_searches?.length > 0 ? dashboardData.recent_searches.slice(0, 5).map((search, index) => (
                          <div key={index} className="text-sm">
                            <span className="font-medium">"{search.keyword}"</span>
                            <span className="text-gray-600"> in r/{search.subreddit}</span>
                            <div className="text-xs text-gray-500">
                              {search.post_count} posts • {new Date(search.timestamp).toLocaleDateString()}
                              {search.avg_sentiment && (
                                <span className={`ml-2 ${getSentimentColor(search.avg_sentiment)}`}>
                                  Sentiment: {search.avg_sentiment.toFixed(1)}
                                </span>
                              )}
                            </div>
                          </div>
                        )) : (
                          <div className="text-sm text-gray-500">No searches yet</div>
                        )}
                      </div>
                    </div>

                    {/* Top Keywords */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">Top Keywords</h3>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {dashboardData.keyword_stats?.length > 0 ? dashboardData.keyword_stats.slice(0, 5).map((stat, index) => (
                          <div key={index} className="text-sm">
                            <span className="font-medium">"{stat._id}"</span>
                            <div className="text-xs text-gray-500">
                              {stat.search_count} searches • {stat.total_posts} posts
                              {stat.avg_sentiment && (
                                <span className={`ml-2 ${getSentimentColor(stat.avg_sentiment)}`}>
                                  Sentiment: {stat.avg_sentiment.toFixed(1)}
                                </span>
                              )}
                            </div>
                          </div>
                        )) : (
                          <div className="text-sm text-gray-500">No keywords yet</div>
                        )}
                      </div>
                    </div>

                    {/* Sentiment Trends */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">Sentiment Trends</h3>
                      <div className="space-y-2 max-h-64 overflow-y-auto">
                        {dashboardData.sentiment_trends?.length > 0 ? dashboardData.sentiment_trends.slice(0, 7).map((trend, index) => (
                          <div key={index} className="text-sm">
                            <span className="font-medium">{trend._id}</span>
                            <div className="text-xs text-gray-500">
                              {trend.post_count} posts • 
                              <span className={`ml-1 ${getSentimentColor(trend.avg_sentiment)}`}>
                                Avg sentiment: {trend.avg_sentiment.toFixed(1)}
                              </span>
                            </div>
                          </div>
                        )) : (
                          <div className="text-sm text-gray-500">No sentiment data yet</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Additional Charts Section */}
                  {dashboardData.sentiment_trends?.length > 0 && (
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">Sentiment Over Time</h3>
                      <div className="flex flex-wrap gap-2">
                        {dashboardData.sentiment_trends.slice(0, 10).map((trend, index) => (
                          <div key={index} className="flex items-center space-x-2 text-xs">
                            <span className="text-gray-600">{trend._id}</span>
                            <div 
                              className={`w-3 h-3 rounded-full ${
                                trend.avg_sentiment >= 7 ? 'bg-green-500' :
                                trend.avg_sentiment >= 4 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              title={`Sentiment: ${trend.avg_sentiment.toFixed(1)}`}
                            ></div>
                            <span className="text-gray-500">({trend.post_count})</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Help Section */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-medium text-blue-900 mb-2">💡 Dashboard Tips</h3>
                    <div className="text-sm text-blue-800 space-y-1">
                      <p>• Perform some searches to see analytics data</p>
                      <p>• Sentiment scores: 7-10 (Positive), 4-6 (Neutral), 0-3 (Negative)</p>
                      <p>• Data updates automatically after each search</p>
                      <p>• Use filters to refine your analysis</p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                  <p className="text-gray-500 text-lg">Loading dashboard data...</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Saved Keywords Tab */}
        {activeTab === 'keywords' && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Saved Keywords</h2>
            
            {savedKeywords.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">📝</div>
                <p className="text-gray-500 text-lg">No saved keywords yet</p>
                <p className="text-gray-400">Save keywords from the search tab to track them</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {savedKeywords.map((savedKeyword) => (
                  <div key={savedKeyword.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-900">"{savedKeyword.keyword}"</h3>
                      <button
                        onClick={() => deleteKeyword(savedKeyword.id)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        Delete
                      </button>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">
                      Subreddit: r/{savedKeyword.subreddit}
                    </p>
                    
                    <p className="text-xs text-gray-500 mb-3">
                      Saved: {new Date(savedKeyword.created_at).toLocaleDateString()}
                    </p>
                    
                    <button
                      onClick={() => {
                        setKeyword(savedKeyword.keyword);
                        setSubreddit(savedKeyword.subreddit);
                        setActiveTab('search');
                        searchPosts(savedKeyword.keyword, savedKeyword.subreddit);
                      }}
                      className="w-full bg-blue-500 text-white px-3 py-1.5 rounded-lg hover:bg-blue-600 transition-colors text-sm"
                    >
                      Search Now
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Search History Tab */}
        {activeTab === 'history' && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Search History</h2>
            
            {searchHistory.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-400 text-6xl mb-4">📊</div>
                <p className="text-gray-500 text-lg">No search history yet</p>
                <p className="text-gray-400">Your search history will appear here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {searchHistory.map((search, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-900">"{search.keyword}"</h3>
                      <span className="text-sm text-gray-500">
                        {new Date(search.timestamp).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <span>r/{search.subreddit}</span>
                      <span>{search.post_count} posts found</span>
                      {search.avg_sentiment && (
                        <span className={`${getSentimentColor(search.avg_sentiment)}`}>
                          Avg sentiment: {search.avg_sentiment.toFixed(1)}
                        </span>
                      )}
                    </div>
                    
                    <button
                      onClick={() => {
                        setKeyword(search.keyword);
                        setSubreddit(search.subreddit);
                        setActiveTab('search');
                        searchPosts(search.keyword, search.subreddit);
                      }}
                      className="bg-gray-500 text-white px-3 py-1.5 rounded-lg hover:bg-gray-600 transition-colors text-sm"
                    >
                      Search Again
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;