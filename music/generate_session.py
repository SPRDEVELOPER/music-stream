#!/usr/bin/env python3
"""
Session String Generator for Telegram Music Bot
Run this script to generate the SESSION_STRING for your .env file
"""

from pyrogram import Client

print("🎵 Telegram Music Bot - Session String Generator")
print("=" * 50)

# Get API credentials
api_id = input("Enter your API ID: ")
api_hash = input("Enter your API HASH: ")

print("\nℹ️  You will be asked to enter your phone number and verification code.")
print("📱 Make sure you have access to your Telegram account.\n")

# Create client and generate session
app = Client("session_generator", api_id=int(api_id), api_hash=api_hash)

with app:
    session_string = app.export_session_string()
    print(f"✅ Your SESSION_STRING:\n\n{session_string}")
    print(f"\n💾 Save this SESSION_STRING in your .env file!")
    print("🔒 Keep this session string private and secure!")

print("\n✨ Session string generated successfully!")
print("🎵 You can now start your music bot!")