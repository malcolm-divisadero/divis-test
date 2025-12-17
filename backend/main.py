from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from dotenv import load_dotenv
from database import get_client
from auth_utils import get_current_user, check_user_permission

# Load environment variables from .env file
load_dotenv()

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
        print(f"👤 [ORG/ME] Fetching org for user {current_user.get('id')}")
        # Check if service role key is available
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not service_role_key:
            raise HTTPException(
                status_code=500,
                detail="SUPABASE_SERVICE_ROLE_KEY environment variable is not set. Please check your backend .env file."
            )
        
        try:
            admin_client = get_client(use_service_role=True)
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize Supabase admin client: {str(e)}"
            )
        
        # Get user's profile to find org_id
        profile_response = admin_client.table("profiles").select("*").eq("id", current_user["id"]).execute()
        print(f"📊 [ORG/ME] Profile query result: {len(profile_response.data) if profile_response.data else 0} profiles found")
        
        if not profile_response.data or len(profile_response.data) == 0:
            print(f"⚠️  [ORG/ME] No profile found for user {current_user.get('id')}")
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
                print(f"✅ [ORG/ME] Created profile and retried, found {len(profile_response.data) if profile_response.data else 0} profiles")
            except Exception as create_error:
                print(f"❌ [ORG/ME] Error creating profile: {create_error}")
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
        print(f"📋 [ORG/ME] User profile org_id: {org_id}")
        
        if not org_id:
            print(f"🔄 [ORG/ME] User has no org_id, assigning to default-org")
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
                print(f"✅ [ORG/ME] Assigned user to org {org_id}")
            except Exception as assign_error:
                print(f"❌ [ORG/ME] Error assigning org: {assign_error}")
                return {
                    "status": "error",
                    "error": f"User is not associated with any organization and could not be assigned: {str(assign_error)}"
                }
        
        # Get org details
        org_response = admin_client.table("orgs").select("*").eq("org_id", org_id).execute()
        print(f"🏢 [ORG/ME] Org query result: {len(org_response.data) if org_response.data else 0} orgs found")
        
        if not org_response.data or len(org_response.data) == 0:
            return {
                "status": "error",
                "error": f"Organization with id {org_id} not found"
            }
        
        org = org_response.data[0]
        
        # Get user count for this org
        users_response = admin_client.table("profiles").select("id", count="exact").eq("org_id", org_id).execute()
        user_count = users_response.count if hasattr(users_response, 'count') else len(users_response.data) if users_response.data else 0
        print(f"✅ [ORG/ME] Found org {org.get('org_slug')} with {user_count} members")
        
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
        
        print(f"⭐ [ORG/ME] User is_superuser from profiles table: {is_superuser} (type: {type(is_superuser)}, converted: {is_superuser_bool})")
        
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
        print(f"❌ [ORG/ME] Error: {e}")
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
        print(f"🔐 [INVITE] Checking permission for user {current_user.get('id')} on org {org_slug}")
        try:
            has_permission, org_id = await check_user_permission(current_user, org_slug)
            print(f"✅ [INVITE] Permission check result: has_permission={has_permission}, org_id={org_id}")
        except Exception as perm_error:
            print(f"❌ [INVITE] Permission check error: {perm_error}")
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
            
            print(f"📧 [INVITE] Payload: email={invite_data.email}, org_slug={org_slug}, org_id={org_id}")
            print(f"📦 [INVITE] Full payload: {payload}")
            print(f"🚀 [INVITE] Sending invite request to {invite_url} for email {invite_data.email}")
            
            # Add timeout to prevent hanging
            response = requests.post(invite_url, json=payload, headers=headers, timeout=30)
            print(f"📡 [INVITE] Response status: {response.status_code}")
            print(f"📋 [INVITE] Response headers: {dict(response.headers)}")
            print(f"📄 [INVITE] Response text (first 500 chars): {response.text[:500]}")
            
            if response.status_code not in [200, 201]:
                try:
                    error_data = response.json()
                    print(f"❌ [INVITE] Error response JSON: {error_data}")
                    error_msg = error_data.get("message") or error_data.get("error") or response.text
                except:
                    error_msg = response.text
                    print(f"❌ [INVITE] Error response (non-JSON): {error_msg}")
                
                if "already registered" in str(error_msg).lower() or "already exists" in str(error_msg).lower():
                    raise HTTPException(
                        status_code=400,
                        detail="User with this email already exists"
                    )
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to send invite: {error_msg}"
                )
            
            try:
                invite_data_response = response.json()
                print(f"✅ [INVITE] Success response: {invite_data_response}")
                invited_user_id = invite_data_response.get("id")
                
                # Check if email was sent (Supabase may return confirmation)
                email_sent = False
                if "email" in invite_data_response:
                    print(f"👤 [INVITE] User created with email: {invite_data_response.get('email')}")
                
                if "confirmation_sent_at" in invite_data_response:
                    confirmation_time = invite_data_response.get("confirmation_sent_at")
                    print(f"📬 [INVITE] ✅ Confirmation email sent at: {confirmation_time}")
                    email_sent = True
                else:
                    print(f"⚠️  [INVITE] No 'confirmation_sent_at' field in response")
                
                if "invite_sent_at" in invite_data_response:
                    invite_time = invite_data_response.get("invite_sent_at")
                    print(f"📨 [INVITE] ✅ Invite email sent at: {invite_time}")
                    email_sent = True
                else:
                    print(f"⚠️  [INVITE] No 'invite_sent_at' field in response")
                
                if "last_sign_in_at" in invite_data_response:
                    print(f"🔐 [INVITE] Last sign in: {invite_data_response.get('last_sign_in_at')}")
                
                if not email_sent:
                    print(f"⚠️  [INVITE] ⚠️  WARNING: No email confirmation fields found in response!")
                    print(f"📧 [INVITE] Supabase didn't send email, using Resend API directly...")
                    
                    # Generate invite link from Supabase and send via Resend
                    try:
                        # Step 1: Generate invite link from Supabase
                        generate_link_url = f"{supabase_url}/auth/v1/admin/generate_link"
                        generate_link_payload = {
                            "type": "invite",
                            "email": invite_data.email,
                            "redirect_to": f"{FRONTEND_URL}/auth/accept-invite"
                        }
                        print(f"🔗 [INVITE] Generating invite link via Supabase...")
                        generate_response = requests.post(generate_link_url, json=generate_link_payload, headers=headers, timeout=30)
                        print(f"📡 [INVITE] Generate link response status: {generate_response.status_code}")
                        
                        if generate_response.status_code not in [200, 201]:
                            print(f"❌ [INVITE] Failed to generate link: {generate_response.text}")
                            raise Exception(f"Failed to generate invite link: {generate_response.text}")
                        
                        link_data = generate_response.json()
                        invite_link = None
                        
                        if "properties" in link_data and "action_link" in link_data.get("properties", {}):
                            invite_link = link_data["properties"]["action_link"]
                        elif "action_link" in link_data:
                            invite_link = link_data["action_link"]
                        elif "link" in link_data:
                            invite_link = link_data["link"]
                        
                        if not invite_link:
                            print(f"❌ [INVITE] No invite link found in response: {link_data}")
                            raise Exception("No invite link in Supabase response")
                        
                        print(f"✅ [INVITE] Invite link generated: {invite_link[:100]}...")
                        
                        # Step 2: Send email via Resend API
                        # Reload env vars to ensure we have the latest (load from backend directory)
                        from dotenv import load_dotenv
                        import pathlib
                        backend_dir = pathlib.Path(__file__).parent
                        env_path = backend_dir / ".env"
                        load_dotenv(dotenv_path=env_path)
                        print(f"📁 [INVITE] Loading .env from: {env_path}")
                        print(f"📁 [INVITE] .env file exists: {env_path.exists()}")
                        
                        resend_api_key = os.getenv("RESEND_API_KEY")
                        print(f"🔑 [INVITE] Checking RESEND_API_KEY: {'✅ Found' if resend_api_key else '❌ NOT FOUND'}")
                        if resend_api_key:
                            print(f"🔑 [INVITE] Key length: {len(resend_api_key)} chars, starts with: {resend_api_key[:10]}...")
                        if not resend_api_key:
                            print(f"⚠️  [INVITE] RESEND_API_KEY not found in environment variables")
                            print(f"💡 [INVITE] Resend API is optional. To enable email sending:")
                            print(f"💡 [INVITE]   1. Get API key from https://resend.com/api-keys")
                            print(f"💡 [INVITE]   2. Add RESEND_API_KEY=your_key to backend/.env")
                            print(f"💡 [INVITE]   3. Optionally set RESEND_FROM_EMAIL and RESEND_FROM_NAME")
                            print(f"💡 [INVITE] Alternative: Configure Supabase SMTP in Dashboard → Settings → Auth")
                            print(f"💡 [INVITE] Invite link generated: {invite_link}")
                            print(f"💡 [INVITE] You can manually send this link to {invite_data.email}")
                            # Don't raise exception - just skip Resend email sending
                            # The invite link will be returned in the response
                            raise Exception("RESEND_API_KEY_NOT_SET")  # Special exception to skip Resend
                        
                        # Get sender email from env or use a default
                        sender_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
                        sender_name = os.getenv("RESEND_FROM_NAME", "Divisadero")
                        
                        resend_url = "https://api.resend.com/emails"
                        resend_headers = {
                            "Authorization": f"Bearer {resend_api_key}",
                            "Content-Type": "application/json"
                        }
                        
                        email_subject = f"Invitation to join {org_slug}"
                        email_html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        </head>
                        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                            <div style="background: #f9fafb; border-radius: 8px; padding: 30px; text-align: center;">
                                <h1 style="color: #1a1a1a; margin-top: 0;">You've been invited!</h1>
                                <p style="font-size: 16px; color: #666; margin: 20px 0;">
                                    You've been invited to join <strong>{org_slug}</strong> on Divisadero.
                                </p>
                                <a href="{invite_link}" 
                                   style="display: inline-block; background: #3b82f6; color: #fff; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 600; margin: 20px 0;">
                                    Accept Invitation
                                </a>
                                <p style="font-size: 14px; color: #999; margin-top: 30px;">
                                    Or copy and paste this link into your browser:<br>
                                    <a href="{invite_link}" style="color: #3b82f6; word-break: break-all;">{invite_link}</a>
                                </p>
                                <p style="font-size: 12px; color: #999; margin-top: 30px;">
                                    This invitation link will expire in 7 days.
                                </p>
                            </div>
                        </body>
                        </html>
                        """
                        
                        resend_payload = {
                            "from": f"{sender_name} <{sender_email}>",
                            "to": [invite_data.email],
                            "subject": email_subject,
                            "html": email_html
                        }
                        
                        print(f"📧 [INVITE] Sending email via Resend API to {invite_data.email}...")
                        resend_response = requests.post(resend_url, json=resend_payload, headers=resend_headers, timeout=30)
                        print(f"📡 [INVITE] Resend API response status: {resend_response.status_code}")
                        print(f"📄 [INVITE] Resend API response: {resend_response.text[:500]}")
                        
                        if resend_response.status_code in [200, 201]:
                            resend_data = resend_response.json()
                            print(f"✅ [INVITE] ✅ Email sent successfully via Resend!")
                            print(f"📬 [INVITE] Resend email ID: {resend_data.get('id', 'N/A')}")
                            email_sent = True  # Mark as sent since we sent it via Resend
                        else:
                            error_msg = resend_response.text
                            print(f"❌ [INVITE] Resend API failed: {error_msg}")
                            raise Exception(f"Resend API error: {error_msg}")
                            
                    except Exception as resend_error:
                        print(f"❌ [INVITE] Error sending email via Resend: {resend_error}")
                        import traceback
                        traceback.print_exc()
                        # Don't fail the whole request - user is created, just email failed
                        print(f"⚠️  [INVITE] User created but email sending failed. Invite link: {invite_link if 'invite_link' in locals() else 'N/A'}")
                    
                    print(f"💡 [INVITE] Check Supabase Dashboard → Logs → Auth Logs for email status")
                    print(f"💡 [INVITE] Verify email templates are configured in Supabase Dashboard")
                    print(f"💡 [INVITE] Check SMTP/Resend configuration in Supabase Settings → Auth → SMTP Settings")
                    
            except Exception as parse_error:
                print(f"❌ [INVITE] Error parsing response JSON: {parse_error}")
                print(f"📄 [INVITE] Raw response: {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Unexpected response format from Supabase: {str(parse_error)}"
                )
            
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
                print(f"⚠️  [INVITE] Warning: Could not create/update profile: {e}")
                # Continue anyway - profile might be created later
        
        # Log success details
        print(f"✅ [INVITE] ✓ Invitation API call successful for {invite_data.email}")
        print(f"🆔 [INVITE] User ID: {invited_user_id}")
        # Note: email_sent status is logged above in the email sending section
        
        return {
            "status": "success",
            "message": f"Invitation sent to {invite_data.email}",
            "user_id": invited_user_id,
            "note": "Check Supabase Dashboard → Logs → Auth Logs to verify email delivery"
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

