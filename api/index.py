"""
Vercel Serverless Function Entry Point

This module serves as the entry point for Vercel deployments.
Vercel routes all requests through this file using the serverless runtime.
"""

import os
import sys

# Ensure the parent directory (project root) is in Python path
# This allows imports of app.py and other modules from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the Flask application
from app import app

# Export the app for Vercel to discover and run it as a WSGI application
__all__ = ['app']