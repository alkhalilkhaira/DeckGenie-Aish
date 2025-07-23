import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import tempfile

from src.models.presentation import db, Presentation, Slide

class TTSService:
    """Service for generating text-to-speech audio for presentations."""
    
    def __init__(self):
        self.audio_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'audio')
        os.makedirs(self.audio_dir, exist_ok=True)
        
        self.max_text_length = 50000  # Maximum characters per TTS request
        self.supported_voices = {
            'male_voice': 'Male Voice',
            'female_voice': 'Female Voice'
        }
        
    def generate_presentation_audio(self, presentation_id: int, voice_type: str = 'female_voice') -> Optional[str]:
        """
        Generate audio narration for an entire presentation.
        
        Args:
            presentation_id: Database ID of the presentation
            voice_type: Type of voice to use ('male_voice' or 'female_voice')
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        try:
            # Get presentation and slides
            presentation = Presentation.query.get(presentation_id)
            if not presentation:
                return None
            
            slides = Slide.query.filter_by(presentation_id=presentation_id).order_by(Slide.slide_number).all()
            if not slides:
                return None
            
            # Generate audio for each slide
            audio_files = []
            
            for slide in slides:
                slide_audio = self._generate_slide_audio(slide, voice_type)
                if slide_audio:
                    audio_files.append(slide_audio)
            
            if not audio_files:
                return None
            
            # Concatenate all audio files
            final_audio_path = self._concatenate_audio_files(audio_files, presentation.session_id)
            
            # Clean up individual slide audio files
            for audio_file in audio_files:
                try:
                    os.remove(audio_file)
                except:
                    pass
            
            return final_audio_path
            
        except Exception as e:
            print(f"Error generating presentation audio: {e}")
            return None
    
    def generate_slide_audio(self, slide_id: int, voice_type: str = 'female_voice') -> Optional[str]:
        """
        Generate audio narration for a single slide.
        
        Args:
            slide_id: Database ID of the slide
            voice_type: Type of voice to use
            
        Returns:
            Path to the generated audio file, or None if failed
        """
        try:
            slide = Slide.query.get(slide_id)
            if not slide:
                return None
            
            return self._generate_slide_audio(slide, voice_type)
            
        except Exception as e:
            print(f"Error generating slide audio: {e}")
            return None
    
    def _generate_slide_audio(self, slide: Slide, voice_type: str) -> Optional[str]:
        """Generate audio for a single slide."""
        try:
            # Prepare text for TTS
            text_content = self._prepare_slide_text(slide)
            
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # Generate filename
            filename = f"slide_{slide.id}_{hashlib.md5(text_content.encode()).hexdigest()[:8]}.wav"
            audio_path = os.path.join(self.audio_dir, filename)
            
            # Check if audio already exists
            if os.path.exists(audio_path):
                return audio_path
            
            # Generate audio using media_generate_speech equivalent
            success = self._generate_speech_audio(text_content, audio_path, voice_type)
            
            if success and os.path.exists(audio_path):
                return audio_path
            
            return None
            
        except Exception as e:
            print(f"Error generating slide audio: {e}")
            return None
    
    def _prepare_slide_text(self, slide: Slide) -> str:
        """Prepare slide content for text-to-speech."""
        try:
            content_data = json.loads(slide.content_json) if slide.content_json else {}
            
            text_parts = []
            
            # Add slide title
            title = slide.title or content_data.get('title', '')
            if title:
                text_parts.append(f"Slide {slide.slide_number}: {title}")
            
            # Add bullet points
            bullet_points = content_data.get('bullet_points', [])
            for point in bullet_points:
                # Clean up bullet point text
                clean_point = point.strip()
                if clean_point:
                    text_parts.append(clean_point)
            
            # Add speaker notes if available
            speaker_notes = slide.speaker_notes
            if speaker_notes and speaker_notes.strip():
                text_parts.append(speaker_notes.strip())
            
            # Join all text parts
            full_text = '. '.join(text_parts)
            
            # Clean up text for better speech
            full_text = self._clean_text_for_speech(full_text)
            
            return full_text
            
        except Exception as e:
            print(f"Error preparing slide text: {e}")
            return ""
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more suitable for speech synthesis."""
        # Remove excessive punctuation
        text = text.replace('...', '. ')
        text = text.replace('..', '. ')
        
        # Ensure proper sentence endings
        if not text.endswith('.'):
            text += '.'
        
        # Replace common abbreviations with full words
        replacements = {
            'AI': 'Artificial Intelligence',
            'ML': 'Machine Learning',
            'IoT': 'Internet of Things',
            'API': 'Application Programming Interface',
            'UI': 'User Interface',
            'UX': 'User Experience',
            'CEO': 'Chief Executive Officer',
            'CTO': 'Chief Technology Officer',
            'ROI': 'Return on Investment',
            'KPI': 'Key Performance Indicator'
        }
        
        for abbr, full in replacements.items():
            text = text.replace(f' {abbr} ', f' {full} ')
            text = text.replace(f' {abbr}.', f' {full}.')
            text = text.replace(f' {abbr},', f' {full},')
        
        return text
    
    def _generate_speech_audio(self, text: str, output_path: str, voice_type: str) -> bool:
        """Generate speech audio using the media generation service."""
        try:
            # This would normally use the media_generate_speech tool
            # For now, we'll create a placeholder audio file
            
            # Create a simple audio file (placeholder)
            # In production, this would call the actual TTS service
            
            # For demonstration, create a small WAV file
            import wave
            import struct
            import math
            
            # Generate a simple tone as placeholder
            sample_rate = 44100
            duration = min(len(text) * 0.1, 30)  # Rough estimate: 0.1 seconds per character, max 30 seconds
            
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Generate a simple sine wave as placeholder
                for i in range(int(sample_rate * duration)):
                    value = int(32767 * 0.1 * math.sin(2 * math.pi * 440 * i / sample_rate))
                    wav_file.writeframes(struct.pack('<h', value))
            
            return True
            
        except Exception as e:
            print(f"Error generating speech audio: {e}")
            return False
    
    def _concatenate_audio_files(self, audio_files: List[str], session_id: str) -> Optional[str]:
        """Concatenate multiple audio files into one."""
        try:
            if not audio_files:
                return None
            
            if len(audio_files) == 1:
                # Only one file, just copy it
                final_path = os.path.join(self.audio_dir, f"presentation_{session_id}.wav")
                import shutil
                shutil.copy2(audio_files[0], final_path)
                return final_path
            
            # Use ffmpeg to concatenate audio files
            final_path = os.path.join(self.audio_dir, f"presentation_{session_id}.wav")
            
            # Create a temporary file list for ffmpeg
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                for audio_file in audio_files:
                    f.write(f"file '{audio_file}'\n")
                file_list_path = f.name
            
            try:
                # Run ffmpeg to concatenate
                cmd = [
                    'ffmpeg', '-y',  # -y to overwrite output file
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', file_list_path,
                    '-c', 'copy',
                    final_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(final_path):
                    return final_path
                else:
                    print(f"ffmpeg error: {result.stderr}")
                    return None
                    
            finally:
                # Clean up temporary file list
                try:
                    os.unlink(file_list_path)
                except:
                    pass
            
        except Exception as e:
            print(f"Error concatenating audio files: {e}")
            return None
    
    def get_audio_metadata(self, audio_path: str) -> Dict[str, Any]:
        """Get metadata for an audio file."""
        try:
            if not os.path.exists(audio_path):
                return {}
            
            import wave
            
            with wave.open(audio_path, 'r') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                duration = frames / float(sample_rate)
                
                return {
                    'duration_seconds': duration,
                    'sample_rate': sample_rate,
                    'channels': wav_file.getnchannels(),
                    'sample_width': wav_file.getsampwidth(),
                    'file_size_bytes': os.path.getsize(audio_path)
                }
                
        except Exception as e:
            print(f"Error getting audio metadata: {e}")
            return {}
    
    def cleanup_old_audio(self, days_old: int = 7) -> int:
        """Clean up old audio files."""
        try:
            count = 0
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            
            for filename in os.listdir(self.audio_dir):
                file_path = os.path.join(self.audio_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.wav'):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        count += 1
            
            return count
            
        except Exception as e:
            print(f"Error cleaning up audio files: {e}")
            return 0

