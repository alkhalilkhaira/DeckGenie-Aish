import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import io
import base64

from src.models.presentation import db

class BrandingService:
    """Service for managing custom branding elements in presentations."""
    
    def __init__(self):
        self.branding_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'branding')
        os.makedirs(self.branding_dir, exist_ok=True)
        
        self.logo_dir = os.path.join(self.branding_dir, 'logos')
        os.makedirs(self.logo_dir, exist_ok=True)
        
        self.max_logo_size = (300, 150)  # Max logo dimensions in pixels
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.svg']
        
    def upload_logo(self, logo_data: bytes, filename: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Upload and process a company logo.
        
        Args:
            logo_data: Binary data of the logo image
            filename: Original filename
            session_id: Session ID for the presentation
            
        Returns:
            Dictionary with logo information, or None if failed
        """
        try:
            # Validate file format
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in self.supported_formats:
                return None
            
            # Generate unique filename
            logo_hash = hashlib.md5(logo_data).hexdigest()[:8]
            safe_filename = f"logo_{session_id}_{logo_hash}{file_ext}"
            logo_path = os.path.join(self.logo_dir, safe_filename)
            
            # Save original logo
            with open(logo_path, 'wb') as f:
                f.write(logo_data)
            
            # Process logo for presentation use
            processed_logo = self._process_logo(logo_path)
            
            if processed_logo:
                return {
                    'original_path': logo_path,
                    'processed_path': processed_logo['path'],
                    'width': processed_logo['width'],
                    'height': processed_logo['height'],
                    'format': processed_logo['format'],
                    'session_id': session_id,
                    'uploaded_at': datetime.utcnow().isoformat()
                }
            
            return None
            
        except Exception as e:
            print(f"Error uploading logo: {e}")
            return None
    
    def create_custom_theme(self, base_theme: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom theme based on a base theme and customizations.
        
        Args:
            base_theme: Base theme name ('corporate', 'startup', 'academic')
            customizations: Dictionary of customization options
            
        Returns:
            Custom theme configuration
        """
        # Base themes
        base_themes = {
            'corporate': {
                'primary_color': '#1f2937',
                'secondary_color': '#3b82f6',
                'accent_color': '#10b981',
                'background_color': '#ffffff',
                'text_color': '#1f2937',
                'font_name': 'Calibri'
            },
            'startup': {
                'primary_color': '#7c3aed',
                'secondary_color': '#f59e0b',
                'accent_color': '#ef4444',
                'background_color': '#ffffff',
                'text_color': '#374151',
                'font_name': 'Calibri'
            },
            'academic': {
                'primary_color': '#374151',
                'secondary_color': '#6366f1',
                'accent_color': '#059669',
                'background_color': '#ffffff',
                'text_color': '#374151',
                'font_name': 'Calibri'
            }
        }
        
        # Start with base theme
        custom_theme = base_themes.get(base_theme, base_themes['corporate']).copy()
        
        # Apply customizations
        color_mappings = {
            'primary_color': 'primary_color',
            'secondary_color': 'secondary_color',
            'accent_color': 'accent_color',
            'background_color': 'background_color',
            'text_color': 'text_color'
        }
        
        for custom_key, theme_key in color_mappings.items():
            if custom_key in customizations:
                custom_theme[theme_key] = customizations[custom_key]
        
        # Add logo information if provided
        if 'logo_path' in customizations:
            custom_theme['logo_path'] = customizations['logo_path']
            custom_theme['logo_position'] = customizations.get('logo_position', 'top_right')
            custom_theme['logo_size'] = customizations.get('logo_size', 'small')
        
        # Add font customization
        if 'font_name' in customizations:
            custom_theme['font_name'] = customizations['font_name']
        
        return custom_theme
    
    def generate_color_palette(self, primary_color: str) -> Dict[str, str]:
        """
        Generate a complementary color palette based on a primary color.
        
        Args:
            primary_color: Primary color in hex format
            
        Returns:
            Dictionary of complementary colors
        """
        try:
            # Convert hex to RGB
            primary_rgb = self._hex_to_rgb(primary_color)
            
            # Generate complementary colors using color theory
            palette = {
                'primary_color': primary_color,
                'secondary_color': self._generate_secondary_color(primary_rgb),
                'accent_color': self._generate_accent_color(primary_rgb),
                'background_color': '#ffffff',
                'text_color': self._generate_text_color(primary_rgb)
            }
            
            return palette
            
        except Exception as e:
            print(f"Error generating color palette: {e}")
            return {
                'primary_color': primary_color,
                'secondary_color': '#3b82f6',
                'accent_color': '#10b981',
                'background_color': '#ffffff',
                'text_color': '#1f2937'
            }
    
    def _process_logo(self, logo_path: str) -> Optional[Dict[str, Any]]:
        """Process logo for presentation use."""
        try:
            with Image.open(logo_path) as img:
                # Convert to RGBA if necessary
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Resize if too large
                if img.width > self.max_logo_size[0] or img.height > self.max_logo_size[1]:
                    img.thumbnail(self.max_logo_size, Image.Resampling.LANCZOS)
                
                # Save processed version
                processed_filename = f"processed_{os.path.basename(logo_path)}"
                processed_path = os.path.join(self.logo_dir, processed_filename)
                
                # Save as PNG to preserve transparency
                img.save(processed_path, 'PNG', optimize=True)
                
                return {
                    'path': processed_path,
                    'width': img.width,
                    'height': img.height,
                    'format': 'PNG'
                }
                
        except Exception as e:
            print(f"Error processing logo: {e}")
            return None
    
    def _hex_to_rgb(self, hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _rgb_to_hex(self, rgb: tuple) -> str:
        """Convert RGB tuple to hex color."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
    
    def _generate_secondary_color(self, primary_rgb: tuple) -> str:
        """Generate a secondary color based on primary color."""
        # Create a lighter/darker version of the primary color
        r, g, b = primary_rgb
        
        # If the color is dark, make it lighter; if light, make it darker
        brightness = (r + g + b) / 3
        
        if brightness < 128:
            # Lighten the color
            factor = 1.5
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
        else:
            # Darken the color
            factor = 0.7
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
        
        return self._rgb_to_hex((r, g, b))
    
    def _generate_accent_color(self, primary_rgb: tuple) -> str:
        """Generate an accent color based on primary color."""
        # Create a complementary color
        r, g, b = primary_rgb
        
        # Simple complementary color calculation
        comp_r = 255 - r
        comp_g = 255 - g
        comp_b = 255 - b
        
        # Adjust saturation to make it more appealing
        avg = (comp_r + comp_g + comp_b) / 3
        factor = 0.8
        
        comp_r = int(avg + (comp_r - avg) * factor)
        comp_g = int(avg + (comp_g - avg) * factor)
        comp_b = int(avg + (comp_b - avg) * factor)
        
        return self._rgb_to_hex((comp_r, comp_g, comp_b))
    
    def _generate_text_color(self, primary_rgb: tuple) -> str:
        """Generate appropriate text color based on primary color."""
        # Calculate brightness of primary color
        r, g, b = primary_rgb
        brightness = (r * 0.299 + g * 0.587 + b * 0.114)
        
        # Return dark text for light backgrounds, light text for dark backgrounds
        if brightness > 128:
            return '#1f2937'  # Dark text
        else:
            return '#ffffff'  # Light text
    
    def create_branded_template(self, theme: Dict[str, Any], template_type: str = 'standard') -> Dict[str, Any]:
        """
        Create a branded presentation template.
        
        Args:
            theme: Theme configuration with colors and branding
            template_type: Type of template ('standard', 'minimal', 'modern')
            
        Returns:
            Template configuration
        """
        templates = {
            'standard': {
                'title_slide': {
                    'logo_position': 'top_right',
                    'title_alignment': 'center',
                    'background_style': 'solid'
                },
                'content_slide': {
                    'logo_position': 'top_right',
                    'header_style': 'underline',
                    'bullet_style': 'circle'
                }
            },
            'minimal': {
                'title_slide': {
                    'logo_position': 'bottom_right',
                    'title_alignment': 'left',
                    'background_style': 'gradient'
                },
                'content_slide': {
                    'logo_position': 'bottom_right',
                    'header_style': 'clean',
                    'bullet_style': 'dash'
                }
            },
            'modern': {
                'title_slide': {
                    'logo_position': 'top_left',
                    'title_alignment': 'center',
                    'background_style': 'geometric'
                },
                'content_slide': {
                    'logo_position': 'top_left',
                    'header_style': 'bold',
                    'bullet_style': 'arrow'
                }
            }
        }
        
        template = templates.get(template_type, templates['standard'])
        template['theme'] = theme
        
        return template
    
    def validate_color(self, color: str) -> bool:
        """Validate if a color string is a valid hex color."""
        try:
            if not color.startswith('#'):
                return False
            
            if len(color) != 7:
                return False
            
            int(color[1:], 16)
            return True
            
        except ValueError:
            return False
    
    def get_brand_guidelines(self, theme: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate brand guidelines based on theme.
        
        Args:
            theme: Theme configuration
            
        Returns:
            Brand guidelines with usage recommendations
        """
        guidelines = {
            'colors': {
                'primary': {
                    'color': theme.get('primary_color', '#1f2937'),
                    'usage': 'Main headings, important elements, brand identity'
                },
                'secondary': {
                    'color': theme.get('secondary_color', '#3b82f6'),
                    'usage': 'Subheadings, links, secondary elements'
                },
                'accent': {
                    'color': theme.get('accent_color', '#10b981'),
                    'usage': 'Highlights, call-to-action, emphasis'
                },
                'text': {
                    'color': theme.get('text_color', '#1f2937'),
                    'usage': 'Body text, general content'
                }
            },
            'typography': {
                'font_family': theme.get('font_name', 'Calibri'),
                'title_size': '36pt',
                'subtitle_size': '24pt',
                'body_size': '20pt'
            },
            'logo': {
                'position': theme.get('logo_position', 'top_right'),
                'size': theme.get('logo_size', 'small'),
                'usage': 'Consistent placement on all slides'
            }
        }
        
        return guidelines
    
    def cleanup_old_branding(self, days_old: int = 30) -> int:
        """Clean up old branding files."""
        try:
            count = 0
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            for filename in os.listdir(self.logo_dir):
                file_path = os.path.join(self.logo_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        count += 1
            
            return count
            
        except Exception as e:
            print(f"Error cleaning up branding files: {e}")
            return 0

