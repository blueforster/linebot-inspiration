from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # 最基本的路由，避免所有可能的導入問題
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'linebot-inspiration'}, 200
    
    @app.route('/')
    def index():
        return {'message': 'LINE Bot Inspiration Notes API', 'status': 'running'}, 200
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        return '', 200
    
    return app