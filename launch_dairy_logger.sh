#!/bin/bash

# Dairy Business Logging App Launcher
# Manual entry for orders, income, expenses with analytics

echo "================================================================================"
echo "  Dairy Business Logging & Analysis"
echo "================================================================================"
echo ""
echo "Starting app..."
echo "The dashboard will open automatically in your browser."
echo ""
echo "Press Ctrl+C to stop when you're done."
echo "================================================================================"
echo ""

cd "/Users/mayankkaura/Account_statement analyzer"

python3 -m streamlit run dairy_logger.py
