#!/usr/bin/env python
"""
Production server runner using Waitress
"""
import os
import sys
from waitress import serve
from decouple import config

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vulnmgmt.settings')

# Import Django WSGI application
from vulnmgmt.wsgi import application

if __name__ == '__main__':
    host = config('HOST', default='127.0.0.1')
    port = config('PORT', default=8000, cast=int)
    
    print(f"Starting Vulnerability Management System on {host}:{port}")
    print("Press Ctrl+C to stop the server")
    
    serve(
        application,
        host=host,
        port=port,
        threads=4,
        connection_limit=100,
        cleanup_interval=30,
        channel_timeout=120
    )