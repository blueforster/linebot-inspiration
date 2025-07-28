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
from linebot.models import MessageEvent, TextMessage, AudioMessage, TextSendMessage
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import speech
import urllib.request
import io

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
            # Add message handlers
            handler.add(MessageEvent, message=TextMessage)(handle_text_message)
            handler.add(MessageEvent, message=AudioMessage)(handle_audio_message)
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
            # Multiple attempts to fix the private key format
            private_key = private_key_env
            
            # Method 1: Replace \\n with actual newlines
            if '\\n' in private_key:
                private_key = private_key.replace('\\n', '\n')
                logger.info("Converted \\n to newlines in private key")
            
            # Method 2: Ensure proper header and footer, add if missing
            if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
                logger.warning("Private key missing proper header, adding it")
                private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
            if not private_key.endswith('-----END PRIVATE KEY-----'):
                logger.warning("Private key missing proper footer, adding it")
                private_key = private_key + '\n-----END PRIVATE KEY-----'
            
            # Method 3: Log key structure for debugging
            lines = private_key.split('\n')
            logger.info(f"Private key has {len(lines)} lines")
            if lines:
                logger.info(f"First line: '{lines[0][:50]}...'")
                logger.info(f"Last line: '...{lines[-1][-50:]}'")
            else:
                logger.info("Private key lines are empty")
            
            # Method 4: Try to reconstruct the key if it's mangled
            if len(lines) < 3:  # Should have header, content, footer at minimum
                logger.warning("Private key appears to be on single line, attempting to reconstruct")
                # This is a common issue - the key gets flattened
                # Let's try to rebuild it properly
                if '-----BEGIN PRIVATE KEY-----' in private_key and '-----END PRIVATE KEY-----' in private_key:
                    # Extract just the base64 content between headers
                    start = private_key.find('-----BEGIN PRIVATE KEY-----') + len('-----BEGIN PRIVATE KEY-----')
                    end = private_key.find('-----END PRIVATE KEY-----')
                    base64_content = private_key[start:end].strip()
                    
                    # Rebuild with proper line breaks (64 chars per line is standard)
                    lines = []
                    lines.append('-----BEGIN PRIVATE KEY-----')
                    for i in range(0, len(base64_content), 64):
                        lines.append(base64_content[i:i+64])
                    lines.append('-----END PRIVATE KEY-----')
                    
                    private_key = '\n'.join(lines)
                    logger.info("Reconstructed private key with proper line breaks")
            
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

def convert_audio_to_text(audio_content, content_type='audio/m4a'):
    """Convert audio content to text using Google Speech-to-Text"""
    try:
        # Initialize Speech client with credentials
        cred_info = get_google_credentials()
        if not cred_info:
            raise Exception("Failed to get Google credentials")
            
        credentials = Credentials.from_service_account_info(
            cred_info,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        speech_client = speech.SpeechClient(credentials=credentials)
        
        # Configure audio settings - let Google detect format automatically
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            language_code='zh-TW',  # Traditional Chinese
            alternative_language_codes=['en-US', 'ja-JP'],  # Fallback languages
            enable_automatic_punctuation=True,
        )
        
        # Perform speech recognition
        response = speech_client.recognize(config=config, audio=audio)
        
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            confidence = response.results[0].alternatives[0].confidence
            logger.info(f"Speech recognition result: {transcript} (confidence: {confidence:.2f})")
            return transcript
        else:
            logger.warning("No speech recognition results")
            return None
            
    except Exception as e:
        logger.error(f"Speech-to-text conversion failed: {e}")
        return None

def get_google_credentials():
    """Get Google credentials for speech API"""
    try:
        private_key_env = os.environ.get('GOOGLE_PRIVATE_KEY')
        if not private_key_env:
            raise Exception("GOOGLE_PRIVATE_KEY not found")
            
        # Use same format fixing as Google Sheets
        private_key = private_key_env
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            private_key = '-----BEGIN PRIVATE KEY-----\n' + private_key
        if not private_key.endswith('-----END PRIVATE KEY-----'):
            private_key = private_key + '\n-----END PRIVATE KEY-----'
            
        return {
            "type": "service_account",
            "project_id": "linebot-note-01",
            "private_key_id": "4fbedd350181527528524ae041a671334c02210b",
            "private_key": private_key,
            "client_email": "forsterlin@linebot-note-01.iam.gserviceaccount.com",
            "client_id": "118317723130164740048",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/forsterlin%40linebot-note-01.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
    except Exception as e:
        logger.error(f"Failed to get Google credentials: {e}")
        return None

def handle_audio_message(event):
    try:
        user_id = event.source.user_id
        message_id = event.message.id
        
        logger.info(f"Received audio message from {user_id}: {message_id}")
        
        # Download audio content from LINE
        if line_bot_api:
            message_content = line_bot_api.get_message_content(message_id)
            audio_data = b''
            for chunk in message_content.iter_content():
                audio_data += chunk
            
            logger.info(f"Downloaded audio file, size: {len(audio_data)} bytes")
            
            # Convert audio to text
            transcript = convert_audio_to_text(audio_data, 'audio/m4a')
            
            if transcript:
                # Add transcribed text to Google Sheets
                success = add_message_to_sheet(user_id, 'audio', f"🎵 語音轉文字: {transcript}")
                
                if success:
                    reply_text = f"🎵 語音已轉文字並記錄：\n「{transcript}」"
                else:
                    reply_text = f"🎵 語音轉文字完成：\n「{transcript}」\n(記錄到 Google Sheets 失敗)"
            else:
                # Still record that an audio message was received
                add_message_to_sheet(user_id, 'audio', "🎵 語音訊息 (轉文字失敗)")
                reply_text = "🎵 收到語音訊息，但轉文字失敗，請重新錄製清楚一點的語音"
            
            # Send reply
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )
            logger.info("Audio message processed and reply sent")
        else:
            logger.error("LINE Bot API not initialized for audio processing")
            
    except Exception as e:
        logger.error(f"Error handling audio message: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        if line_bot_api:
            try:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="處理語音訊息時發生錯誤，請稍後再試")
                )
            except Exception as e2:
                logger.error(f"Failed to send audio error reply: {e2}")

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