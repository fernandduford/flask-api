#!/usr/bin/env python3
"""
API Proxy Backend Server
Handles API requests from frontend and proxies them to external APIs
Bypasses CORS restrictions and provides proper error handling
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import json
import logging
from datetime import datetime
import traceback
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app with static file serving
app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'API Proxy Backend',
        'timestamp': datetime.now().isoformat(),
        'message': 'API Proxy Backend is running successfully'
    })

@app.route('/', methods=['GET'])
def serve_frontend():
    """Serve the frontend HTML application"""
    try:
        return send_file('index.html')
    except FileNotFoundError:
        return jsonify({
            'error': 'Frontend file not found',
            'message': 'index.html is missing from the application directory'
        }), 404

@app.route('/api/proxy', methods=['POST', 'OPTIONS'])
def proxy_api_request():
    """
    Proxy API requests to external services
    Accepts configuration and request data from frontend
    """
    try:
        # Handle preflight CORS requests
        if request.method == 'OPTIONS':
            return jsonify({'status': 'ok'}), 200
        
        # Get request data from frontend
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'No request data provided',
                'success': False
            }), 400
        
        # Extract configuration
        config = data.get('config', {})
        request_body = data.get('body', {})
        
        # Validate required fields
        url = config.get('url')
        if not url:
            return jsonify({
                'error': 'No target URL provided',
                'success': False
            }), 400
        
        # Prepare headers
        headers = {
            'Content-Type': config.get('contentType', 'application/json'),
            'User-Agent': config.get('userAgent', 'okhttp/4.11.0'),
            'Accept-Encoding': config.get('acceptEncoding', 'gzip,deflate,br'),
            'x-api-key': config.get('apiKey', ''),
            'Authorization': f"Bearer {config.get('authToken', '')}" if config.get('authToken') else ''
        }
        
        # Remove empty headers
        headers = {k: v for k, v in headers.items() if v}
        
        logger.info(f"Making request to: {url}")
        logger.info(f"Headers: {json.dumps({k: v[:20] + '...' if len(v) > 20 else v for k, v in headers.items()})}")
        logger.info(f"Body: {json.dumps(request_body)}")
        
        # Make the API request
        response = requests.post(
            url=url,
            headers=headers,
            json=request_body,
            timeout=30,  # 30 seconds timeout
            verify=True  # Verify SSL certificates
        )
        
        # Log response status
        logger.info(f"Response status: {response.status_code}")
        
        # Prepare response data
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = response.text
        
        # Return response to frontend
        return jsonify({
            'success': True,
            'status_code': response.status_code,
            'data': response_data,
            'headers': dict(response.headers),
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except requests.exceptions.Timeout:
        error_msg = "Request timeout - the API took too long to respond"
        logger.error(error_msg)
        return jsonify({
            'error': error_msg,
            'success': False,
            'error_type': 'timeout'
        }), 408
        
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error - unable to reach the target API"
        logger.error(error_msg)
        return jsonify({
            'error': error_msg,
            'success': False,
            'error_type': 'connection'
        }), 503
        
    except requests.exceptions.SSLError:
        error_msg = "SSL certificate verification failed"
        logger.error(error_msg)
        return jsonify({
            'error': error_msg,
            'success': False,
            'error_type': 'ssl'
        }), 495
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error occurred: {str(e)}"
        logger.error(error_msg)
        return jsonify({
            'error': error_msg,
            'success': False,
            'error_type': 'http'
        }), 500
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"Unexpected error: {traceback.format_exc()}")
        return jsonify({
            'error': error_msg,
            'success': False,
            'error_type': 'unexpected'
        }), 500

@app.route('/api/config', methods=['GET'])
def get_default_config():
    """
    Return default configuration values
    Useful for resetting settings to defaults
    """
    default_config = {
        'apiKey': 'SIRiZ6in1plZgZyhN9ky7D4Nmx7BJ6AG8YIRPFFhKZFTHbjCOixXu2bnkDW3JMRVoga9oJn6VaSH32saRS3HsrZQCu1E9FnadxzEmlacL4IqtTAmYHGnVA48hXJnFuup',
        'authToken': 'eXFbdvzICNXmtH1ZdcBj-aaKKVtyNKqEwTITJ8Md55GrmAJh7HphndKpQXRjlwjg5-7GYML4DrFL6zl2',
        'url': 'https://www.telma.net/dashboard/bonusdata/',
        'userAgent': 'okhttp/4.11.0',
        'acceptEncoding': 'gzip,deflate,br',
        'contentType': 'application/json',
        'keys': '2YpGZvehX1S7q7fyooco6fsvLbMuEH7M463mFfHaMFAN',
        'eligibility': 'Other',
        'feature': 'RF'
    }
    
    return jsonify({
        'success': True,
        'config': default_config,
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'success': False
    }), 500

if __name__ == '__main__':
    # Print startup information
    print("=" * 60)
    print("🚀 Integrated API Testing Application Starting...")
    print("=" * 60)
    print("📋 Available Endpoints:")
    print("   GET  /          - Frontend application")
    print("   GET  /health    - Backend health check")
    print("   POST /api/proxy - API request proxy")
    print("   GET  /api/config - Default configuration")
    print("=" * 60)
    print("🌐 Full-stack application available at: http://localhost:5000")
    print("💡 Access the web interface by opening the URL in your browser")
    print("=" * 60)
    
    # Start the Flask development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )
