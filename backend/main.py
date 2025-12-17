from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from database import get_client
from auth_utils import get_current_user, check_user_permission

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


@app.get("/org/me")
async def get_my_org(current_user: dict = Depends(get_current_user)):
    """Get the current user's organization"""
    try:
        print(f"[ORG/ME] Fetching org for user {current_user.get('id')}")
        admin_client = get_client(use_service_role=True)
        
        # Get user's profile to find org_id
        profile_response = admin_client.table("profiles").select("*").eq("id", current_user["id"]).execute()
        print(f"[ORG/ME] Profile query result: {len(profile_response.data) if profile_response.data else 0} profiles found")
        
        if not profile_response.data or len(profile_response.data) == 0:
            print(f"[ORG/ME] No profile found for user {current_user.get('id')}")
            # Try to create a default profile with a default org
            try:
                # Check if default-org exists, create if not
                default_org_response = admin_client.table("orgs").select("*").eq("org_slug", "default-org").execute()
                if not default_org_response.data or len(default_org_response.data) == 0:
                    # Create default org
                    new_org = admin_client.table("orgs").insert({"org_slug": "default-org"}).execute()
                    default_org_id = new_org.data[0]["org_id"] if new_org.data else None
                else:
                    default_org_id = default_org_response.data[0]["org_id"]
                
                # Create profile for user
                admin_client.table("profiles").insert({
                    "id": current_user["id"],
                    "org_id": default_org_id,
                    "is_activated": True,
                    "is_superuser": False
                }).execute()
                
                # Retry fetching profile
                profile_response = admin_client.table("profiles").select("*").eq("id", current_user["id"]).execute()
                print(f"[ORG/ME] Created profile and retried, found {len(profile_response.data) if profile_response.data else 0} profiles")
            except Exception as create_error:
                print(f"[ORG/ME] Error creating profile: {create_error}")
                return {
                    "status": "error",
                    "error": f"User profile not found and could not be created: {str(create_error)}"
                }
        
        if not profile_response.data or len(profile_response.data) == 0:
            return {
                "status": "error",
                "error": "User profile not found"
            }
        
        profile = profile_response.data[0]
        org_id = profile.get("org_id")
        print(f"[ORG/ME] User profile org_id: {org_id}")
        
        if not org_id:
            print(f"[ORG/ME] User has no org_id, assigning to default-org")
            # Assign user to default org
            try:
                default_org_response = admin_client.table("orgs").select("*").eq("org_slug", "default-org").execute()
                if not default_org_response.data or len(default_org_response.data) == 0:
                    new_org = admin_client.table("orgs").insert({"org_slug": "default-org"}).execute()
                    org_id = new_org.data[0]["org_id"] if new_org.data else None
                else:
                    org_id = default_org_response.data[0]["org_id"]
                
                # Update profile
                admin_client.table("profiles").update({"org_id": org_id}).eq("id", current_user["id"]).execute()
                print(f"[ORG/ME] Assigned user to org {org_id}")
            except Exception as assign_error:
                print(f"[ORG/ME] Error assigning org: {assign_error}")
                return {
                    "status": "error",
                    "error": f"User is not associated with any organization and could not be assigned: {str(assign_error)}"
                }
        
        # Get org details
        org_response = admin_client.table("orgs").select("*").eq("org_id", org_id).execute()
        print(f"[ORG/ME] Org query result: {len(org_response.data) if org_response.data else 0} orgs found")
        
        if not org_response.data or len(org_response.data) == 0:
            return {
                "status": "error",
                "error": f"Organization with id {org_id} not found"
            }
        
        org = org_response.data[0]
        
        # Get user count for this org
        users_response = admin_client.table("profiles").select("id", count="exact").eq("org_id", org_id).execute()
        user_count = users_response.count if hasattr(users_response, 'count') else len(users_response.data) if users_response.data else 0
        print(f"[ORG/ME] Found org {org.get('org_slug')} with {user_count} members")
        
        # Get superuser status from profiles table (not users table)
        # profiles.is_superuser is a boolean NOT NULL DEFAULT FALSE
        is_superuser = profile.get("is_superuser", False)
        # Ensure it's a boolean (handle None, string "true", etc.)
        if isinstance(is_superuser, bool):
            is_superuser_bool = is_superuser
        elif isinstance(is_superuser, str):
            is_superuser_bool = is_superuser.lower() in ('true', '1', 'yes')
        else:
            is_superuser_bool = bool(is_superuser)
        
        print(f"[ORG/ME] User is_superuser from profiles table: {is_superuser} (type: {type(is_superuser)}, converted: {is_superuser_bool})")
        
        return {
            "status": "success",
            "org": {
                **org,
                "user_count": user_count
            },
            "is_superuser": is_superuser_bool
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ORG/ME] Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching organization: {str(e)}"
        )


# Request models
class InviteRequest(BaseModel):
    email: EmailStr


# Frontend URL for redirects
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@app.post("/org/{org_slug}/invite")
async def invite_user(
    org_slug: str,
    invite_data: InviteRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Invite a user to an organization.
    Requires authentication and permission to invite to the org.
    """
    try:
        # Check user permission
        print(f"[INVITE] Checking permission for user {current_user.get('id')} on org {org_slug}")
        try:
            has_permission, org_id = await check_user_permission(current_user, org_slug)
            print(f"[INVITE] Permission check result: has_permission={has_permission}, org_id={org_id}")
        except Exception as perm_error:
            print(f"[INVITE] Permission check error: {perm_error}")
            raise HTTPException(
                status_code=500,
                detail=f"Error checking permissions: {str(perm_error)}"
            )
        
        if not has_permission:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to invite users to this organization"
            )
        
        if not org_id:
            raise HTTPException(
                status_code=404,
                detail="Organization not found"
            )
        
        # Get admin client to invite user
        admin_client = get_client(use_service_role=True)
        
        # Invite user via Supabase Admin API
        # Use REST API directly since Python client may not have invite method
        try:
            import requests
            
            supabase_url = os.getenv("SUPABASE_URL")
            service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            
            if not supabase_url or not service_role_key:
                raise HTTPException(
                    status_code=500,
                    detail="Supabase configuration missing. Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables."
                )
            
            # Call Supabase Admin API directly via REST
            invite_url = f"{supabase_url}/auth/v1/admin/users"
            
            headers = {
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json"
            }
            
            # Supabase Admin API payload for inviting users
            # Include org info in both user_metadata and app_metadata for reliability
            payload = {
                "email": invite_data.email,
                "user_metadata": {
                    "org_slug": org_slug,
                    "org_id": str(org_id),  # Convert to string for metadata
                    "invited_by": current_user["id"]
                },
                "app_metadata": {
                    "org_slug": org_slug,
                    "org_id": str(org_id),
                    "invited_by": current_user["id"]
                },
                "email_redirect_to": f"{FRONTEND_URL}/auth/accept-invite",
                "invite": True  # This triggers an invite email
            }
            
            print(f"[INVITE] Payload: email={invite_data.email}, org_slug={org_slug}, org_id={org_id}")
            
            print(f"Sending invite request to {invite_url} for email {invite_data.email}")
            # Add timeout to prevent hanging
            response = requests.post(invite_url, json=payload, headers=headers, timeout=30)
            print(f"Invite response status: {response.status_code}")
            
            if response.status_code not in [200, 201]:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get("message", response.text)
                
                if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                    raise HTTPException(
                        status_code=400,
                        detail="User with this email already exists"
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to send invite: {error_msg}"
                )
            
            invite_data_response = response.json()
            invited_user_id = invite_data_response.get("id")
            
        except HTTPException:
            raise
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Invite functionality requires 'requests' package. Please install it: pip install requests"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send invite: {str(e)}"
            )
        
        # Create or update profile entry
        if invited_user_id:
            try:
                # Check if profile exists
                profile_check = admin_client.table("profiles").select("*").eq("id", invited_user_id).execute()
                
                if not profile_check.data or len(profile_check.data) == 0:
                    # Create profile entry
                    admin_client.table("profiles").insert({
                        "id": invited_user_id,
                        "org_id": org_id,
                        "is_activated": False,
                        "is_superuser": False
                    }).execute()
                else:
                    # Update existing profile with org_id
                    admin_client.table("profiles").update({
                        "org_id": org_id,
                        "is_activated": False
                    }).eq("id", invited_user_id).execute()
            except Exception as e:
                print(f"Warning: Could not create/update profile: {e}")
                # Continue anyway - profile might be created later
        
        return {
            "status": "success",
            "message": f"Invitation sent to {invite_data.email}",
            "user_id": invited_user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error inviting user: {str(e)}"
        )


@app.post("/auth/accept")
async def accept_invite(
    current_user: dict = Depends(get_current_user)
):
    """
    Accept an invite and link user to organization.
    Called by frontend after user clicks invite link and signs in.
    """
    try:
        admin_client = get_client(use_service_role=True)
        
        # Get user metadata to find org info (check both user_metadata and app_metadata)
        user_metadata = current_user.get("user_metadata", {})
        org_slug = user_metadata.get("org_slug")
        org_id_str = user_metadata.get("org_id")
        
        # Convert org_id to int if it's a string
        org_id = None
        if org_id_str:
            try:
                org_id = int(org_id_str) if isinstance(org_id_str, str) else org_id_str
            except (ValueError, TypeError):
                pass
        
        if not org_id:
            # Try to get org_id from org_slug
            if org_slug:
                org_response = admin_client.table("orgs").select("org_id").eq("org_slug", org_slug).execute()
                if org_response.data and len(org_response.data) > 0:
                    org_id = org_response.data[0]["org_id"]
        
        if not org_id:
            raise HTTPException(
                status_code=400,
                detail="No organization found in invite. Please contact the person who invited you."
            )
        
        # Update profile to mark as activated and ensure org_id is set
        profile_response = admin_client.table("profiles").select("*").eq("id", current_user["id"]).execute()
        
        if not profile_response.data or len(profile_response.data) == 0:
            # Create profile
            admin_client.table("profiles").insert({
                "id": current_user["id"],
                "org_id": org_id,
                "is_activated": True,
                "is_superuser": False
            }).execute()
        else:
            # Update existing profile
            admin_client.table("profiles").update({
                "org_id": org_id,
                "is_activated": True
            }).eq("id", current_user["id"]).execute()
        
        return {
            "status": "success",
            "message": "Invite accepted successfully",
            "org_id": org_id,
            "org_slug": org_slug
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error accepting invite: {str(e)}"
        )

