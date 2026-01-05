import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

# ---------------------------------------------------------
# IMPORTANT: Imports must point to 'src', not 'app'
# ---------------------------------------------------------
from src.config import settings
from src.prisma import database
from src.app_module import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle startup and shutdown events
    """
    # Connect to Database on startup
    await database.connect_db()
    yield
    # Disconnect on shutdown
    await database.disconnect_db()

# In src/main.py

app = FastAPI(
    title="Email Assistant API",
    lifespan=lifespan,
    redirect_slashes=False  # Prevent automatic redirects that cause CORS issues
)

# CORS Middleware - Allow localhost and 127.0.0.1 with any port for development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",  # Allow localhost and 127.0.0.1 with any port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint - redirect to Swagger UI
@app.get("/")
async def root():
    """Redirect to Swagger UI documentation"""
    return RedirectResponse(url="/docs")

# Include the main application router
app.include_router(api_router, prefix=settings.api_prefix)

if __name__ == "__main__":
    # Note: We run "src.main:app" because we are in the parent folder
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)