import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import time
import re

from src.models.presentation import db, SearchCache

class EnhancedDataService:
    """Enhanced service for fetching and managing research data for presentations."""
    
    def __init__(self):
        self.cache_duration_hours = 24
        self.max_results_per_source = 5
        self.request_timeout = 10
        self.rate_limit_delay = 1  # seconds between requests
        
    def research_topic(self, topic: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Research a topic using multiple data sources.
        
        Args:
            topic: The topic to research
            max_results: Maximum number of results to return
            
        Returns:
            List of research results with metadata
        """
        # Check cache first
        cached_results = self._get_cached_results(topic)
        if cached_results:
            return cached_results[:max_results]
        
        results = []
        
        try:
            # Search Wikipedia
            wikipedia_results = self._search_wikipedia(topic, 3)
            results.extend(wikipedia_results)
            
            # Search arXiv for academic papers
            arxiv_results = self._search_arxiv(topic, 2)
            results.extend(arxiv_results)
            
            # Add simulated web search results
            web_results = self._simulate_web_search(topic, 5)
            results.extend(web_results)
            
            # Cache results
            if results:
                self._cache_results(topic, results)
            
        except Exception as e:
            print(f"Error researching topic '{topic}': {e}")
        
        return results[:max_results]
    
    def get_statistics(self, topic: str) -> List[Dict[str, Any]]:
        """
        Get statistical data related to a topic.
        
        Args:
            topic: The topic to get statistics for
            
        Returns:
            List of statistical data points
        """
        statistics = []
        
        if 'artificial intelligence' in topic.lower() or 'ai' in topic.lower():
            statistics = [
                {
                    'title': 'Global AI Market Size',
                    'value': '$136.6 billion',
                    'year': '2022',
                    'source': 'Grand View Research',
                    'description': 'The global artificial intelligence market size was valued at USD 136.6 billion in 2022'
                },
                {
                    'title': 'AI Market Growth Rate',
                    'value': '37.3%',
                    'year': '2023-2030',
                    'source': 'Grand View Research',
                    'description': 'Expected compound annual growth rate (CAGR) from 2023 to 2030'
                },
                {
                    'title': 'Companies Using AI',
                    'value': '35%',
                    'year': '2023',
                    'source': 'IBM Global AI Adoption Index',
                    'description': 'Percentage of companies that have adopted AI in their business'
                }
            ]
        elif 'technology' in topic.lower():
            statistics = [
                {
                    'title': 'Global Tech Spending',
                    'value': '$4.6 trillion',
                    'year': '2023',
                    'source': 'Gartner',
                    'description': 'Worldwide IT spending in 2023'
                },
                {
                    'title': 'Digital Transformation Investment',
                    'value': '$2.8 trillion',
                    'year': '2025',
                    'source': 'IDC',
                    'description': 'Projected global spending on digital transformation by 2025'
                }
            ]
        
        return statistics
    
    def _search_wikipedia(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search Wikipedia for information."""
        results = []
        
        try:
            # Search for pages
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            
            # Clean query for Wikipedia
            clean_query = query.replace(' ', '_')
            
            response = requests.get(
                f"{search_url}{clean_query}",
                timeout=self.request_timeout,
                headers={'User-Agent': 'Prompt2Presentation/1.0'}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                result = {
                    'title': data.get('title', query),
                    'content': data.get('extract', ''),
                    'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                    'source': 'Wikipedia',
                    'type': 'encyclopedia',
                    'relevance_score': 0.9,
                    'last_updated': datetime.utcnow().isoformat()
                }
                
                if result['content']:
                    results.append(result)
            
            time.sleep(self.rate_limit_delay)
            
        except Exception as e:
            print(f"Error searching Wikipedia: {e}")
        
        return results[:max_results]
    
    def _search_arxiv(self, query: str, max_results: int = 2) -> List[Dict[str, Any]]:
        """Search arXiv for academic papers."""
        results = []
        
        try:
            # arXiv API search
            search_url = "http://export.arxiv.org/api/query"
            params = {
                'search_query': f'all:{query}',
                'start': 0,
                'max_results': max_results,
                'sortBy': 'relevance',
                'sortOrder': 'descending'
            }
            
            response = requests.get(
                search_url,
                params=params,
                timeout=self.request_timeout,
                headers={'User-Agent': 'Prompt2Presentation/1.0'}
            )
            
            if response.status_code == 200:
                # Parse XML response (simplified)
                content = response.text
                
                # Extract paper information using regex (simplified)
                titles = re.findall(r'<title>(.*?)</title>', content)
                summaries = re.findall(r'<summary>(.*?)</summary>', content, re.DOTALL)
                links = re.findall(r'<id>(http://arxiv.org/abs/[^<]+)</id>', content)
                
                for i, (title, summary, link) in enumerate(zip(titles[1:], summaries, links)):
                    if i >= max_results:
                        break
                    
                    result = {
                        'title': title.strip(),
                        'content': summary.strip()[:500] + '...' if len(summary.strip()) > 500 else summary.strip(),
                        'url': link,
                        'source': 'arXiv',
                        'type': 'academic_paper',
                        'relevance_score': 0.8,
                        'last_updated': datetime.utcnow().isoformat()
                    }
                    
                    results.append(result)
            
            time.sleep(self.rate_limit_delay)
            
        except Exception as e:
            print(f"Error searching arXiv: {e}")
        
        return results[:max_results]
    
    def _simulate_web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Simulate web search results with curated content."""
        simulated_results = []
        
        # AI-related content
        if 'artificial intelligence' in query.lower() or 'ai' in query.lower():
            simulated_results = [
                {
                    'title': 'The History and Evolution of Artificial Intelligence',
                    'content': 'Artificial Intelligence (AI) has evolved from a concept in science fiction to a transformative technology reshaping industries. The field began in the 1950s with pioneers like Alan Turing and John McCarthy, who coined the term "artificial intelligence" in 1956.',
                    'url': 'https://example.com/ai-history',
                    'source': 'Tech Research Institute',
                    'type': 'article',
                    'relevance_score': 0.95,
                    'last_updated': datetime.utcnow().isoformat()
                },
                {
                    'title': 'AI Impact on Modern Society and Future Trends',
                    'content': 'AI is revolutionizing healthcare, finance, transportation, and education. Machine learning algorithms are enabling personalized medicine, autonomous vehicles, and intelligent tutoring systems. The economic impact is projected to reach trillions of dollars by 2030.',
                    'url': 'https://example.com/ai-impact',
                    'source': 'Future Technology Review',
                    'type': 'analysis',
                    'relevance_score': 0.92,
                    'last_updated': datetime.utcnow().isoformat()
                },
                {
                    'title': 'Ethical Considerations in AI Development',
                    'content': 'As AI becomes more prevalent, ethical considerations around bias, privacy, and job displacement become critical. Organizations are developing AI ethics frameworks to ensure responsible development and deployment of AI systems.',
                    'url': 'https://example.com/ai-ethics',
                    'source': 'AI Ethics Council',
                    'type': 'policy',
                    'relevance_score': 0.88,
                    'last_updated': datetime.utcnow().isoformat()
                }
            ]
        
        # Technology-related content
        elif 'technology' in query.lower():
            simulated_results = [
                {
                    'title': 'Digital Transformation in the Modern Era',
                    'content': 'Digital transformation is reshaping how businesses operate, from cloud computing to IoT devices. Companies are investing heavily in digital infrastructure to remain competitive in the digital economy.',
                    'url': 'https://example.com/digital-transformation',
                    'source': 'Digital Business Journal',
                    'type': 'article',
                    'relevance_score': 0.90,
                    'last_updated': datetime.utcnow().isoformat()
                }
            ]
        
        # Business-related content
        elif 'business' in query.lower() or 'marketing' in query.lower():
            simulated_results = [
                {
                    'title': 'Modern Marketing Strategies for 2025',
                    'content': 'Marketing in 2025 will be dominated by AI-powered personalization, voice search optimization, and sustainable brand messaging. Companies must adapt to changing consumer preferences and digital-first approaches.',
                    'url': 'https://example.com/marketing-2025',
                    'source': 'Marketing Insights',
                    'type': 'strategy',
                    'relevance_score': 0.87,
                    'last_updated': datetime.utcnow().isoformat()
                }
            ]
        
        # Default content
        else:
            simulated_results = [
                {
                    'title': f'Comprehensive Guide to {query}',
                    'content': f'This comprehensive guide covers the key aspects of {query}, including current trends, best practices, and future outlook. Industry experts provide insights into the most important developments and their implications.',
                    'url': f'https://example.com/{query.lower().replace(" ", "-")}',
                    'source': 'Industry Research',
                    'type': 'guide',
                    'relevance_score': 0.75,
                    'last_updated': datetime.utcnow().isoformat()
                }
            ]
        
        return simulated_results[:max_results]
    
    def _get_cached_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        
        cached = SearchCache.query.filter_by(query_hash=query_hash).first()
        
        if cached and cached.expires_at > datetime.utcnow():
            cached.hit_count += 1
            db.session.commit()
            
            return json.loads(cached.results_json)
        
        return None
    
    def _cache_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Cache search results."""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        expires_at = datetime.utcnow() + timedelta(hours=self.cache_duration_hours)
        
        existing = SearchCache.query.filter_by(query_hash=query_hash).first()
        
        if existing:
            existing.results_json = json.dumps(results)
            existing.expires_at = expires_at
            existing.hit_count += 1
        else:
            cache_entry = SearchCache(
                query_hash=query_hash,
                query_text=query,
                source_type='web',
                results_json=json.dumps(results),
                expires_at=expires_at
            )
            db.session.add(cache_entry)
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error caching results: {e}")
            db.session.rollback()
    
    def validate_source(self, url: str) -> Dict[str, Any]:
        """Validate and get metadata for a source URL."""
        try:
            response = requests.head(url, timeout=5)
            
            return {
                'valid': response.status_code == 200,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'last_modified': response.headers.get('last-modified', ''),
                'domain': urlparse(url).netloc
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'domain': urlparse(url).netloc if url else ''
            }
    
    def extract_key_facts(self, content: str, max_facts: int = 5) -> List[str]:
        """Extract key facts from content text."""
        # Simple fact extraction (in production, would use NLP)
        sentences = content.split('. ')
        
        # Filter for sentences that look like facts
        facts = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence) > 20 and 
                any(keyword in sentence.lower() for keyword in ['is', 'are', 'was', 'were', 'has', 'have', 'will', 'can', 'shows', 'indicates', 'research', 'study', 'data', 'statistics'])):
                facts.append(sentence)
                if len(facts) >= max_facts:
                    break
        
        return facts
    
    def get_trending_topics(self, category: str = 'technology') -> List[str]:
        """Get trending topics in a category."""
        # Simulated trending topics
        trending = {
            'technology': [
                'Artificial Intelligence',
                'Quantum Computing',
                'Blockchain Technology',
                'Internet of Things',
                'Cybersecurity'
            ],
            'business': [
                'Digital Transformation',
                'Remote Work',
                'Sustainability',
                'Customer Experience',
                'Data Analytics'
            ],
            'science': [
                'Climate Change',
                'Space Exploration',
                'Biotechnology',
                'Renewable Energy',
                'Medical Research'
            ]
        }
        
        return trending.get(category, trending['technology'])

