#!/bin/bash

echo "============================================================"
echo "🧠 Second Brain - Quick Start"
echo "============================================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo ""
    echo "Install it with:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    echo ""
    echo "Or download from: https://ollama.com/download"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if llama3 is downloaded
if ! ollama list | grep -q "llama3"; then
    echo "📥 Llama 3 not found. Downloading..."
    ollama pull llama3
else
    echo "✅ Llama 3 is ready"
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🚀 Starting Ollama server..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
else
    echo "✅ Ollama server is running"
fi

# Check Python dependencies
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install -r requirements.txt
else
    echo "✅ Python dependencies installed"
fi

echo ""
echo "============================================================"
echo "🎉 Everything is ready!"
echo "============================================================"
echo ""
echo "Starting Second Brain server..."
echo ""

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)

if [ -n "$LOCAL_IP" ]; then
    echo "Access from this Mac:    http://localhost:5000"
    echo "Access from your phone:  http://$LOCAL_IP:5000"
else
    echo "Access from this Mac:    http://localhost:5000"
    echo "Access from your phone:  Find your Mac's IP in System Preferences > Network"
fi

echo ""
echo "Press Ctrl+C to stop"
echo "============================================================"
echo ""

# Start the server
python3 server.py
