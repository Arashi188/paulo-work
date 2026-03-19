import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# This is the serverless entry point for Vercel
app = create_app()

# Vercel looks for this variable name
handler = app