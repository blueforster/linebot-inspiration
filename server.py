#!/usr/bin/env python3
"""
LINE Bot server with Google Sheets integration
"""
import os
import json
import logging
import tempfile
import base64
from datetime import datetime
from flask import Flask, jsonify, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import gspread
from google.oauth2.service_account import Credentials

# Create Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE Bot configuration
line_bot_api = None
handler = None
sheets_service = None

def init_line_bot():
    global line_bot_api, handler
    try:
        access_token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
        channel_secret = os.environ.get('LINE_CHANNEL_SECRET')
        
        if access_token and channel_secret:
            line_bot_api = LineBotApi(access_token)
            handler = WebhookHandler(channel_secret)
            # Add message handler
            handler.add(MessageEvent, message=TextMessage)(handle_text_message)
            logger.info("LINE Bot initialized successfully")
        else:
            logger.warning("LINE Bot credentials not found")
    except Exception as e:
        logger.error(f"Failed to initialize LINE Bot: {e}")

def init_google_sheets():
    global sheets_service
    try:
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        
        if not sheet_id:
            logger.warning("GOOGLE_SHEET_ID not set - Google Sheets disabled")
            sheets_service = None
            return
        
        # Create credentials using only the essential fields
        # This bypasses many potential formatting issues
        cred_info = {
            "type": "service_account",
            "project_id": "linebot-note-01",
            "private_key_id": "4fbedd350181527528524ae041a671334c02210b",
            "client_email": "forsterlin@linebot-note-01.iam.gserviceaccount.com",
            "client_id": "118317723130164740048",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/forsterlin%40linebot-note-01.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        # Try to get private key from environment
        private_key_env = os.environ.get('GOOGLE_PRIVATE_KEY')
        if private_key_env:
            # Replace \\n with actual newlines if needed
            private_key = private_key_env.replace('\\n', '\n')
            cred_info["private_key"] = private_key
            logger.info("Using private key from GOOGLE_PRIVATE_KEY environment variable")
        else:
            logger.error("GOOGLE_PRIVATE_KEY environment variable not found")
            sheets_service = None
            return
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            cred_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        # Connect to Google Sheets
        client = gspread.authorize(credentials)
        sheets_service = client.open_by_key(sheet_id).sheet1
        logger.info("Google Sheets initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {e}")
        sheets_service = None

def add_message_to_sheet(user_id, message_type, content):
    try:
        if sheets_service:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row_data = [timestamp, message_type, content, user_id, '', 'processed']
            sheets_service.insert_row(row_data, 2)  # Insert at row 2 (after header)
            logger.info(f"Message added to sheet: {content[:50]}...")
            return True
    except Exception as e:
        logger.error(f"Failed to add message to sheet: {e}")
    return False

@app.route('/')
def index():
    return jsonify({
        'message': 'LINE Bot Inspiration Notes API', 
        'status': 'running',
        'port': os.environ.get('PORT', 'unknown')
    }), 200

@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy', 
        'service': 'linebot-inspiration',
        'port': os.environ.get('PORT', 'unknown')
    }), 200

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    # Handle LINE webhook verification
    if request.method == 'GET':
        return 'Webhook endpoint is ready', 200
    
    # Handle POST requests from LINE
    try:
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        logger.info(f"Webhook received: signature={signature[:20]}...")
        
        if handler:
            handler.handle(body, signature)
        else:
            logger.warning("LINE Bot handler not initialized")
        
        return '', 200
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return '', 500

def handle_text_message(event):
    try:
        user_id = event.source.user_id
        text_content = event.message.text
        
        logger.info(f"Received message from {user_id}: {text_content}")
        
        # Try to add message to Google Sheets
        success = add_message_to_sheet(user_id, 'text', text_content)
        
        # Send reply based on result
        if success:
            reply_text = f"✅ 已記錄到 Google Sheets：{text_content}"
        elif sheets_service is None:
            reply_text = f"📝 收到訊息：{text_content}\n(Google Sheets 未初始化)"
        else:
            reply_text = f"❌ 記錄失敗：{text_content}\n請稍後再試"
        
        if line_bot_api:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            logger.info("Reply sent successfully")
        else:
            logger.error("LINE Bot API not initialized")
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        if line_bot_api:
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="處理訊息時發生錯誤")
                )
            except Exception as e2:
                logger.error(f"Failed to send error reply: {e2}")

# Initialize services when module is loaded
init_line_bot()
init_google_sheets()

if __name__ == '__main__':
    # Debug environment variables
    logger.info("=== Environment Debug ===")
    logger.info(f"LINE_CHANNEL_ACCESS_TOKEN: {'✓' if os.environ.get('LINE_CHANNEL_ACCESS_TOKEN') else '✗'}")
    logger.info(f"LINE_CHANNEL_SECRET: {'✓' if os.environ.get('LINE_CHANNEL_SECRET') else '✗'}")
    logger.info(f"GOOGLE_SERVICE_ACCOUNT_JSON: {'✓' if os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON') else '✗'}")
    logger.info(f"GOOGLE_SHEET_ID: {'✓' if os.environ.get('GOOGLE_SHEET_ID') else '✗'}")
    logger.info("========================")
    
    # Use port 5000 as configured
    port = 5000
    logger.info(f"Starting LINE Bot server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)