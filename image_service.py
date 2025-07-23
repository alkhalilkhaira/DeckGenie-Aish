import os
import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
import shutil
from PIL import Image
import io

from src.models.presentation import db, SearchCache

class ImageService:
    """Service for searching, downloading, and managing images for presentations."""
    
    def __init__(self):
        self.cache_duration_hours = 24
        self.max_images_per_search = 8
        self.request_timeout = 10
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        
        # Create images directory
        self.images_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'images')
        os.makedirs(self.images_dir, exist_ok=True)
    
    def search_images(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for images related to a query.
        
        Args:
            query: Search query for images
            max_results: Maximum number of images to return
            
        Returns:
            List of image results with metadata
        """
        # Check cache first
        cached_results = self._get_cached_image_results(query)
        if cached_results:
            return cached_results[:max_results]
        
        results = []
        
        try:
            # For now, use local curated images and simulate search
            # In production, this would integrate with image APIs like Unsplash, Pexels, etc.
            results = self._search_curated_images(query, max_results)
            
            # Cache results
            if results:
                self._cache_image_results(query, results)
                
        except Exception as e:
            print(f"Error searching images: {e}")
        
        return results[:max_results]
    
    def download_image(self, image_url: str, filename: str = None) -> Optional[str]:
        """
        Download an image from URL and save locally.
        
        Args:
            image_url: URL of the image to download
            filename: Optional custom filename
            
        Returns:
            Local file path if successful, None otherwise
        """
        try:
            if not filename:
                # Generate filename from URL
                parsed_url = urlparse(image_url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    filename = f"image_{hashlib.md5(image_url.encode()).hexdigest()[:8]}.jpg"
            
            # Ensure filename has supported extension
            if not any(filename.lower().endswith(ext) for ext in self.supported_formats):
                filename += '.jpg'
            
            file_path = os.path.join(self.images_dir, filename)
            
            # Download image
            response = requests.get(image_url, timeout=self.request_timeout, stream=True)
            response.raise_for_status()
            
            # Save image
            with open(file_path, 'wb') as f:
                shutil.copyfileobj(response.raw, f)
            
            # Validate and optimize image
            optimized_path = self._optimize_image(file_path)
            
            return optimized_path
            
        except Exception as e:
            print(f"Error downloading image from {image_url}: {e}")
            return None
    
    def get_images_for_slide(self, slide_content: Dict[str, Any], slide_type: str) -> List[Dict[str, Any]]:
        """
        Get appropriate images for a slide based on its content and type.
        
        Args:
            slide_content: Content of the slide
            slide_type: Type of slide (title, content, etc.)
            
        Returns:
            List of image suggestions with metadata
        """
        images = []
        
        try:
            # Extract search terms from slide content
            search_terms = self._extract_search_terms(slide_content, slide_type)
            
            # Search for images for each term
            for term in search_terms[:2]:  # Limit to 2 search terms per slide
                term_images = self.search_images(term, 2)
                images.extend(term_images)
            
            # Remove duplicates and limit results
            seen_urls = set()
            unique_images = []
            for img in images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
                    if len(unique_images) >= 3:  # Max 3 images per slide
                        break
            
            return unique_images
            
        except Exception as e:
            print(f"Error getting images for slide: {e}")
            return []
    
    def _search_curated_images(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search through curated local images and simulate API results."""
        # Map common queries to available images
        query_mappings = {
            'artificial intelligence': [
                {
                    'title': 'AI Technology Concept',
                    'url': 'https://example.com/ai-tech-1.jpg',
                    'local_path': os.path.join(self.images_dir, 'ns3MQsg8IBdn.jpg'),
                    'width': 1200,
                    'height': 800,
                    'description': 'Modern AI technology visualization with neural networks',
                    'source': 'WorkItDaily',
                    'license': 'royalty-free'
                },
                {
                    'title': 'AI Network Visualization',
                    'url': 'https://example.com/ai-network.jpg',
                    'local_path': os.path.join(self.images_dir, 'SJkdn7uNPS7g.jpg'),
                    'width': 1400,
                    'height': 900,
                    'description': 'Artificial intelligence network and connectivity',
                    'source': 'Neil Sahota',
                    'license': 'royalty-free'
                }
            ],
            'technology': [
                {
                    'title': 'Digital Technology',
                    'url': 'https://example.com/tech-1.jpg',
                    'local_path': os.path.join(self.images_dir, 'pCI0ihUdix6p.jpg'),
                    'width': 1440,
                    'height': 1000,
                    'description': 'Modern digital technology concept',
                    'source': 'AI Time Journal',
                    'license': 'royalty-free'
                }
            ],
            'business': [
                {
                    'title': 'Business Presentation',
                    'url': 'https://example.com/business-1.jpg',
                    'local_path': os.path.join(self.images_dir, 'NEr8RIohEBtR.jpg'),
                    'width': 720,
                    'height': 360,
                    'description': 'Professional business presentation template',
                    'source': 'Adobe Stock',
                    'license': 'stock'
                }
            ]
        }
        
        # Find matching images
        results = []
        query_lower = query.lower()
        
        for key, images in query_mappings.items():
            if key in query_lower or any(word in query_lower for word in key.split()):
                for img in images:
                    if os.path.exists(img['local_path']):
                        results.append(img)
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
        
        # If no specific matches, return some default images
        if not results:
            for images in query_mappings.values():
                for img in images:
                    if os.path.exists(img['local_path']):
                        results.append(img)
                        if len(results) >= max_results:
                            break
                if len(results) >= max_results:
                    break
        
        return results[:max_results]
    
    def _extract_search_terms(self, slide_content: Dict[str, Any], slide_type: str) -> List[str]:
        """Extract relevant search terms from slide content."""
        search_terms = []
        
        # Extract from title
        title = slide_content.get('title', '')
        if title:
            search_terms.append(title)
        
        # Extract from bullet points
        bullet_points = slide_content.get('bullet_points', [])
        for point in bullet_points[:2]:  # Limit to first 2 points
            # Extract key phrases (simplified)
            words = point.split()
            if len(words) >= 2:
                search_terms.append(' '.join(words[:3]))  # First 3 words
        
        # Add slide type specific terms
        if slide_type == 'title':
            search_terms.append('professional presentation')
        elif slide_type == 'conclusion':
            search_terms.append('success achievement')
        
        return search_terms[:3]  # Limit to 3 search terms
    
    def _optimize_image(self, file_path: str) -> str:
        """Optimize image for presentation use."""
        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large (max 1920x1080 for presentations)
                max_width, max_height = 1920, 1080
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save optimized version
                optimized_path = file_path.replace('.', '_optimized.')
                img.save(optimized_path, 'JPEG', quality=85, optimize=True)
                
                # Replace original with optimized
                os.replace(optimized_path, file_path)
                
                return file_path
                
        except Exception as e:
            print(f"Error optimizing image {file_path}: {e}")
            return file_path
    
    def _get_cached_image_results(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached image search results."""
        query_hash = hashlib.sha256(f"images_{query}".encode()).hexdigest()
        
        cached = SearchCache.query.filter_by(query_hash=query_hash).first()
        
        if cached and cached.expires_at > datetime.utcnow():
            cached.hit_count += 1
            db.session.commit()
            
            return json.loads(cached.results_json)
        
        return None
    
    def _cache_image_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Cache image search results."""
        query_hash = hashlib.sha256(f"images_{query}".encode()).hexdigest()
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
                source_type='images',
                results_json=json.dumps(results),
                expires_at=expires_at
            )
            db.session.add(cache_entry)
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error caching image results: {e}")
            db.session.rollback()
    
    def get_image_metadata(self, file_path: str) -> Dict[str, Any]:
        """Get metadata for an image file."""
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(file_path)
                }
        except Exception as e:
            print(f"Error getting image metadata: {e}")
            return {}
    
    def cleanup_old_images(self, days_old: int = 7) -> int:
        """Clean up old downloaded images."""
        try:
            count = 0
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            for filename in os.listdir(self.images_dir):
                file_path = os.path.join(self.images_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        count += 1
            
            return count
            
        except Exception as e:
            print(f"Error cleaning up images: {e}")
            return 0

