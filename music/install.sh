#!/bin/bash

echo "🎵 Telegram Music Bot - Installation Script"
echo "=========================================="

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
apt install -y python3 python3-pip ffmpeg git curl wget

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip3 install -r requirements.txt

# Create required directories
echo "📁 Creating directories..."
mkdir -p downloads cache temp logs

# Set permissions
echo "🔐 Setting permissions..."
chmod +x install.sh
chmod +x main.py

echo "✅ Installation completed!"
echo ""
echo "🔑 Setup Instructions:"
echo "1. Create a bot with @BotFather and get BOT_TOKEN"
echo "2. Get API_ID and API_HASH from https://my.telegram.org"
echo "3. Run 'python3 generate_session.py' to get SESSION_STRING"
echo "4. Fill in the .env file with your credentials"
echo "5. Run 'python3 main.py' to start the bot"
echo ""
echo "🎵 Enjoy your music bot!"