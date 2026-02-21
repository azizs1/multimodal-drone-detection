from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routers import detections, health, streams
from app.database.database import Base, engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Drone Detection API",
    description="API for drone detection and tracking",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(detections.router)
app.include_router(streams.router)


# Redirect root to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")
