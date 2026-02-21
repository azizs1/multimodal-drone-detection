from fastapi import APIRouter, HTTPException, status

from app.database.schemas import StreamInfo, StreamListResponse

router = APIRouter(
    prefix="/streams",
    tags=["streams"],
    responses={404: {"description": "Not found"}},
)

# Available stream configurations
STREAMS = {
    "drone": StreamInfo(
        name="drone",
        description="Main drone detection stream",
        rtsp_url="rtsp://mediamtx:8554/drone",
        hls_url="http://mediamtx:8888/drone/index.m3u8",
        status="active",
    )
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

    - **stream_name**: Name of the stream (e.g., "drone")

    Returns RTSP and HLS connection URLs and stream status.
    """
    if stream_name not in STREAMS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Stream '{stream_name}' not found"
        )
    return STREAMS[stream_name]
