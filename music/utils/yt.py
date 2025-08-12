import os
import re
import asyncio
import yt_dlp
from typing import Dict, List, Optional, Tuple
from youtubesearchpython import VideosSearch
from utils.queue import Track, MediaType
from utils.helpers import clean_filename, format_duration
import logging

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    """YouTube and other platform downloader"""
    
    def __init__(self):
        self.audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'extractaudio': True,
            'audioformat': 'mp3',
            'audio-quality': 0,
            'embed-subs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
            'extractflat': False,
        }
        
        self.video_opts = {
            'format': 'best[height<=720]',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'embed-subs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': True,
            'no_warnings': True,
            'quiet': True,
            'extractflat': False,
        }
    
    async def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for videos"""
        try:
            loop = asyncio.get_event_loop()
            search = await loop.run_in_executor(
                None, lambda: VideosSearch(query, limit=limit)
            )
            results = search.result()['result']
            return results
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def get_info(self, url: str) -> Optional[Dict]:
        """Get video/audio info"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractflat': False,
            }
            
            loop = asyncio.get_event_loop()
            
            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await loop.run_in_executor(None, extract_info)
            return info
        except Exception as e:
            logger.error(f"Info extraction error: {e}")
            return None
    
    async def download_audio(self, url: str, progress_callback=None) -> Optional[str]:
        """Download audio from URL"""
        try:
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    if 'downloaded_bytes' in d and 'total_bytes' in d:
                        asyncio.create_task(progress_callback(
                            d['downloaded_bytes'], 
                            d['total_bytes']
                        ))
            
            opts = self.audio_opts.copy()
            opts['progress_hooks'] = [progress_hook]
            
            loop = asyncio.get_event_loop()
            
            def download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    # Change extension to mp3 if needed
                    base_name = os.path.splitext(filename)[0]
                    mp3_file = f"{base_name}.mp3"
                    if os.path.exists(filename) and filename != mp3_file:
                        os.rename(filename, mp3_file)
                    return mp3_file if os.path.exists(mp3_file) else filename
            
            filepath = await loop.run_in_executor(None, download)
            return filepath if os.path.exists(filepath) else None
            
        except Exception as e:
            logger.error(f"Audio download error: {e}")
            return None
    
    async def download_video(self, url: str, progress_callback=None) -> Optional[str]:
        """Download video from URL"""
        try:
            def progress_hook(d):
                if progress_callback and d['status'] == 'downloading':
                    if 'downloaded_bytes' in d and 'total_bytes' in d:
                        asyncio.create_task(progress_callback(
                            d['downloaded_bytes'], 
                            d['total_bytes']
                        ))
            
            opts = self.video_opts.copy()
            opts['progress_hooks'] = [progress_hook]
            
            loop = asyncio.get_event_loop()
            
            def download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)
            
            filepath = await loop.run_in_executor(None, download)
            return filepath if os.path.exists(filepath) else None
            
        except Exception as e:
            logger.error(f"Video download error: {e}")
            return None
    
    def is_url(self, text: str) -> bool:
        """Check if text is a valid URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(text) is not None
    
    def get_platform(self, url: str) -> str:
        """Get platform from URL"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'soundcloud.com' in url:
            return 'soundcloud'
        elif 'spotify.com' in url:
            return 'spotify'
        else:
            return 'direct'
    
    async def create_track_from_info(self, info: Dict, media_type: MediaType, 
                                   requested_by: str, user_id: int, chat_id: int) -> Track:
        """Create track object from video info"""
        return Track(
            title=info.get('title', 'Unknown'),
            duration=info.get('duration', 0),
            url=info.get('webpage_url', info.get('url', '')),
            source=self.get_platform(info.get('webpage_url', '')),
            media_type=media_type,
            thumbnail=info.get('thumbnail', ''),
            requested_by=requested_by,
            user_id=user_id,
            chat_id=chat_id
        )

# Global downloader instance
downloader = YouTubeDownloader()