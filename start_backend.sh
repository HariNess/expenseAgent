#!/bin/bash
echo "🚀 Starting NessExpense Backend..."

cd "$(dirname "$0")"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Copy env if not exists
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "⚠️  Created .env from template. Please add your ANTHROPIC_API_KEY."
fi

# Create database directory
mkdir -p database

# Start server
echo "✅ Starting FastAPI server on http://localhost:8081"
echo "📖 API docs at http://localhost:8081/docs"
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8081
