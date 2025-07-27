#!/usr/bin/env python3
"""
Simple standalone server for Zeabur
"""
import os
from flask import Flask, jsonify, request

# Create Flask app directly
app = Flask(__name__)

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

@app.route('/webhook', methods=['POST'])
def webhook():
    return '', 200

if __name__ == '__main__':
    # Debug environment variables
    print("=== Environment Debug ===")
    print(f"PORT environment variable: {os.environ.get('PORT', 'not set')}")
    print(f"All environment variables containing PORT:")
    for key, value in os.environ.items():
        if 'PORT' in key.upper():
            print(f"  {key} = {value}")
    print("========================")
    
    # Force use port 8080 since Zeabur expects it
    port = 8080
    print(f"Starting server on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)