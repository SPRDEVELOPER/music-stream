#!/usr/bin/env python3
"""
Telegram Voice Chat Music & Video Streaming Bot
Supports YouTube, Spotify, SoundCloud, and direct links
Built with Pyrogram and PyTgCalls
"""

import asyncio
import logging
import signal
import sys
from pyrogram import Client, idle
from pytgcalls import PyTgCalls
from config import Config
from utils.helpers import setup_logging, create_directories
from handlers import play, video, control, admin

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

class MusicBot:
    def __init__(self):
        """Initialize the music bot"""
        try:
            # Validate configuration
            Config.validate_config()
            
            # Initialize Pyrogram client
            self.app = Client(
                "music_bot",
                api_id=Config.API_ID,
                api_hash=Config.API_HASH,
                bot_token=Config.BOT_TOKEN,
                plugins=dict(root="handlers")
            )
            
            # Initialize PyTgCalls client
            self.call_py = PyTgCalls(
                Client(
                    "assistant",
                    api_id=Config.API_ID,
                    api_hash=Config.API_HASH,
                    session_string=Config.SESSION_STRING
                )
            )
            
            # Store references globally
            self.app.call_py = self.call_py
            
            logger.info("✓ Music Bot initialized successfully")
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize bot: {e}")
            sys.exit(1)
    
    async def start(self):
        """Start the bot and call client"""
        try:
            # Create required directories
            create_directories()
            
            # Start PyTgCalls
            await self.call_py.start()
            logger.info("✓ PyTgCalls started")
            
            # Start Pyrogram client
            await self.app.start()
            logger.info("✓ Pyrogram client started")
            
            # Get bot info
            bot_info = await self.app.get_me()
            logger.info(f"✓ Bot started as @{bot_info.username}")
            
            # Send startup message to log chat
            if Config.LOG_CHAT_ID:
                try:
                    await self.app.send_message(
                        Config.LOG_CHAT_ID,
                        "🎵 **Music Bot Started**\n\n"
                        f"**Bot:** @{bot_info.username}\n"
                        f"**ID:** `{bot_info.id}`\n"
                        f"**Status:** Online ✅"
                    )
                except Exception as e:
                    logger.warning(f"Could not send startup message: {e}")
            
            # Keep the bot running
            await idle()
            
        except Exception as e:
            logger.error(f"✗ Error during startup: {e}")
            sys.exit(1)
    
    async def stop(self):
        """Stop the bot and call client"""
        try:
            logger.info("🔄 Shutting down bot...")
            
            # Send shutdown message to log chat
            if Config.LOG_CHAT_ID:
                try:
                    await self.app.send_message(
                        Config.LOG_CHAT_ID,
                        "🎵 **Music Bot Stopped**\n\n"
                        "**Status:** Offline ❌"
                    )
                except:
                    pass
            
            # Stop clients
            await self.call_py.stop()
            await self.app.stop()
            
            logger.info("✓ Bot stopped successfully")
            
        except Exception as e:
            logger.error(f"✗ Error during shutdown: {e}")

# Global bot instance
music_bot = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}")
    if music_bot:
        asyncio.create_task(music_bot.stop())

async def main():
    """Main function"""
    global music_bot
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start bot
    music_bot = MusicBot()
    
    try:
        await music_bot.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if music_bot:
            await music_bot.stop()

if __name__ == "__main__":
    print("""
    🎵 Telegram Voice Chat Music Bot
    ================================
    Starting bot... Please wait.
    """)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)