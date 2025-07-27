from flask import Flask
from config.settings import Config
from app.utils.logger import setup_logger
from app.routes.webhook import webhook_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configuration
    Config.validate_config()
    
    # Setup logging
    setup_logger(app)
    
    # Register blueprints
    app.register_blueprint(webhook_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'linebot-inspiration'}, 200
    
    # Root endpoint
    @app.route('/')
    def index():
        return {'message': 'LINE Bot Inspiration Notes API', 'status': 'running'}, 200
    
    return app