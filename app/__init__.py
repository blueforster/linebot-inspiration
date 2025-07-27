from flask import Flask
import logging

def create_app():
    app = Flask(__name__)
    
    # 設定基本日誌
    logging.basicConfig(level=logging.INFO)
    
    @app.route('/health')
    def health_check():
        app.logger.info("Health check accessed")
        return {'status': 'healthy', 'service': 'linebot-inspiration'}, 200
    
    @app.route('/')
    def index():
        app.logger.info("Root endpoint accessed")
        return {'message': 'LINE Bot Inspiration Notes API', 'status': 'running'}, 200
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        app.logger.info("Webhook endpoint accessed")
        return '', 200
    
    @app.before_request
    def log_request():
        from flask import request
        app.logger.info(f"Request received: {request.method} {request.path}")
    
    return app