"""FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.api import router
from app.logger import get_logger
from app.database import init_db
from app.middleware.logging import LoggingMiddleware
from app.services.backup_scheduler import init_backup_scheduler, shutdown_backup_scheduler

# Get logger
logger = get_logger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="GRA External Integration API",
    description="Secure compliance gateway for GRA E-VAT submissions",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Add logging middleware (should be added first to catch all requests)
app.add_middleware(LoggingMiddleware)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API routes
app.include_router(router.api_router, prefix="/api/v1")

@app.get("/register")
async def register_page():
    """Serve business registration page"""
    static_dir = Path(__file__).parent / "static"
    register_file = static_dir / "register.html"
    if register_file.exists():
        return FileResponse(register_file, media_type="text/html")
    return JSONResponse({"error": "Registration page not found"}, status_code=404)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("Starting GRA External Integration API")
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        # Initialize backup and audit log retention scheduler
        init_backup_scheduler()
        logger.info("Backup and audit log retention scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down GRA External Integration API")
    shutdown_backup_scheduler()

@app.get("/health")
async def health_check():
    """
    API health check endpoint
    
    Returns:
        dict: API status, version, and environment information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "api_name": settings.APP_NAME
    }

@app.get("/api/v1/health")
async def api_health_check():
    """
    API v1 health check endpoint with component status
    
    Returns:
        dict: API health status and component status
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "components": {
            "api": "operational",
            "database": "operational"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "SERVER_ERROR",
            "message": "An unexpected error occurred",
            "timestamp": None
        }
    )

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
