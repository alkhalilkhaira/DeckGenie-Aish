import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

from src.models.presentation import db, SearchCache

class DataService:
    """Service for fetching and caching research data from various sources."""
    
    def __init__(self):
        self.cache_duration_hours = 24
        self.max_results_per_source = 5
        self.request_timeout = 10
    
    def search_web_content(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for web content using multiple strategies.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with content
        """
        # Check cache first
        cached_results = self._get_cached_results(query, 'web')
        if cached_results:
            return cached_results[:max_results]
        
        results = []
        
        # Try different search strategies
        try:
            # Strategy 1: Wikipedia search
            wikipedia_results = self._search_wikipedia(query, max_results // 2)
            results.extend(wikipedia_results)
            
            # Strategy 2: General web search (simulated)
            web_results = self._search_general_web(query, max_results - len(results))
            results.extend(web_results)
            
        except Exception as e:
            print(f"Error in web search: {e}")
        