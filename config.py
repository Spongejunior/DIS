import os
from datetime import timedelta

class Config:
    # Security - must be overridden in production
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database - supports both local SQLite and PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    # Handle SQLite-specific requirements for local development
    if DATABASE_URL and 'sqlite' in DATABASE_URL:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'connect_args': {'check_same_thread': False}
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {}
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = True  # Only send over HTTPS in production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    
    # Email settings (for production)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or 'no-reply@chiwetocare.local'
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'true').lower() == 'true'
    
    # Application settings
    APP_NAME = 'Animal Health System'
    VERSION = '2.1.4'

    # Internationalization (i18n)
    LANGUAGES = ['en', 'chi', 'tum']
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    
    # Prediction settings
    PREDICTION_TIMEOUT = 30  # seconds
    MAX_PREDICTIONS_PER_DAY = 1000
    
    @staticmethod
    def init_app(app):
        # Ensure upload folder exists
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    TESTING = False
    # Additional production security settings
    PREFERRED_URL_SCHEME = 'https'

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # This will resolve to /app/uploads inside the container
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads') 
    SQLALCHEMY_ECHO = True
    def init_app(self, app):
        app.config['UPLOAD_FOLDER'] = self.UPLOAD_FOLDER
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}