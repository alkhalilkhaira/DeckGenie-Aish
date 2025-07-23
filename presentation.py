from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    total_generations = db.Column(db.Integer, default=0)
    
    # Relationships
    presentations = db.relationship('Presentation', backref='user', lazy=True, cascade='all, delete-orphan')
    branding_assets = db.relationship('BrandingAsset', backref='user', lazy=True, cascade='all, delete-orphan')
    rate_limits = db.relationship('RateLimit', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_generations': self.total_generations
        }

class Presentation(db.Model):
    __tablename__ = 'presentations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    original_prompt = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('queued', 'researching', 'planning', 'generating', 'assembling', 'completed', 'failed', name='presentation_status'), default='queued')
    progress = db.Column(db.Integer, default=0)
    current_step = db.Column(db.String(100))
    slide_count = db.Column(db.Integer, nullable=False)
    theme = db.Column(db.String(50), nullable=False)
    language = db.Column(db.String(5), default='en')
    include_tts = db.Column(db.Boolean, default=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.Integer)
    generation_time = db.Column(db.Integer)  # in seconds
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    slides = db.relationship('Slide', backref='presentation', lazy=True, cascade='all, delete-orphan')
    citations = db.relationship('Citation', backref='presentation', lazy=True, cascade='all, delete-orphan')
    generation_logs = db.relationship('GenerationLog', backref='presentation', lazy=True, cascade='all, delete-orphan')
    tts_audio = db.relationship('TTSAudio', backref='presentation', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'original_prompt': self.original_prompt,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'slide_count': self.slide_count,
            'theme': self.theme,
            'language': self.language,
            'include_tts': self.include_tts,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'generation_time': self.generation_time,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class Slide(db.Model):
    __tablename__ = 'slides'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    slide_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slide_type = db.Column(db.Enum('title', 'agenda', 'content', 'chart', 'image', 'conclusion', 'references', name='slide_type'), nullable=False)
    content_json = db.Column(db.Text)  # JSON blob containing slide content
    speaker_notes = db.Column(db.Text)
    image_urls = db.Column(db.Text)  # JSON array of image URLs
    chart_data = db.Column(db.Text)  # JSON blob for chart configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('presentation_id', 'slide_number', name='unique_presentation_slide'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'slide_number': self.slide_number,
            'title': self.title,
            'slide_type': self.slide_type,
            'content_json': self.content_json,
            'speaker_notes': self.speaker_notes,
            'image_urls': self.image_urls,
            'chart_data': self.chart_data,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Citation(db.Model):
    __tablename__ = 'citations'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    citation_number = db.Column(db.Integer, nullable=False)
    source_type = db.Column(db.Enum('web', 'academic', 'government', 'news', 'image', name='source_type'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(255))
    publication_date = db.Column(db.Date)
    accessed_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('presentation_id', 'citation_number', name='unique_presentation_citation'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'citation_number': self.citation_number,
            'source_type': self.source_type,
            'title': self.title,
            'url': self.url,
            'author': self.author,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'accessed_date': self.accessed_date.isoformat() if self.accessed_date else None,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class BrandingAsset(db.Model):
    __tablename__ = 'branding_assets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    logo_path = db.Column(db.String(500))
    logo_filename = db.Column(db.String(255))
    primary_color = db.Column(db.String(7))  # hex color code
    secondary_color = db.Column(db.String(7))
    accent_color = db.Column(db.String(7))
    font_family = db.Column(db.String(100))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'logo_path': self.logo_path,
            'logo_filename': self.logo_filename,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'font_family': self.font_family,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_active': self.is_active
        }

class GenerationLog(db.Model):
    __tablename__ = 'generation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    step_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('started', 'completed', 'failed', name='log_status'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in milliseconds
    details = db.Column(db.Text)  # JSON blob with step-specific information
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'step_name': self.step_name,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'details': self.details,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SearchCache(db.Model):
    __tablename__ = 'search_cache'
    
    id = db.Column(db.Integer, primary_key=True)
    query_hash = db.Column(db.String(64), unique=True, nullable=False)  # SHA-256 hash
    query_text = db.Column(db.Text, nullable=False)
    source_type = db.Column(db.String(50), nullable=False)
    results_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    hit_count = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'query_hash': self.query_hash,
            'query_text': self.query_text,
            'source_type': self.source_type,
            'results_json': self.results_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'hit_count': self.hit_count
        }

class TTSAudio(db.Model):
    __tablename__ = 'tts_audio'
    
    id = db.Column(db.Integer, primary_key=True)
    presentation_id = db.Column(db.Integer, db.ForeignKey('presentations.id'), nullable=False)
    slide_number = db.Column(db.Integer, nullable=False)
    voice_type = db.Column(db.Enum('male_voice', 'female_voice', name='voice_type'), nullable=False)
    audio_path = db.Column(db.String(500), nullable=False)
    audio_filename = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.Numeric(6, 2))  # duration in seconds
    file_size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('presentation_id', 'slide_number', 'voice_type', name='unique_presentation_slide_voice'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'presentation_id': self.presentation_id,
            'slide_number': self.slide_number,
            'voice_type': self.voice_type,
            'audio_path': self.audio_path,
            'audio_filename': self.audio_filename,
            'duration': float(self.duration) if self.duration else None,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RateLimit(db.Model):
    __tablename__ = 'rate_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    request_count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    window_end = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'endpoint', 'window_start', name='unique_user_endpoint_window'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'endpoint': self.endpoint,
            'request_count': self.request_count,
            'window_start': self.window_start.isoformat() if self.window_start else None,
            'window_end': self.window_end.isoformat() if self.window_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

