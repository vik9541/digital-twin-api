from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Viktor Digital Twin API",
    description="API for tracking project events, contacts sync, and monitoring system health",
    version="1.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routes.events import router as events_router
from api.routes.contacts import router as contacts_router

app.include_router(events_router)
app.include_router(contacts_router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Viktor Digital Twin API",
        "version": "1.1.0",
        "docs": "/docs",
        "endpoints": {
            "events": "/events",
            "contacts": "/contacts"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
