from flask import Blueprint, request, jsonify, send_file, session
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from src.models.presentation import db, Presentation
from src.services.tts_service import TTSService
from src.services.branding_service import BrandingService
from src.services.translation_service import TranslationService

advanced_bp = Blueprint('advanced', __name__)

# Initialize services
tts_service = TTSService()
branding_service = BrandingService()
translation_service = TranslationService()

@advanced_bp.route('/tts/generate/<session_id>', methods=['POST'])
def generate_audio_narration(session_id):
    """Generate audio narration for a presentation."""
    try:
        # Get presentation
        presentation = Presentation.query.filter_by(session_id=session_id).first()
        if not presentation:
            return jsonify({'error': {'code': 'PRESENTATION_NOT_FOUND', 'message': 'Presentation not found'}}), 404
        
        # Get voice type from request
        data = request.get_json() or {}
        voice_type = data.get('voice_type', 'female_voice')
        
        if voice_type not in tts_service.supported_voices:
            return jsonify({'error': {'code': 'INVALID_VOICE', 'message': 'Invalid voice type'}}), 400
        
        # Generate audio
        audio_path = tts_service.generate_presentation_audio(presentation.id, voice_type)
        
        if not audio_path:
            return jsonify({'error': {'code': 'AUDIO_GENERATION_FAILED', 'message': 'Failed to generate audio'}}), 500
        
        # Get audio metadata
        metadata = tts_service.get_audio_metadata(audio_path)
        
        return jsonify({
            'success': True,
            'audio_path': audio_path,
            'metadata': metadata,
            'voice_type': voice_type
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/tts/download/<session_id>')
def download_audio(session_id):
    """Download audio narration file."""
    try:
        # Get presentation
        presentation = Presentation.query.filter_by(session_id=session_id).first()
        if not presentation:
            return jsonify({'error': {'code': 'PRESENTATION_NOT_FOUND', 'message': 'Presentation not found'}}), 404
        
        # Find audio file
        audio_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'audio')
        audio_filename = f"presentation_{session_id}.wav"
        audio_path = os.path.join(audio_dir, audio_filename)
        
        if not os.path.exists(audio_path):
            return jsonify({'error': {'code': 'AUDIO_NOT_FOUND', 'message': 'Audio file not found'}}), 404
        
        return send_file(
            audio_path,
            as_attachment=True,
            download_name=f"presentation_audio_{session_id}.wav",
            mimetype='audio/wav'
        )
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/branding/upload-logo', methods=['POST'])
def upload_logo():
    """Upload a company logo for branding."""
    try:
        if 'logo' not in request.files:
            return jsonify({'error': {'code': 'NO_FILE', 'message': 'No logo file provided'}}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'error': {'code': 'NO_FILE', 'message': 'No file selected'}}), 400
        
        # Get session ID
        session_id = request.form.get('session_id')
        if not session_id:
            return jsonify({'error': {'code': 'NO_SESSION', 'message': 'Session ID required'}}), 400
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Upload logo
        logo_info = branding_service.upload_logo(file.read(), filename, session_id)
        
        if not logo_info:
            return jsonify({'error': {'code': 'UPLOAD_FAILED', 'message': 'Failed to upload logo'}}), 500
        
        return jsonify({
            'success': True,
            'logo_info': logo_info
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/branding/create-theme', methods=['POST'])
def create_custom_theme():
    """Create a custom theme with branding."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': {'code': 'NO_DATA', 'message': 'No theme data provided'}}), 400
        
        base_theme = data.get('base_theme', 'corporate')
        customizations = data.get('customizations', {})
        
        # Create custom theme
        custom_theme = branding_service.create_custom_theme(base_theme, customizations)
        
        # Generate brand guidelines
        guidelines = branding_service.get_brand_guidelines(custom_theme)
        
        return jsonify({
            'success': True,
            'theme': custom_theme,
            'guidelines': guidelines
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/branding/generate-palette', methods=['POST'])
def generate_color_palette():
    """Generate a color palette from a primary color."""
    try:
        data = request.get_json()
        if not data or 'primary_color' not in data:
            return jsonify({'error': {'code': 'NO_COLOR', 'message': 'Primary color required'}}), 400
        
        primary_color = data['primary_color']
        
        # Validate color format
        if not branding_service.validate_color(primary_color):
            return jsonify({'error': {'code': 'INVALID_COLOR', 'message': 'Invalid color format'}}), 400
        
        # Generate palette
        palette = branding_service.generate_color_palette(primary_color)
        
        return jsonify({
            'success': True,
            'palette': palette
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/translation/translate/<session_id>', methods=['POST'])
def translate_presentation(session_id):
    """Translate a presentation to a different language."""
    try:
        # Get presentation
        presentation = Presentation.query.filter_by(session_id=session_id).first()
        if not presentation:
            return jsonify({'error': {'code': 'PRESENTATION_NOT_FOUND', 'message': 'Presentation not found'}}), 404
        
        data = request.get_json()
        if not data or 'target_language' not in data:
            return jsonify({'error': {'code': 'NO_LANGUAGE', 'message': 'Target language required'}}), 400
        
        target_language = data['target_language']
        
        # Validate language
        if target_language not in translation_service.get_supported_languages():
            return jsonify({'error': {'code': 'UNSUPPORTED_LANGUAGE', 'message': 'Language not supported'}}), 400
        
        # Perform translation
        success = translation_service.translate_presentation(presentation.id, target_language)
        
        if not success:
            return jsonify({'error': {'code': 'TRANSLATION_FAILED', 'message': 'Translation failed'}}), 500
        
        # Get language info
        language_info = translation_service.get_language_info(target_language)
        
        return jsonify({
            'success': True,
            'target_language': target_language,
            'language_info': language_info,
            'message': f'Presentation translated to {language_info["name"]}'
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/translation/languages', methods=['GET'])
def get_supported_languages():
    """Get list of supported languages for translation."""
    try:
        languages = translation_service.get_supported_languages()
        
        return jsonify({
            'success': True,
            'languages': languages
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/translation/detect', methods=['POST'])
def detect_language():
    """Detect the language of provided text."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': {'code': 'NO_TEXT', 'message': 'Text required'}}), 400
        
        text = data['text']
        detected_language = translation_service.detect_language(text)
        language_info = translation_service.get_language_info(detected_language)
        
        return jsonify({
            'success': True,
            'detected_language': detected_language,
            'language_info': language_info
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/features/status', methods=['GET'])
def get_features_status():
    """Get status of advanced features."""
    try:
        # Check if services are available
        features = {
            'text_to_speech': {
                'available': True,
                'supported_voices': tts_service.supported_voices,
                'description': 'Generate voice narration for presentations'
            },
            'custom_branding': {
                'available': True,
                'supported_formats': branding_service.supported_formats,
                'description': 'Upload logos and customize presentation themes'
            },
            'translation': {
                'available': True,
                'supported_languages': translation_service.get_supported_languages(),
                'description': 'Translate presentations to multiple languages'
            }
        }
        
        return jsonify({
            'success': True,
            'features': features
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

@advanced_bp.route('/cleanup', methods=['POST'])
def cleanup_advanced_files():
    """Clean up old advanced feature files."""
    try:
        data = request.get_json() or {}
        days_old = data.get('days_old', 7)
        
        # Clean up files
        audio_cleaned = tts_service.cleanup_old_audio(days_old)
        branding_cleaned = branding_service.cleanup_old_branding(days_old)
        translations_cleaned = translation_service.cleanup_old_translations(days_old)
        
        return jsonify({
            'success': True,
            'cleaned_files': {
                'audio_files': audio_cleaned,
                'branding_files': branding_cleaned,
                'cached_translations': translations_cleaned
            }
        })
        
    except Exception as e:
        return jsonify({'error': {'code': 'INTERNAL_ERROR', 'message': str(e)}}), 500

