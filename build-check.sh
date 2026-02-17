#!/bin/bash

# SaraokuDB Build Check Script
# This script runs the frontend build process to verify its integrity.

echo "--- Starting Frontend Build Check ---"
cd "$(dirname "$0")/frontend" || exit

if npm run build; then
    echo ""
    echo "✅ Build SUCCESSFUL!"
    echo "You can safely commit your changes."
else
    echo ""
    echo "❌ Build FAILED!"
    echo "Please check the errors above before committing."
    exit 1
fi
