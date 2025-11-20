#!/bin/bash
# Quick start script for AI Receptionist

set -e

echo "🤖 AI Receptionist - Quick Start"
echo "================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📋 Please copy env.example to .env and configure your API keys:"
    echo "   cp env.example .env"
    echo "   nano .env  # or use your preferred editor"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create data directory
mkdir -p data

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Starting AI Receptionist server..."
echo "   Server will be available at: http://localhost:8000"
echo "   Health check: http://localhost:8000/healthz"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "⚠️  Remember to:"
echo "   1. Expose with ngrok: ngrok http 8000"
echo "   2. Update PUBLIC_URL in .env"
echo "   3. Configure Twilio webhook to your ngrok URL + /voice/incoming"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

