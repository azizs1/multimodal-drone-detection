"""Fusion HTTP service for Jetson runtime."""

from __future__ import annotations

import os

from fastapi import FastAPI

from ml.fusion.fusion_core import FusionEngine
from ml.fusion.transport_stub import build_router

app = FastAPI(title="Jetson Fusion Service")
app.include_router(build_router(FusionEngine()))


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def main() -> int:
    import uvicorn

    host = os.getenv("FUSION_HOST", "0.0.0.0")
    port = int(os.getenv("FUSION_PORT", "8050"))
    uvicorn.run("ml.fusion_service:app", host=host, port=port, reload=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
