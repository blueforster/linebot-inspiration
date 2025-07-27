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
        # Try Base64 encoded credentials first
        google_creds_base64 = os.environ.get('GOOGLE_CREDENTIALS_BASE64')
        google_creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        
        logger.info(f"Base64 credentials available: {'✓' if google_creds_base64 else '✗'}")
        logger.info(f"JSON credentials available: {'✓' if google_creds_json else '✗'}")
        logger.info(f"Sheet ID: {sheet_id[:20] + '...' if sheet_id else 'None'}")
        
        # Get credentials from Base64 or JSON
        cred_json = None
        if google_creds_base64:
            try:
                decoded_creds = base64.b64decode(google_creds_base64).decode()
                cred_json = decoded_creds
                logger.info("Using Base64 encoded credentials")
            except Exception as e:
                logger.error(f"Failed to decode Base64 credentials: {e}")
        
        if not cred_json and google_creds_json:
            cred_json = google_creds_json
            logger.info("Using JSON credentials")
        
        if not cred_json:
            logger.error("No Google credentials found (neither Base64 nor JSON)")
            return
            
        if not sheet_id:
            logger.error("GOOGLE_SHEET_ID environment variable not set")
            return
        
        # Parse JSON credentials
        try:
            cred_dict = json.loads(cred_json)
            logger.info(f"Credentials type: {cred_dict.get('type', 'unknown')}")
            logger.info(f"Project ID: {cred_dict.get('project_id', 'unknown')}")
            
            # Fix private key formatting
            if 'private_key' in cred_dict:
                private_key = cred_dict['private_key']
                logger.info(f"Original private key length: {len(private_key)}")
                logger.info(f"Private key starts with: {private_key[:50]}...")
                
                # Handle different newline encodings
                if '\\n' in private_key:
                    # Replace literal \n with actual newlines
                    private_key = private_key.replace('\\n', '\n')
                    logger.info("Replaced \\n with actual newlines")
                
                # Fix Base64 padding issues in private key content
                lines = private_key.split('\n')
                fixed_lines = []
                for line in lines:
                    if line and not line.startswith('-----'):
                        # This is a Base64 content line, fix padding
                        missing_padding = len(line) % 4
                        if missing_padding:
                            line += '=' * (4 - missing_padding)
                            logger.info(f"Fixed padding for line: {line[:20]}...")
                    fixed_lines.append(line)
                
                private_key = '\n'.join(fixed_lines)
                
                # Ensure proper formatting
                if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                    logger.error("Private key doesn't start with proper header")
                if not private_key.endswith('-----END PRIVATE KEY-----\n'):
                    if private_key.endswith('-----END PRIVATE KEY-----'):
                        private_key += '\n'
                    logger.info("Added missing trailing newline")
                
                cred_dict['private_key'] = private_key
                logger.info(f"Final private key length: {len(private_key)}")
                logger.info("Private key processing completed")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Google credentials JSON: {e}")
            return
        
        # Create credentials - try different methods
        credentials = None
        try:
            # Method 1: from_service_account_info
            credentials = Credentials.from_service_account_info(
                cred_dict,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            logger.info("Successfully created credentials using from_service_account_info")
        except Exception as e:
            logger.error(f"Method 1 failed: {e}")
            
            # Method 2: Write to temp file and use from_service_account_file
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(cred_dict, f)
                    temp_file_path = f.name
                
                credentials = Credentials.from_service_account_file(
                    temp_file_path,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                
                # Clean up temp file
                os.unlink(temp_file_path)
                logger.info("Successfully created credentials using temp file method")
            except Exception as e2:
                logger.error(f"Method 2 also failed: {e2}")
                return
        
        if not credentials:
            logger.error("Could not create Google credentials")
            return
        
        # Connect to Google Sheets
        client = gspread.authorize(credentials)
        sheets_service = client.open_by_key(sheet_id).sheet1
        logger.info("Google Sheets initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {e}")
        import traceback
        logger.error(traceback.format_exc())

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
        
        # Add message to Google Sheets
        success = add_message_to_sheet(user_id, 'text', text_content)
        
        # Send reply
        if success:
            reply_text = f"✅ 已記錄：{text_content}"
        else:
            reply_text = "❌ 記錄失敗，請稍後再試"
        
        if line_bot_api:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
        
    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        if line_bot_api:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="處理訊息時發生錯誤")
            )

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