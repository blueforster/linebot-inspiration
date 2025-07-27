#!/usr/bin/env python3
"""
Minimal test app to isolate 502 error
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {'message': 'Hello from minimal test app'}, 200

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)