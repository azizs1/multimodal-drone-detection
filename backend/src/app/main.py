from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import detections, health, streams

# API metadata
app = FastAPI(
    title="Multimodal Drone Detection API",
    description="""
    ## Overview
    API for multimodal drone detection system integrating visual and thermal sensors.

    ## Features
    * 📹 **Video Stream Management** - Manage RTSP/HLS video streams
    * 🎯 **Detection Records** - Store and retrieve drone detection events
    * 📊 **Statistics** - Aggregate detection data and analytics
    * ❤️ **Health Checks** - Monitor service and database status

    ## Authentication
    Currently, this API does not require authentication. This will be added in future versions.

    ## Rate Limiting
    No rate limiting is currently enforced.
    """,
    version="1.0.0",
    contact={
        "name": "Drone Detection Team",
        "email": "support@dronedetection.example.com",
    },
    license_info={
        "name": "MIT",
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(streams.router)
app.include_router(detections.router)


@app.get(
    "/",
    tags=["root"],
    summary="API Root",
    description="Get basic API information and available endpoints",
)
async def root():
    """
    Welcome endpoint providing API information.

    Returns:
    - API name and version
    - Links to documentation
    - Available endpoint categories
    """
    return {
        "name": "Multimodal Drone Detection API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/health",
            "streams": "/streams",
            "detections": "/detections",
        },
    }
