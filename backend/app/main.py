from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.utils.logger import get_logger
from app.database.engine import init_db
from app.api import health, agents, diagnosis

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("app_startup", environment=settings.environment)
    init_db()
    logger.info("database_initialized")
    yield
    logger.info("app_shutdown")

# Create FastAPI app
app = FastAPI(
    title="AgriSense AI",
    description="Enterprise-grade agricultural disease diagnosis platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(agents.router)
app.include_router(diagnosis.router)

@app.get("/")
async def root():
    return {
        "name": "AgriSense AI",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
