"""
FormatGuard — FastAPI Application Entry Point.
Sets up CORS, routers, exception handlers, and startup events.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.database import init_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
)

logger = structlog.get_logger()

# Initialize Sentry if DSN is configured
if settings.SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration(), SqlalchemyIntegration()],
            traces_sample_rate=0.1,
        )
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry initialization")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    logger.info("FormatGuard API starting up...")

    # Create tables in development (use Alembic migrations in production)
    await init_db()
    logger.info("Database tables initialized")

    # Seed pre-built rulesets
    try:
        from app.services.ruleset_service import seed_prebuilt_rulesets
        await seed_prebuilt_rulesets()
        logger.info("Pre-built rulesets seeded")
    except Exception as e:
        logger.warning("Failed to seed rulesets", error=str(e))

    yield

    logger.info("FormatGuard API shutting down...")


app = FastAPI(
    title="FormatGuard API",
    description="Document formatting compliance and auto-correction platform — 'The Turnitin for Formatting'",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Import and register routers
from app.routers import auth, submissions, rulesets, reports, corrections, admin

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(rulesets.router, prefix="/api/rulesets", tags=["Rulesets"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(corrections.router, prefix="/api/corrections", tags=["Corrections"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "FormatGuard API",
        "version": "1.0.0",
    }
