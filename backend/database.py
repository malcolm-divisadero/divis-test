"""
Database configuration and connection utilities for Supabase
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Lazy-loaded client instances
_supabase_client: Optional[Client] = None
_supabase_admin_client: Optional[Client] = None


def get_supabase_client(use_service_role: bool = False) -> Client:
    """
    Create and return a Supabase client instance.
    
    Args:
        use_service_role: If True, uses service role key (bypasses RLS).
                         If False, uses anon key (respects RLS).
    
    Returns:
        Supabase client instance
    
    Raises:
        ValueError: If required environment variables are not set
    """
    if not SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is not set")
    
    key = SUPABASE_SERVICE_ROLE_KEY if use_service_role else SUPABASE_KEY
    if not key:
        key_name = "SUPABASE_SERVICE_ROLE_KEY" if use_service_role else "SUPABASE_KEY"
        raise ValueError(f"{key_name} environment variable is not set")
    
    return create_client(SUPABASE_URL, key)


def get_client(use_service_role: bool = False) -> Client:
    """
    Get or create a Supabase client instance (singleton pattern).
    
    Args:
        use_service_role: If True, uses service role key (bypasses RLS).
                         If False, uses anon key (respects RLS).
    
    Returns:
        Supabase client instance
    """
    global _supabase_client, _supabase_admin_client
    
    if use_service_role:
        if _supabase_admin_client is None:
            _supabase_admin_client = get_supabase_client(use_service_role=True)
        return _supabase_admin_client
    else:
        if _supabase_client is None:
            _supabase_client = get_supabase_client(use_service_role=False)
        return _supabase_client


# Convenience accessors (will raise error if env vars not set)
try:
    supabase: Client = get_client(use_service_role=False)
except ValueError:
    supabase = None  # Will be None if env vars not configured

try:
    supabase_admin: Client = get_client(use_service_role=True)
except ValueError:
    supabase_admin = None  # Will be None if env vars not configured

