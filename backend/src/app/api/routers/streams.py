import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.database.schemas import StreamInfo, StreamListResponse


def _resolve_hls_content_type(file_path: str, upstream_content_type: str | None) -> str:
    """Resolve HLS content type from upstream headers or file extension."""
    if upstream_content_type:
        return upstream_content_type.split(";", 1)[0].strip()

    lowered = file_path.lower()
    if lowered.endswith(".m3u8"):
        return "application/vnd.apple.mpegurl"
    if lowered.endswith(".ts"):
        return "video/mp2t"
    if lowered.endswith(".m4s"):
        return "video/iso.segment"

    return "application/octet-stream"


def _base_url(env_name: str, default: str) -> str:
    return os.getenv(env_name, default).rstrip("/")


def _int_env(env_name: str, default: int) -> int:
    raw_value = os.getenv(env_name)
    if raw_value is None:
        return default
    try:
        value = int(raw_value)
    except ValueError:
        logging.warning("Invalid integer for %s=%r; using %s", env_name, raw_value, default)
        return default
    return value if value > 0 else default


def _stream_info(
    stream_name: str,
    description: str,
    *,
    width: int,
    height: int,
    fps: int,
) -> StreamInfo:
    rtsp_base_url = _base_url("STREAM_RTSP_BASE_URL", "rtsp://mediamtx:8554")
    hls_base_url = _base_url("STREAM_HLS_BASE_URL", "http://mediamtx:8888")
    webrtc_base_url = _base_url("STREAM_WEBRTC_BASE_URL", "http://mediamtx:9998")
    return StreamInfo(
        name=stream_name,
        description=description,
        rtsp_url=f"{rtsp_base_url}/{stream_name}",
        hls_url=f"{hls_base_url}/{stream_name}/index.m3u8",
        webrtc_url=f"{webrtc_base_url}/{stream_name}/",
        width=width,
        height=height,
        fps=fps,
        status="active",
    )


router = APIRouter(
    prefix="/streams",
    tags=["streams"],
    responses={404: {"description": "Not found"}},
)

STREAM_CONFIG = {
    "thermal": {
        "description": "Thermal camera stream",
        "width_env": "THERMAL_STREAM_WIDTH",
        "height_env": "THERMAL_STREAM_HEIGHT",
        "fps_env": "THERMAL_STREAM_FPS",
        "default_width": 160,
        "default_height": 120,
        "default_fps": 15,
    },
    "visual": {
        "description": "Visual camera stream",
        "width_env": "VISUAL_STREAM_WIDTH",
        "height_env": "VISUAL_STREAM_HEIGHT",
        "fps_env": "VISUAL_STREAM_FPS",
        "default_width": 1280,
        "default_height": 720,
        "default_fps": 15,
    },
}


def _streams() -> dict[str, StreamInfo]:
    return {
        stream_name: _stream_info(
            stream_name,
            config["description"],
            width=_int_env(config["width_env"], config["default_width"]),
            height=_int_env(config["height_env"], config["default_height"]),
            fps=_int_env(config["fps_env"], config["default_fps"]),
        )
        for stream_name, config in STREAM_CONFIG.items()
    }


@router.get(
    "",
    response_model=StreamListResponse,
    summary="List all streams",
    description="Get a list of all available video streams",
)
async def list_streams() -> StreamListResponse:
    """
    List all configured video streams with their connection details.

    Returns information about RTSP and HLS URLs for each stream.
    """
    streams = _streams()
    return StreamListResponse(streams=list(streams.values()), total=len(streams))


@router.get(
    "/{stream_name}",
    response_model=StreamInfo,
    summary="Get stream information",
    description="Get detailed information about a specific stream",
)
async def get_stream_info(stream_name: str) -> StreamInfo:
    """
    Get detailed information about a specific video stream.

    - **stream_name**: Name of the stream (e.g. "thermal", "visual")

    Returns RTSP and HLS connection URLs and stream status.
    """
    streams = _streams()
    if stream_name not in streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Stream '{stream_name}' not found"
        )
    return streams[stream_name]


@router.get(
    "/{stream_name}/hls/{file_path:path}",
    summary="Get HLS stream",
    description="Get HLS playlist or segment files from MediaMTX",
)
async def get_hls(stream_name: str, file_path: str = "index.m3u8"):
    """
    Get HLS stream files from MediaMTX.

    - **stream_name**: Stream name (e.g., "thermal", "visual")
    - **file_path**: HLS file path (defaults to index.m3u8)

    Use in video player: http://localhost:8000/streams/thermal/hls/index.m3u8
    """
    if stream_name not in STREAM_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Stream '{stream_name}' not found"
        )

    hls_base_url = _base_url("STREAM_HLS_BASE_URL", "http://mediamtx:8888")
    mediamtx_url = f"{hls_base_url}/{stream_name}/{file_path}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(mediamtx_url, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Stream file not found"
                )

            content_type = _resolve_hls_content_type(
                file_path=file_path,
                upstream_content_type=response.headers.get("content-type"),
            )

            return StreamingResponse(
                response.iter_bytes(),
                media_type=content_type,
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                },
            )
    except httpx.RequestError as e:
        logging.error("MediaMTX error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to MediaMTX: {str(e)}",
        ) from None
