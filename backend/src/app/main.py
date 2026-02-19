from fastapi import FastAPI
from datetime import datetime
import os

app = FastAPI(title="Multimodal Drone Detection API")

# Available stream configurations
STREAMS = {
    "drone": {
        "name": "drone",
        "description": "Main drone detection stream",
        "rtsp_url": "rtsp://localhost:8554/drone",
        "hls_url": "http://localhost:8888/drone/index.m3u8",
        "hls_player": "http://localhost:8888/drone/",  # Built-in player
    }
}


@app.get("/")
async def root():
    return {
        "message": "Multimodal Drone Detection API",
        "version": "1.0.0",
        "endpoints": {
            "streams": "/streams",
            "stream_info": "/info/{stream_name}",
            "health": "/health"
        },
        "quick_links": {
            "watch_stream": "http://localhost:8888/drone/",
            "hls_url": "http://localhost:8888/drone/index.m3u8"
        }
    }


@app.get("/streams")
async def list_streams():
    """List all available streams"""
    return {
        "streams": list(STREAMS.values()),
        "count": len(STREAMS)
    }


@app.get("/info/{stream_name}")
async def get_stream(stream_name: str):
    """Get HLS and RTSP URLs for a specific stream"""
    if stream_name in STREAMS:
        return STREAMS[stream_name]
    return {
        "error": "Stream not found",
        "stream": stream_name,
        "available_streams": list(STREAMS.keys())
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mediamtx_rtsp": "mediamtx:8554",
        "mediamtx_hls": "mediamtx:8888"
    }
