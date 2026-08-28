"""
supabase_auth.py - Supabase Authentication Backend Helper Module (Python)

Provides Python backend functions for signing in, signing up, verifying tokens,
and signing out users using Supabase.
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

try:
    from supabase import create_client, Client
    _supabase_client_available = True
except ImportError:
    _supabase_client_available = False


class SupabaseAuthManager:
    """Manager for handling Supabase user authentication in Python."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_ANON_KEY
        self.client: Optional[Any] = None

        if _supabase_client_available and self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
            except Exception as e:
                print(f"[SupabaseAuth] Warning initializing client: {e}")

    def is_configured(self) -> bool:
        return bool(self.client and self.url and self.key)

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in user with email and password."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized. Check your credentials."}

        try:
            res = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {
                "success": True,
                "user": {
                    "id": res.user.id,
                    "email": res.user.email,
                    "metadata": res.user.user_metadata,
                },
                "session": {
                    "access_token": res.session.access_token,
                    "refresh_token": res.session.refresh_token,
                    "expires_in": res.session.expires_in,
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sign_up(self, email: str, password: str, full_name: Optional[str] = None) -> Dict[str, Any]:
        """Register a new user in Supabase."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized."}

        try:
            data = {}
            if full_name:
                data["full_name"] = full_name

            res = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": data}
            })

            user_dict = {"id": res.user.id, "email": res.user.email} if res.user else None
            session_dict = {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
            } if res.session else None

            return {
                "success": True,
                "user": user_dict,
                "session": session_dict,
                "requires_email_confirmation": res.session is None
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def sign_out(self, access_token: str) -> Dict[str, Any]:
        """Sign out user session in Supabase."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized."}

        try:
            self.client.auth.sign_out(access_token)
            return {"success": True, "message": "Signed out successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_user(self, access_token: str) -> Dict[str, Any]:
        """Verify JWT access token and return current user details."""
        if not self.client:
            return {"success": False, "error": "Supabase client not initialized."}

        try:
            res = self.client.auth.get_user(access_token)
            if res.user:
                return {
                    "success": True,
                    "user": {
                        "id": res.user.id,
                        "email": res.user.email,
                        "metadata": res.user.user_metadata,
                        "last_sign_in": res.user.last_sign_in_at
                    }
                }
            return {"success": False, "error": "Invalid token or user not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
auth_manager = SupabaseAuthManager()
