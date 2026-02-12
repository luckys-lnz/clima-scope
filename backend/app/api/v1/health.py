"""
Health Check Endpoint

Provides health status and system information.
"""

from fastapi import APIRouter
from datetime import datetime

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", tags=["health"])
async def health_check():
    """
    Health check endpoint using Supabase configuration.
    
    Returns the status of the API and Supabase services.
    """
    # API status - always healthy if this endpoint is reachable
    api_status = "healthy"
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    services = {
        "api": api_status,
        "timestamp": timestamp
    }
    
    # Check Supabase configuration
    if settings.SUPABASE_URL:
        services["supabase_url"] = "configured"
        
        # Check if we can connect to Supabase
        if settings.SUPABASE_SERVICE_KEY:
            try:
                from supabase import create_client, Client
                
                # Initialize client
                supabase: Client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                
                # Test auth service
                try:
                    # Just create client - if no error, auth is reachable
                    services["supabase_auth"] = "reachable"
                except Exception as e:
                    services["supabase_auth"] = f"error: {str(e)[:50]}"
                
                # Test database via a simple query
                try:
                    # Try to get count from profiles table (or any table)
                    response = supabase.table("profiles")\
                        .select("id", count="exact")\
                        .limit(1)\
                        .execute()
                    
                    if hasattr(response, 'count') or hasattr(response, 'data'):
                        services["supabase_database"] = "connected"
                    else:
                        services["supabase_database"] = "query_failed"
                        
                except Exception as e:
                    logger.warning("supabase_database_check_failed", error=str(e))
                    services["supabase_database"] = f"error: {str(e)[:50]}"
                
                # Test storage
                try:
                    buckets = supabase.storage.list_buckets()
                    if buckets:
                        services["supabase_storage"] = "available"
                    else:
                        services["supabase_storage"] = "no_buckets"
                except Exception as e:
                    logger.warning("supabase_storage_check_failed", error=str(e))
                    services["supabase_storage"] = f"error: {str(e)[:50]}"
                    
            except ImportError:
                services["supabase"] = "client_not_installed"
                services["supabase_database"] = "client_not_installed"
                services["supabase_storage"] = "client_not_installed"
            except Exception as e:
                logger.error("supabase_connection_failed", error=str(e))
                services["supabase"] = f"connection_error: {str(e)[:50]}"
        else:
            services["supabase"] = "service_key_missing"
    else:
        services["supabase"] = "not_configured"
    
    # Check OpenAI if configured
    if settings.OPENAI_API_KEY:
        services["openai"] = "configured"
    else:
        services["openai"] = "not_configured"
    
    # Overall status
    overall_status = "healthy"
    
    # Check if any critical service is down
    critical_services = ["supabase_database", "supabase_auth"]
    for service in critical_services:
        if service in services and "error" in services[service].lower():
            overall_status = "degraded"
            break
    
    return {
        "status": overall_status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": timestamp,
        "services": services
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers."""
    return {
        "status": "success",
        "message": "pong",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": settings.APP_NAME
    }


@router.get("/config")
async def show_config():
    """Show non-sensitive configuration (for debugging)."""
    return {
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
            "api_prefix": settings.API_V1_PREFIX,
        },
        "cors": {
            "origins": settings.cors_origins_list,
            "origins_raw": settings.CORS_ORIGINS
        },
        "supabase": {
            "url_configured": bool(settings.SUPABASE_URL),
            "service_key_configured": bool(settings.SUPABASE_SERVICE_KEY),
            "anon_key_configured": bool(settings.SUPABASE_ANON_KEY),
            "storage_bucket": settings.SUPABASE_STORAGE_BUCKET,
            "url_masked": mask_url(settings.SUPABASE_URL) if settings.SUPABASE_URL else None
        },
        "ai": {
            "provider": settings.AI_PROVIDER,
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "anthropic_configured": bool(settings.ANTHROPIC_API_KEY)
        },
        "storage": {
            "local_path": settings.STORAGE_PATH,
            "pdf_path": settings.PDF_STORAGE_PATH
        }
    }


def mask_url(url: str) -> str:
    """Mask sensitive parts of URLs."""
    if not url:
        return ""
    # Mask project ID in Supabase URL
    # https://abc123.supabase.co → https://***.supabase.co
    if "supabase.co" in url:
        parts = url.split(".")
        if len(parts) >= 3:
            parts[0] = "https://***"
        return ".".join(parts)
    return "***"
