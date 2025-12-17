from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Divisadero API",
    description="API for Divisadero",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Divisadero API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

