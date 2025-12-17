from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from database import get_client

app = FastAPI(
    title="Divisadero API",
    description="API for Divisadero",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Divisadero API"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/health/db")
async def health_db():
    """Database health check endpoint"""
    try:
        supabase_client = get_client(use_service_role=False)
        # Test database connection by querying the profiles table
        response = supabase_client.table("profiles").select("count", count="exact").limit(0).execute()
        return {
            "status": "healthy",
            "database": "connected",
            "supabase": "operational",
            "profiles_count": response.count
        }
    except ValueError as e:
        # Environment variables not set
        return {
            "status": "unhealthy",
            "database": "not_configured",
            "error": "Supabase environment variables not set",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


@app.get("/profiles")
async def get_profiles():
    """Get profiles endpoint - for testing"""
    try:
        supabase_client = get_client(use_service_role=False)
        response = supabase_client.table("profiles").select("*").execute()
        return {
            "status": "success",
            "count": len(response.data) if response.data else 0,
            "profiles": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/brands")
async def get_brands():
    """Get all brands"""
    try:
        supabase_client = get_client(use_service_role=False)
        response = supabase_client.table("brands").select("*").order("name", desc=False).execute()
        return {
            "status": "success",
            "count": len(response.data) if response.data else 0,
            "brands": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@app.get("/brands/{slug}")
async def get_brand_by_slug(slug: str):
    """Get a specific brand by slug"""
    try:
        supabase_client = get_client(use_service_role=False)
        response = supabase_client.table("brands").select("*").eq("slug", slug).execute()
        
        if not response.data or len(response.data) == 0:
            return {
                "status": "error",
                "error": "Brand not found"
            }
        
        return {
            "status": "success",
            "brand": response.data[0]
        }
    except ValueError as e:
        # Environment variables not set
        return {
            "status": "error",
            "error": "Supabase environment variables not set",
            "message": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

