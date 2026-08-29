"""
fastapi_backend.py - FastAPI Authentication Backend with Supabase Integration

Demonstrates:
- Verification of Supabase Bearer JWT Tokens on protected endpoints.
- User registration, sign-in, and sign-out endpoints.
- Integration middleware for your FastAPI backend (app.py).
"""

import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status
from pydantic import BaseModel, EmailStr
from .supabase_auth import auth_manager

app = FastAPI(
    title="Medical Assistant API with Supabase Auth",
    description="Backend API featuring Sign In, Sign Out, and JWT Authentication via Supabase",
    version="1.0.0"
)

# Pydantic Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSignup(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


# JWT Verification Dependency for Protected Endpoints
async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header. Expected 'Bearer <JWT>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]
    res = auth_manager.get_user(token)

    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid session token: {res.get('error')}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return res["user"]


# API Routes

@app.get("/")
def read_root():
    return {"message": "Supabase Authentication API operational", "status": "active"}


@app.post("/api/auth/signup")
def signup(payload: UserSignup):
    """Register a new user in Supabase."""
    res = auth_manager.sign_up(payload.email, payload.password, full_name=payload.full_name)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res


@app.post("/api/auth/login")
def login(payload: UserLogin):
    """Authenticate user and return JWT access token."""
    res = auth_manager.sign_in(payload.email, payload.password)
    if not res.get("success"):
        raise HTTPException(status_code=401, detail=res.get("error"))
    return res


@app.post("/api/auth/logout")
def logout(user=Depends(get_current_user), authorization: str = Header(None)):
    """Sign out active user session in Supabase."""
    token = authorization.split(" ")[1]
    res = auth_manager.sign_out(token)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return {"message": "Signed out successfully", "user_id": user["id"]}


@app.get("/api/auth/me")
def get_user_profile(current_user=Depends(get_current_user)):
    """Protected endpoint returning active user profile."""
    return {"status": "authenticated", "user": current_user}


@app.get("/api/protected-consultation")
def protected_consultation(current_user=Depends(get_current_user)):
    """Sample protected API endpoint (Medical Consultation)."""
    return {
        "message": f"Hello {current_user['email']}, you have accessed a protected consultation endpoint!",
        "user_id": current_user["id"]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_backend:app", host="0.0.0.0", port=8000, reload=True)
