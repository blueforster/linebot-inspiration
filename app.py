from flask import Flask
from app.routes.webhook import webhook_bp
from app.utils.logger import setup_logger
from config.settings import Config
import logging

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        logging.error(f"Configuration error: {e}")
        raise
    
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

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0', 
        port=Config.PORT, 
        debug=Config.DEBUG
    )