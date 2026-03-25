#!/bin/bash
echo "🚀 Starting NessExpense Frontend..."

cd "$(dirname "$0")/frontend"

# Install if needed
if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm packages..."
  npm install
fi

echo "✅ Starting React dev server on http://localhost:8080"
npm run dev
