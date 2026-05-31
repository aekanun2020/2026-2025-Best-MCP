#!/bin/bash
# Start AuthenticRAG UI System
# This script starts both FastAPI backend and Streamlit frontend

echo "🚀 Starting AuthenticRAG UI System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements-ui.txt
else
    source venv/bin/activate
fi

# Check if OpenSearch is running
echo "🔍 Checking OpenSearch..."
if curl -s http://localhost:9200 > /dev/null; then
    echo "✅ OpenSearch is running"
else
    echo "❌ OpenSearch is not running!"
    echo "Please start OpenSearch first:"
    echo "  brew services start opensearch"
    exit 1
fi

# Check if API dependencies are installed
echo "📦 Checking dependencies..."
python -c "import fastapi, uvicorn, streamlit" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing UI dependencies..."
    pip install -r requirements-ui.txt
fi

echo ""
echo "✅ All checks passed!"
echo ""
echo "Starting services..."
echo "  📡 FastAPI Backend: http://localhost:8001"
echo "  🌐 Streamlit UI: http://localhost:8501"
echo "  📚 API Docs: http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start FastAPI in background
echo "🔧 Starting FastAPI backend..."
python api_server.py > api_server.log 2>&1 &
API_PID=$!
echo "  PID: $API_PID"

# Wait for API to start
sleep 3

# Check if API is running
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ FastAPI backend started successfully"
else
    echo "❌ Failed to start FastAPI backend"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Start Streamlit
echo ""
echo "🎨 Starting Streamlit frontend..."
streamlit run streamlit_app.py

# Cleanup on exit
echo ""
echo "🛑 Stopping services..."
kill $API_PID 2>/dev/null
echo "✅ All services stopped"
