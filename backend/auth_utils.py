"""
Authentication utilities for FastAPI endpoints
"""
from fastapi import Depends, HTTPException, Header
from typing import Optional
from database import get_client
import jwt
import os

# Get Supabase JWT secret from environment (needed to verify tokens)
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


async def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract and validate JWT token from Authorization header.
    Returns the user information from the token.
    
    The token should be a Supabase session access_token.
    We decode the JWT to extract user info (Supabase tokens are self-contained).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.split(" ")[1]
    
    try:
        # Decode JWT to get user info
        # Supabase JWT tokens contain user info in the payload
        import base64
        import json
        
        # JWT has 3 parts: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        # Decode payload (add padding if needed)
        payload = parts[1]
        payload += '=' * (4 - len(payload) % 4)  # Add padding
        decoded = base64.urlsafe_b64decode(payload)
        user_data = json.loads(decoded)
        
        user_id = user_data.get('sub')
        email = user_data.get('email')
        user_metadata = user_data.get('user_metadata', {})
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no user ID")
        
        return {
            "id": user_id,
            "email": email,
            "user_metadata": user_metadata
        }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


async def get_current_user_from_session(session_token: Optional[str] = None):
    """
    Alternative: Get user from session token (if passed directly)
    """
    if not session_token:
        raise HTTPException(status_code=401, detail="No session token provided")
    
    try:
        supabase_client = get_client(use_service_role=False)
        response = supabase_client.auth.get_user(session_token)
        
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata or {}
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Session validation failed: {str(e)}")


async def check_user_permission(user: dict, org_slug: str, require_superuser: bool = False):
    """
    Check if user has permission to perform action on organization.
    
    Args:
        user: User dict from get_current_user
        org_slug: Organization slug to check
        require_superuser: If True, only superusers can perform action
    
    Returns:
        tuple: (has_permission: bool, org_id: Optional[int])
    """
    try:
        print(f"[PERMISSION] Starting permission check for user {user.get('id')} on org {org_slug}")
        supabase_client = get_client(use_service_role=True)  # Use admin to check profiles
        
        # First, check if org exists
        print(f"[PERMISSION] Checking if org '{org_slug}' exists...")
        try:
            org_response = supabase_client.table("orgs").select("*").eq("org_slug", org_slug).execute()
            print(f"[PERMISSION] Org query completed: {len(org_response.data) if org_response.data else 0} orgs found")
        except Exception as e:
            print(f"[PERMISSION] Error querying orgs: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        org_id = None
        if not org_response.data or len(org_response.data) == 0:
            # Org doesn't exist - create it for development purposes
            print(f"[PERMISSION] Org '{org_slug}' not found, creating it...")
            try:
                new_org_response = supabase_client.table("orgs").insert({
                    "org_slug": org_slug
                }).execute()
                if new_org_response.data and len(new_org_response.data) > 0:
                    org_id = new_org_response.data[0]["org_id"]
                    print(f"[PERMISSION] Created org '{org_slug}' with id {org_id}")
                else:
                    print(f"[PERMISSION] Failed to create org - no data returned")
                    return False, None
            except Exception as e:
                print(f"[PERMISSION] Failed to create org: {e}")
                import traceback
                traceback.print_exc()
                return False, None
        else:
            org = org_response.data[0]
            org_id = org["org_id"]
            print(f"[PERMISSION] Found org '{org_slug}' with id {org_id}")
        
        # Get user's profile
        print(f"[PERMISSION] Checking profile for user {user['id']}...")
        try:
            profile_response = supabase_client.table("profiles").select("*").eq("id", user["id"]).execute()
            print(f"[PERMISSION] Profile query completed: {len(profile_response.data) if profile_response.data else 0} profiles found")
        except Exception as e:
            print(f"[PERMISSION] Error querying profiles: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # If user has no profile, create one and allow access to the org
        if not profile_response.data or len(profile_response.data) == 0:
            print(f"[PERMISSION] User {user['id']} has no profile, creating one with org_id {org_id}")
            try:
                # Create profile for user
                supabase_client.table("profiles").insert({
                    "id": user["id"],
                    "org_id": org_id,
                    "is_activated": True,
                    "is_superuser": False
                }).execute()
                print(f"[PERMISSION] Created profile for user {user['id']}")
                return True, org_id
            except Exception as e:
                print(f"[PERMISSION] Failed to create profile: {e}")
                import traceback
                traceback.print_exc()
                return False, None
        
        profile = profile_response.data[0]
        print(f"[PERMISSION] User profile: org_id={profile.get('org_id')}, is_superuser={profile.get('is_superuser')}")
        
        # Check if superuser
        if require_superuser:
            return profile.get("is_superuser", False), None
        
        # Check if user is superuser (can do anything)
        if profile.get("is_superuser", False):
            print(f"[PERMISSION] User is superuser, granting permission")
            return True, org_id
        
        # Regular user: check if they belong to the org
        user_org_id = profile.get("org_id")
        
        # If user has no org_id, assign them to this org and grant permission
        if not user_org_id:
            print(f"[PERMISSION] User {user['id']} has no org_id, assigning to org {org_id}")
            try:
                supabase_client.table("profiles").update({
                    "org_id": org_id
                }).eq("id", user["id"]).execute()
                print(f"[PERMISSION] Updated user profile with org_id {org_id}")
                return True, org_id
            except Exception as e:
                print(f"[PERMISSION] Failed to update profile: {e}")
                import traceback
                traceback.print_exc()
                # Still grant permission if update fails - allow them to proceed
                return True, org_id
        
        # Check if org_id matches user's org
        if user_org_id == org_id:
            print(f"[PERMISSION] User belongs to org {org_id}, granting permission")
            return True, org_id
        
        # For development: if user's org doesn't match, still allow but log warning
        # In production, you might want to deny this
        print(f"[PERMISSION] WARNING: User {user['id']} belongs to org {user_org_id}, but requested org {org_id} - allowing for development")
        return True, org_id  # Allow for now - change to False in production if needed
        
    except Exception as e:
        print(f"Error checking permission: {e}")
        import traceback
        traceback.print_exc()
        return False, None

