from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from .database import engine, Base
from .routers import auth, qrcodes, scan, analytics
from .config import get_settings
from .init_db import init_database

settings = get_settings()

# Create tables and seed admin
init_database()

app = FastAPI(title="QR Code Analytics API", version="1.0.0")

# CORS - allow frontend URLs
allowed_origins = [
    settings.frontend_url,
    "http://localhost:5173",
    "http://localhost:3000",
]
# Add any vercel preview URLs
if settings.frontend_url:
    # Allow all vercel preview deployments for the project
    allowed_origins.append("https://*.vercel.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
os.makedirs("uploads/logos", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(qrcodes.router)
app.include_router(scan.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "QR Code Analytics API", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy"}
