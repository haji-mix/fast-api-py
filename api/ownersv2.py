from fastapi import Request, Query
from fastapi.responses import Response
import random
import aiohttp
import os
from pathlib import Path

meta = {
    "name": "ownersv2",
    "description": "Returns a random ownersv2 video from a predefined list of video URLs or local files",
    "path": "/ownersv2",
    "method": "GET"
}

# Predefined list of video sources (URLs or local file paths)
VIDEO_SOURCES = [
    "assets/videos/jujinciciprajiks.mp4",  # Local file path (relative to the project directory)
    "assets/videos/kaizenega.mp4",  # Local file path
]

async def on_start(request: Request):
    try:
        # Filter out empty strings and select a random video source
        valid_sources = [source for source in VIDEO_SOURCES if source]
        if not valid_sources:
            return {"error": "No valid video sources available."}
        
        selected_source = random.choice(valid_sources)
        
        # Check if the source is a local file
        if not selected_source.startswith(("http://", "https://")):
            file_path = Path(selected_source)
            if file_path.is_file():
                # Read local file
                with open(file_path, "rb") as file:
                    video_bytes = file.read()
                return Response(content=video_bytes, media_type="video/mp4")
            else:
                return {"error": f"Local video file not found: {selected_source}"}
        
        # Handle remote URL
        async with aiohttp.ClientSession() as session:
            async with session.get(selected_source) as response:
                if response.status != 200:
                    return {"error": f"Failed to fetch video: {response.status}"}
                
                video_bytes = await response.read()
                return Response(content=video_bytes, media_type="video/mp4")
                
    except Exception as e:
        return {"error": str(e)}