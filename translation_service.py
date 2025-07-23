import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests

from src.models.presentation import db, SearchCache

class TranslationService:
    """Service for translating presentation content to different languages."""
    
    def __init__(self):
        self.cache_duration_hours = 168  # 1 week for translations
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese (Simplified)',
            'ar': 'Arabic',
            'hi': 'Hindi'
        }
        
        # Language-specific formatting rules
        self.language_rules = {
            'ar': {'rtl': True, 'font_adjustment': 1.2},
            'zh': {'font_adjustment': 1.1},
            'ja': {'font_adjustment': 1.1},
            'ko': {'font_adjustment': 1.1},
            'hi': {'font_adjustment': 1.1},
            'ru': {'font_adjustment': 1.05}
        }
    
    def translate_presentation(self, presentation_id: int, target_language: str) -> bool:
        """
        Translate an entire presentation to a target language.
        
        Args:
            presentation_id: Database ID of the presentation
            target_language: Target language code (e.g., 'es', 'fr')
            
        Returns:
            True if translation successful, False otherwise
        """
        try:
            from src.models.presentation import Presentation, Slide
            
            # Get presentation
            presentation = Presentation.query.get(presentation_id)
            if not presentation:
                return False
            
            # Validate target language
            if target_language not in self.supported_languages:
                return False
            
            # Translate presentation title
            translated_title = self.translate_text(presentation.title, target_language)
            if translated_title:
                presentation.title = translated_title
            
            # Get all slides
            slides = Slide.query.filter_by(presentation_id=presentation_id).all()
            
            # Translate each slide
            for slide in slides:
                self._translate_slide(slide, target_language)
            
            # Update presentation language
            presentation.language = target_language
            db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error translating presentation: {e}")
            db.session.rollback()
            return False
    
    def translate_text(self, text: str, target_language: str, source_language: str = 'en') -> Optional[str]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (default: 'en')
            
        Returns:
            Translated text, or None if translation failed
        """
        if not text or not text.strip():
            return text
        
        # Check cache first
        cached_translation = self._get_cached_translation(text, source_language, target_language)
        if cached_translation:
            return cached_translation
        
        # Perform translation
        translated_text = self._perform_translation(text, source_language, target_language)
        
        # Cache the result
        if translated_text:
            self._cache_translation(text, source_language, target_language, translated_text)
        
        return translated_text
    
    def get_language_info(self, language_code: str) -> Dict[str, Any]:
        """
        Get information about a language including formatting rules.
        
        Args:
            language_code: Language code
            
        Returns:
            Dictionary with language information
        """
        info = {
            'code': language_code,
            'name': self.supported_languages.get(language_code, 'Unknown'),
            'rtl': False,
            'font_adjustment': 1.0
        }
        
        # Apply language-specific rules
        if language_code in self.language_rules:
            info.update(self.language_rules[language_code])
        
        return info
    
    def _translate_slide(self, slide, target_language: str) -> None:
        """Translate a single slide."""
        try:
            # Parse slide content
            content_data = json.loads(slide.content_json) if slide.content_json else {}
            
            # Translate title
            if slide.title:
                translated_title = self.translate_text(slide.title, target_language)
                if translated_title:
                    slide.title = translated_title
                    content_data['title'] = translated_title
            
            # Translate bullet points
            if 'bullet_points' in content_data:
                translated_points = []
                for point in content_data['bullet_points']:
                    translated_point = self.translate_text(point, target_language)
                    translated_points.append(translated_point or point)
                content_data['bullet_points'] = translated_points
            
            # Translate speaker notes
            if slide.speaker_notes:
                translated_notes = self.translate_text(slide.speaker_notes, target_language)
                if translated_notes:
                    slide.speaker_notes = translated_notes
            
            # Update slide content
            slide.content_json = json.dumps(content_data)
            
        except Exception as e:
            print(f"Error translating slide {slide.id}: {e}")
    
    def _perform_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """
        Perform the actual translation.
        
        For now, this provides simulated translations for common phrases.
        In production, this would integrate with translation APIs like Google Translate,
        Azure Translator, or OpenAI's translation capabilities.
        """
        # Simulated translations for common presentation terms
        translations = {
            'en_es': {
                'Introduction': 'Introducción',
                'Conclusion': 'Conclusión',
                'Overview': 'Resumen',
                'Agenda': 'Agenda',
                'Thank you': 'Gracias',
                'Questions': 'Preguntas',
                'Artificial Intelligence': 'Inteligencia Artificial',
                'Technology': 'Tecnología',
                'Business': 'Negocio',
                'Marketing': 'Marketing',
                'Strategy': 'Estrategia',
                'Innovation': 'Innovación',
                'Digital Transformation': 'Transformación Digital',
                'Data Analysis': 'Análisis de Datos',
                'Machine Learning': 'Aprendizaje Automático',
                'Future Trends': 'Tendencias Futuras'
            },
            'en_fr': {
                'Introduction': 'Introduction',
                'Conclusion': 'Conclusion',
                'Overview': 'Aperçu',
                'Agenda': 'Ordre du jour',
                'Thank you': 'Merci',
                'Questions': 'Questions',
                'Artificial Intelligence': 'Intelligence Artificielle',
                'Technology': 'Technologie',
                'Business': 'Entreprise',
                'Marketing': 'Marketing',
                'Strategy': 'Stratégie',
                'Innovation': 'Innovation',
                'Digital Transformation': 'Transformation Numérique',
                'Data Analysis': 'Analyse de Données',
                'Machine Learning': 'Apprentissage Automatique',
                'Future Trends': 'Tendances Futures'
            },
            'en_de': {
                'Introduction': 'Einführung',
                'Conclusion': 'Fazit',
                'Overview': 'Überblick',
                'Agenda': 'Tagesordnung',
                'Thank you': 'Danke',
                'Questions': 'Fragen',
                'Artificial Intelligence': 'Künstliche Intelligenz',
                'Technology': 'Technologie',
                'Business': 'Geschäft',
                'Marketing': 'Marketing',
                'Strategy': 'Strategie',
                'Innovation': 'Innovation',
                'Digital Transformation': 'Digitale Transformation',
                'Data Analysis': 'Datenanalyse',
                'Machine Learning': 'Maschinelles Lernen',
                'Future Trends': 'Zukunftstrends'
            }
        }
        
        # Get translation dictionary for this language pair
        translation_key = f"{source_lang}_{target_lang}"
        translation_dict = translations.get(translation_key, {})
        
        # Check for exact matches first
        if text in translation_dict:
            return translation_dict[text]
        
        # Check for partial matches (case-insensitive)
        text_lower = text.lower()
        for original, translated in translation_dict.items():
            if original.lower() == text_lower:
                return translated
        
        # For longer text, try to translate known phrases within it
        translated_text = text
        for original, translated in translation_dict.items():
            if original in text:
                translated_text = translated_text.replace(original, translated)
        
        # If we made any changes, return the result
        if translated_text != text:
            return translated_text
        
        # For demonstration purposes, add a language prefix for untranslated text
        language_prefixes = {
            'es': '[ES] ',
            'fr': '[FR] ',
            'de': '[DE] ',
            'it': '[IT] ',
            'pt': '[PT] ',
            'ru': '[RU] ',
            'ja': '[JA] ',
            'ko': '[KO] ',
            'zh': '[ZH] ',
            'ar': '[AR] ',
            'hi': '[HI] '
        }
        
        prefix = language_prefixes.get(target_lang, f'[{target_lang.upper()}] ')
        return f"{prefix}{text}"
    
    def _get_cached_translation(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """Get cached translation."""
        cache_key = f"translate_{source_lang}_{target_lang}_{hashlib.sha256(text.encode()).hexdigest()}"
        
        cached = SearchCache.query.filter_by(query_hash=cache_key).first()
        
        if cached and cached.expires_at > datetime.utcnow():
            cached.hit_count += 1
            db.session.commit()
            
            result = json.loads(cached.results_json)
            return result.get('translation')
        
        return None
    
    def _cache_translation(self, text: str, source_lang: str, target_lang: str, translation: str) -> None:
        """Cache translation result."""
        cache_key = f"translate_{source_lang}_{target_lang}_{hashlib.sha256(text.encode()).hexdigest()}"
        expires_at = datetime.utcnow() + timedelta(hours=self.cache_duration_hours)
        
        result_data = {
            'original_text': text,
            'translation': translation,
            'source_language': source_lang,
            'target_language': target_lang
        }
        
        existing = SearchCache.query.filter_by(query_hash=cache_key).first()
        
        if existing:
            existing.results_json = json.dumps(result_data)
            existing.expires_at = expires_at
            existing.hit_count += 1
        else:
            cache_entry = SearchCache(
                query_hash=cache_key,
                query_text=f"translate:{text[:100]}",
                source_type='translation',
                results_json=json.dumps(result_data),
                expires_at=expires_at
            )
            db.session.add(cache_entry)
        
        try:
            db.session.commit()
        except Exception as e:
            print(f"Error caching translation: {e}")
            db.session.rollback()
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of text.
        
        For now, this is a simple heuristic-based detection.
        In production, this would use proper language detection libraries.
        """
        # Simple language detection based on common words
        language_indicators = {
            'es': ['el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con', 'para', 'una', 'del', 'los', 'las'],
            'fr': ['le', 'de', 'et', 'à', 'un', 'il', 'être', 'et', 'en', 'avoir', 'que', 'pour', 'dans', 'ce', 'son', 'une', 'sur', 'avec', 'ne', 'se', 'pas', 'tout', 'plus', 'par'],
            'de': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'für', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'als', 'auch', 'es', 'an', 'werden'],
            'it': ['il', 'di', 'che', 'e', 'la', 'per', 'un', 'in', 'con', 'del', 'da', 'a', 'al', 'le', 'si', 'dei', 'come', 'io', 'questo', 'qui', 'tutto', 'ancora', 'suo', 'della']
        }
        
        text_lower = text.lower()
        words = text_lower.split()
        
        language_scores = {}
        
        for lang, indicators in language_indicators.items():
            score = 0
            for word in words:
                if word in indicators:
                    score += 1
            language_scores[lang] = score / len(words) if words else 0
        
        # Return language with highest score, or 'en' as default
        if language_scores:
            detected_lang = max(language_scores, key=language_scores.get)
            if language_scores[detected_lang] > 0.1:  # Threshold for detection confidence
                return detected_lang
        
        return 'en'  # Default to English
    
    def get_translation_quality_score(self, original: str, translated: str, target_language: str) -> float:
        """
        Estimate translation quality score.
        
        This is a simplified quality assessment.
        In production, this would use more sophisticated metrics.
        """
        try:
            # Basic quality indicators
            score = 1.0
            
            # Check if translation is too similar to original (might indicate no translation)
            if original.lower() == translated.lower():
                score *= 0.3
            
            # Check length ratio (translations should be reasonably similar in length)
            length_ratio = len(translated) / len(original) if original else 1
            if length_ratio < 0.5 or length_ratio > 2.0:
                score *= 0.7
            
            # Check for language-specific characters
            language_chars = {
                'es': 'ñáéíóúü',
                'fr': 'àâäéèêëïîôöùûüÿç',
                'de': 'äöüß',
                'it': 'àèéìíîòóù',
                'pt': 'ãáàâéêíóôõúç',
                'ru': 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
            }
            
            if target_language in language_chars:
                target_chars = language_chars[target_language]
                has_target_chars = any(char in translated.lower() for char in target_chars)
                if has_target_chars:
                    score *= 1.2
                else:
                    score *= 0.8
            
            return min(1.0, score)
            
        except Exception as e:
            print(f"Error calculating translation quality: {e}")
            return 0.5
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages."""
        return self.supported_languages.copy()
    
    def cleanup_old_translations(self, days_old: int = 30) -> int:
        """Clean up old cached translations."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            
            deleted = SearchCache.query.filter(
                SearchCache.source_type == 'translation',
                SearchCache.expires_at < cutoff_time
            ).delete()
            
            db.session.commit()
            return deleted
            
        except Exception as e:
            print(f"Error cleaning up translations: {e}")
            db.session.rollback()
            return 0

