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
        # 最簡單的 webhook - 先確保能回應 200
        logger.info("Webhook received")
        return '', 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return '', 500

@webhook_bp.route('/webhook/health', methods=['GET'])
def webhook_health():
    return jsonify({
        'status': 'healthy',
        'webhook': 'ok'
    }), 200