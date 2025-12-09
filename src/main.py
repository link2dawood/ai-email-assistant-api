import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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
    # docs_url=f"{settings.api_prefix}/docs"  <-- REMOVE THIS LINE
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the main application router
app.include_router(api_router, prefix=settings.api_prefix)

if __name__ == "__main__":
    # Note: We run "src.main:app" because we are in the parent folder
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)