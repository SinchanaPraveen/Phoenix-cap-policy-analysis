#!/bin/bash
set -e  # exit immediately on any error

echo "Step 1: Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "Step 2: Extracting Phoenix CAP PDF to text..."
python scripts/extract_cap.py

echo "Step 3: Installing frontend dependencies..."
cd frontend && npm install && cd ..

echo "Setup complete. Run 'bash run.sh' to start the app."
