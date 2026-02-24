import logging

import httpx
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.database.schemas import StreamInfo, StreamListResponse

router = APIRouter(
    prefix="/streams",
    tags=["streams"],
    responses={404: {"description": "Not found"}},
)

# Available stream configurations
STREAMS = {
    "thermal": StreamInfo(
        name="thermal",
        description="Thermal camera stream",
        rtsp_url="rtsp://mediamtx:8554/thermal",
        hls_url="http://mediamtx:8888/thermal/index.m3u8",
        status="active",
    ),
    "visual": StreamInfo(
        name="visual",
        description="Visual camera stream",
        rtsp_url="rtsp://mediamtx:8554/visual",
        hls_url="http://mediamtx:8888/visual/index.m3u8",
        status="active",
    ),
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
    return StreamListResponse(streams=list(STREAMS.values()), total=len(STREAMS))


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
    if stream_name not in STREAMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Stream '{stream_name}' not found"
        )
    return STREAMS[stream_name]


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
    if stream_name not in STREAMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Stream '{stream_name}' not found"
        )

    mediamtx_url = f"http://mediamtx:8888/{stream_name}/{file_path}"
    logging.info(f"Proxying HLS: {mediamtx_url}")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(mediamtx_url, timeout=10.0)

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Stream file not found"
                )

            content_type = (
                "application/vnd.apple.mpegurl" if file_path.endswith(".m3u8") else "video/mp2t"
            )

            return StreamingResponse(
                response.iter_bytes(),
                media_type=content_type,
                headers={
                    "Cache-Control": "no-cache",
                    "Access-Control-Allow-Origin": "*",
                },
            )
    except httpx.RequestError as e:
        logging.error(f"MediaMTX error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to connect to MediaMTX: {str(e)}",
        ) from None
