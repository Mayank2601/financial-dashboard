#!/bin/bash

# Dashboard Launcher for Shri Hari Organic Farms Account Analysis
# This script launches the interactive dashboard

echo "================================================================================"
echo "  📊 Financial Dashboard - Shri Hari Organic Farms"
echo "================================================================================"
echo ""
echo "Starting interactive dashboard..."
echo "The dashboard will open automatically in your browser."
echo ""
echo "Press Ctrl+C to stop the dashboard when you're done."
echo "================================================================================"
echo ""

cd "/Users/mayankkaura/Account_statement analyzer"

# Use python module (works when streamlit is installed with --user)
python3 -m streamlit run dashboard.py
