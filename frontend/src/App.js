import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [keyword, setKeyword] = useState('');
  const [subreddit, setSubreddit] = useState('all');
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [savedKeywords, setSavedKeywords] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  
  // Filter states
  const [minUpvotes, setMinUpvotes] = useState('');
  const [minComments, setMinComments] = useState('');
  const [maxUpvotes, setMaxUpvotes] = useState('');
  const [maxComments, setMaxComments] = useState('');
  const [subredditFilter, setSubredditFilter] = useState('');
  
  // UI states
  const [activeTab, setActiveTab] = useState('search');
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchSavedKeywords();
    fetchSearchHistory();
  }, []);

  const fetchSavedKeywords = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/saved-keywords`);
      if (response.ok) {
        const data = await response.json();
        setSavedKeywords(data);
      }
    } catch (error) {
      console.error('Error fetching saved keywords:', error);
    }
  };

  const fetchSearchHistory = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/search-history`);
      if (response.ok) {
        const data = await response.json();
        setSearchHistory(data);
      }
    } catch (error) {
      console.error('Error fetching search history:', error);
    }
  };

  const searchPosts = async (searchKeyword = keyword, searchSubreddit = subreddit) => {
    if (!searchKeyword.trim()) {
      alert('Please enter a keyword to search');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/search-posts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword: searchKeyword,
          subreddit: searchSubreddit,
          limit: 50
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setPosts(data);
        fetchSearchHistory(); // Refresh search history
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error searching posts:', error);
      alert('Error searching posts. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const saveKeyword = async () => {
    if (!keyword.trim()) {
      alert('Please enter a keyword to save');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/save-keyword`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          keyword: keyword,
          subreddit: subreddit
        }),
      });

      if (response.ok) {
        fetchSavedKeywords();
        alert('Keyword saved successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error saving keyword:', error);
      alert('Error saving keyword');
    }
  };

  const deleteKeyword = async (keywordId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/saved-keywords/${keywordId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        fetchSavedKeywords();
        alert('Keyword deleted successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error deleting keyword:', error);
      alert('Error deleting keyword');
    }
  };

  const applyFilters = () => {
    const filtered = posts.filter(post => {
      if (minUpvotes && post.upvotes < parseInt(minUpvotes)) return false;
      if (maxUpvotes && post.upvotes > parseInt(maxUpvotes)) return false;
      if (minComments && post.comments < parseInt(minComments)) return false;
      if (maxComments && post.comments > parseInt(maxComments)) return false;
      if (subredditFilter && !post.subreddit.toLowerCase().includes(subredditFilter.toLowerCase())) return false;
      return true;
    });
    return filtered;
  };

  const filteredPosts = applyFilters();

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
            <div className="flex space-x-4">
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
                onClick={() => setActiveTab('keywords')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === 'keywords' 
                    ? 'bg-blue-500 text-white' 
                    : 'text-gray-600 hover:text-blue-600'
                }`}
              >
                Saved Keywords
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
              </div>
            </div>

            {/* Filters */}
            {showFilters && (
              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
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
                      Subreddit Filter
                    </label>
                    <input
                      type="text"
                      value={subredditFilter}
                      onChange={(e) => setSubredditFilter(e.target.value)}
                      placeholder="Filter by subreddit"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
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
                        </div>
                        
                        {post.body && (
                          <p className="text-gray-700 mb-3 line-clamp-3">{post.body}</p>
                        )}
                        
                        <div className="flex gap-2">
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
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
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
                      <h3 className="font-semibold text-gray-900">{savedKeyword.keyword}</h3>
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
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600">
                      <span>r/{search.subreddit}</span>
                      <span>{search.post_count} posts found</span>
                    </div>
                    
                    <button
                      onClick={() => {
                        setKeyword(search.keyword);
                        setSubreddit(search.subreddit);
                        setActiveTab('search');
                        searchPosts(search.keyword, search.subreddit);
                      }}
                      className="mt-3 bg-gray-500 text-white px-3 py-1.5 rounded-lg hover:bg-gray-600 transition-colors text-sm"
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