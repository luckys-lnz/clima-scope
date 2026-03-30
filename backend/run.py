import uvicorn
from app.core.config import settings
import os

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
