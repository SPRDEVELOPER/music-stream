import os
import logging
import asyncio
import aiohttp
import aiofiles
from typing import Union, Optional
from pyrogram.types import Message
from config import Config

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bot.log'),
            logging.StreamHandler()
        ]
    )

def create_directories():
    """Create required directories"""
    directories = ['downloads', 'cache', 'logs', 'temp']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def is_admin(message: Message) -> bool:
    """Check if user is admin"""
    user_id = message.from_user.id
    
    # Owner is always admin
    if Config.OWNER_ID and user_id == Config.OWNER_ID:
        return True
    
    # Sudo users are admins
    if user_id in Config.SUDO_USERS:
        return True
    
    return False

async def is_group_admin(message: Message, user_id: int = None) -> bool:
    """Check if user is group admin"""
    if not user_id:
        user_id = message.from_user.id
    
    try:
        chat_member = await message.chat.get_member(user_id)
        return chat_member.status in ["administrator", "creator"]
    except:
        return False

def format_duration(seconds: int) -> str:
    """Format duration from seconds to MM:SS or HH:MM:SS"""
    if seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def format_bytes(bytes_size: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

async def download_file(url: str, filename: str) -> bool:
    """Download file from URL"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(filename, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    return True
        return False
    except Exception as e:
        logging.error(f"Download error: {e}")
        return False

def clean_filename(filename: str) -> str:
    """Clean filename for filesystem"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:100]  # Limit filename length

async def run_command(command: str) -> tuple:
    """Run shell command asynchronously"""
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        return -1, "", str(e)

def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def cleanup_file(filepath: str):
    """Clean up temporary file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except:
        pass

class Progress:
    """Progress tracker for downloads"""
    
    def __init__(self, message: Message, action: str = "Downloading"):
        self.message = message
        self.action = action
        self.last_update = 0
    
    async def update(self, current: int, total: int):
        """Update progress"""
        import time
        
        now = time.time()
        if now - self.last_update < 2:  # Update every 2 seconds
            return
        
        self.last_update = now
        percentage = (current / total) * 100
        
        try:
            await self.message.edit_text(
                f"**{self.action}...**\n\n"
                f"**Progress:** {percentage:.1f}%\n"
                f"**Size:** {format_bytes(current)} / {format_bytes(total)}"
            )
        except:
            pass