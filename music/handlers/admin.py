from pyrogram import Client, filters
from pyrogram.types import Message
from utils.queue import get_queue, queues
from utils.helpers import is_admin
from config import Config
import psutil
import os
import asyncio
import logging

logger = logging.getLogger(__name__)

@Client.on_message(filters.command(["stats", "status"]) & filters.private)
async def stats_command(client: Client, message: Message):
    """Show bot statistics (admin only)"""
    try:
        if not is_admin(message):
            await message.reply_text("❌ **You don't have permission to use this command!**")
            return
        
        # Get system stats
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get bot stats
        active_chats = len(queues)
        total_tracks = sum(len(q.queue) + (1 if q.current else 0) for q in queues.values())
        playing_chats = sum(1 for q in queues.values() if q.is_playing)
        
        stats_text = (
            f"📊 **Bot Statistics**\n\n"
            f"**System:**\n"
            f"• CPU: {cpu_percent}%\n"
            f"• RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)\n"
            f"• Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)\n\n"
            f"**Bot:**\n"
            f"• Active Chats: {active_chats}\n"
            f"• Playing Chats: {playing_chats}\n"
            f"• Total Tracks: {total_tracks}\n"
            f"• Uptime: {get_uptime()}"
        )
        
        await message.reply_text(stats_text)
    
    except Exception as e:
        logger.error(f"Stats command error: {e}")
        await message.reply_text("❌ **Error:** Could not get statistics.")

@Client.on_message(filters.command(["logs"]) & filters.private)
async def logs_command(client: Client, message: Message):
    """Send bot logs (admin only)"""
    try:
        if not is_admin(message):
            await message.reply_text("❌ **You don't have permission to use this command!**")
            return
        
        log_file = "bot.log"
        if os.path.exists(log_file):
            await message.reply_document(log_file, caption="📋 **Bot Logs**")
        else:
            await message.reply_text("❌ **No log file found!**")
    
    except Exception as e:
        logger.error(f"Logs command error: {e}")
        await message.reply_text("❌ **Error:** Could not send logs.")

@Client.on_message(filters.command(["broadcast"]) & filters.private)
async def broadcast_command(client: Client, message: Message):
    """Broadcast message to all chats (admin only)"""
    try:
        if not is_admin(message):
            await message.reply_text("❌ **You don't have permission to use this command!**")
            return
        
        if len(message.command) < 2:
            await message.reply_text("**Usage:** `/broadcast <message>`")
            return
        
        broadcast_text = message.text.split(None, 1)[1]
        
        sent = 0
        failed = 0
        
        status_msg = await message.reply_text("📡 **Broadcasting message...**")
        
        for chat_id in queues.keys():
            try:
                await client.send_message(chat_id, f"📢 **Broadcast Message:**\n\n{broadcast_text}")
                sent += 1
            except:
                failed += 1
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(0.1)
        
        await status_msg.edit_text(
            f"📡 **Broadcast Complete!**\n\n"
            f"✅ **Sent:** {sent}\n"
            f"❌ **Failed:** {failed}"
        )
    
    except Exception as e:
        logger.error(f"Broadcast command error: {e}")
        await message.reply_text("❌ **Error:** Could not broadcast message.")

@Client.on_message(filters.command(["cleanup"]) & filters.private)
async def cleanup_command(client: Client, message: Message):
    """Clean up temporary files (admin only)"""
    try:
        if not is_admin(message):
            await message.reply_text("❌ **You don't have permission to use this command!**")
            return
        
        # Clean up downloads directory
        downloads_dir = "downloads"
        temp_dir = "temp"
        cache_dir = "cache"
        
        cleaned_files = 0
        freed_space = 0
        
        for directory in [downloads_dir, temp_dir, cache_dir]:
            if os.path.exists(directory):
                for filename in os.listdir(directory):
                    filepath = os.path.join(directory, filename)
                    try:
                        file_size = os.path.getsize(filepath)
                        os.remove(filepath)
                        cleaned_files += 1
                        freed_space += file_size
                    except:
                        pass
        
        await message.reply_text(
            f"🧹 **Cleanup Complete!**\n\n"
            f"🗑️ **Files cleaned:** {cleaned_files}\n"
            f"💾 **Space freed:** {freed_space // (1024**2)} MB"
        )
    
    except Exception as e:
        logger.error(f"Cleanup command error: {e}")
        await message.reply_text("❌ **Error:** Could not perform cleanup.")

@Client.on_message(filters.command(["restart"]) & filters.private)
async def restart_command(client: Client, message: Message):
    """Restart the bot (admin only)"""
    try:
        if not is_admin(message):
            await message.reply_text("❌ **You don't have permission to use this command!**")
            return
        
        await message.reply_text("🔄 **Restarting bot...**")
        
        # Clean up all voice chats
        for chat_id, queue in queues.items():
            try:
                if queue.is_playing:
                    await client.call_py.leave_group_call(chat_id)
            except:
                pass
        
        # Clear all queues
        queues.clear()
        
        # Send restart signal
        os.execv(__file__, [__file__] + [])
    
    except Exception as e:
        logger.error(f"Restart command error: {e}")
        await message.reply_text("❌ **Error:** Could not restart bot.")

def get_uptime() -> str:
    """Get bot uptime"""
    try:
        with open("/proc/uptime", "r") as f:
            uptime_seconds = float(f.readline().split()[0])
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        return f"{days}d {hours}h {minutes}m"
    except:
        return "Unknown"

@Client.on_message(filters.command(["help", "start"]))
async def help_command(client: Client, message: Message):
    """Show help message"""
    try:
        bot_info = await client.get_me()
        
        help_text = (
            f"🎵 **{bot_info.first_name} - Voice Chat Music Bot**\n\n"
            f"**🎧 Music Commands:**\n"
            f"• `/play <song name/URL>` - Play audio\n"
            f"• `/video <video name/URL>` - Play video\n"
            f"• `/pause` - Pause playback\n"
            f"• `/resume` - Resume playback\n"
            f"• `/skip` - Skip current track\n"
            f"• `/stop` - Stop and clear queue\n\n"
            f"**📋 Queue Commands:**\n"
            f"• `/queue` - Show current queue\n"
            f"• `/np` - Now playing info\n"
            f"• `/loop` - Toggle loop mode\n"
            f"• `/shuffle` - Shuffle queue\n"
            f"• `/clear` - Clear queue\n\n"
            f"**🎯 Supported Sources:**\n"
            f"• YouTube (youtube.com, youtu.be)\n"
            f"• SoundCloud (soundcloud.com)\n"
            f"• Direct MP3/MP4 links\n"
            f"• Many other platforms via yt-dlp\n\n"
            f"**💡 Tips:**\n"
            f"• Start a voice chat in your group\n"
            f"• Admin permissions required for controls\n"
            f"• Maximum duration: {Config.MAX_DURATION // 60} minutes\n"
            f"• Queue limit: {Config.QUEUE_LIMIT} tracks\n\n"
            f"**🔧 Support:** Contact bot owner for issues"
        )
        
        await message.reply_text(help_text)
    
    except Exception as e:
        logger.error(f"Help command error: {e}")
        await message.reply_text("❌ **Error:** Could not send help message.")