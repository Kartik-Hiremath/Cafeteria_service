from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base
from . import models
from app.routes import auth, bookings, seats
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Cafeteria Reservation Service")

# Mount static files
static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(bookings.router)
app.include_router(seats.router)

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    """Serve the login page"""
    index_path = os.path.join(static_path, "index.html")
    return FileResponse(index_path)
