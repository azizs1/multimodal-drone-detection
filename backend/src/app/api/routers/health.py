import time
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.database.schemas import (
    DatabaseHealthResponse,
    HealthCheckResponse,
    LivenessCheckResponse,
    ReadinessCheckResponse,
)

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get(
    "",
    response_model=HealthCheckResponse,
    summary="Basic health check",
    description="Check if the API is running",
)
async def health_check() -> HealthCheckResponse:
    """
    Basic health check endpoint.

    Returns the API status and current timestamp.
    """
    return HealthCheckResponse(status="healthy", timestamp=time.time())


@router.get(
    "/db",
    response_model=DatabaseHealthResponse,
    summary="Database health check",
    description="Check if the database connection is working",
)
async def database_health_check(db: Annotated[Session, Depends(get_db)]) -> DatabaseHealthResponse:
    """
    Check database connectivity and status.

    Tests the database connection by executing a simple query.
    Returns detailed information about database status.
    """
    try:
        # Execute a simple query to test connection
        result = db.execute(text("SELECT 1"))
        result.fetchone()

        # Get database version
        version_result = db.execute(text("SELECT version()"))
        version = version_result.fetchone()[0]

        # Check if detections table exists
        table_check = db.execute(
            text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'detections'
            )
        """)
        )
        table_exists = table_check.fetchone()[0]

        return DatabaseHealthResponse(
            status="healthy",
            database="connected",
            version=version.split()[0:2],  # PostgreSQL version
            detections_table_exists=table_exists,
            timestamp=time.time(),
        )
    except Exception as e:
        return DatabaseHealthResponse(
            status="unhealthy", database="disconnected", error=str(e), timestamp=time.time()
        )


@router.get(
    "/ready",
    response_model=ReadinessCheckResponse,
    summary="Readiness check",
    description="Check if the service is ready to accept requests",
)
async def readiness_check(db: Annotated[Session, Depends(get_db)]) -> ReadinessCheckResponse:
    """
    Kubernetes-style readiness probe.

    Checks if the service is ready to handle requests by verifying:
    - API is running
    - Database is connected
    - Required tables exist
    """
    try:
        # Check database
        db.execute(text("SELECT 1"))

        # Check if detections table exists
        table_check = db.execute(
            text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'detections'
            )
        """)
        )
        table_exists = table_check.fetchone()[0]

        if not table_exists:
            return ReadinessCheckResponse(
                status="not_ready", reason="detections table does not exist", timestamp=time.time()
            )

        return ReadinessCheckResponse(status="ready", timestamp=time.time())
    except Exception as e:
        return ReadinessCheckResponse(status="not_ready", reason=str(e), timestamp=time.time())


@router.get(
    "/live",
    response_model=LivenessCheckResponse,
    summary="Liveness check",
    description="Check if the service is alive",
)
async def liveness_check() -> LivenessCheckResponse:
    """
    Kubernetes-style liveness probe.

    Simple check to verify the service is running.
    """
    return LivenessCheckResponse(status="alive", timestamp=str(time.time()))
