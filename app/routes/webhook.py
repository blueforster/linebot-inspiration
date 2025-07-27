from flask import Blueprint, request, abort, jsonify
import logging
from app.services.line_service import LineService
from app.utils.logger import get_logger

webhook_bp = Blueprint('webhook', __name__)
logger = get_logger(__name__)

# Initialize LINE service
line_service = LineService()

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Get request signature
        signature = request.headers.get('X-Line-Signature', '')
        if not signature:
            logger.warning("Missing X-Line-Signature header")
            abort(400)
        
        # Get request body
        body = request.get_data(as_text=True)
        if not body:
            logger.warning("Empty request body")
            abort(400)
        
        logger.info(f"Webhook received: signature={signature[:20]}...")
        
        # Handle webhook
        success = line_service.handle_webhook(body, signature)
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            logger.error("Webhook handling failed")
            abort(400)
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        abort(500)

@webhook_bp.route('/webhook/health', methods=['GET'])
def webhook_health():
    try:
        # Check services health
        sheets_healthy = line_service.sheets_service.is_healthy()
        
        health_status = {
            'webhook': True,
            'sheets_service': sheets_healthy,
            'timestamp': line_service.sheets_service.get_user_statistics('health_check').get('last_message', 'unknown')
        }
        
        status_code = 200 if all(health_status.values()) else 503
        
        return jsonify({
            'status': 'healthy' if status_code == 200 else 'unhealthy',
            'services': health_status
        }), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500