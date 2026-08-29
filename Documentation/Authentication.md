# Supabase Authentication Integration
## Technical Documentation & Security Architecture

---

# 1. Overview

The AI Medical Assistant platform utilizes **Supabase Authentication** to provide secure user registration, login, session management, and API authorization across both the Streamlit frontend and FastAPI backend.

Authentication is enforced using **JWT Bearer Tokens** issued by Supabase Auth. These tokens are stored within the Streamlit session state and attached to all protected API requests.

The integration ensures that:

- Only authenticated users can access application features.
- Backend endpoints are protected from unauthorized access.
- User identity is validated before executing AI inference or consultation workflows.
- Session state remains synchronized between frontend and backend components.

---

# 2. System Architecture

```text
+---------------------------------------------------------------------------------+
|                                Streamlit Frontend                               |
|                                  (frontend.py)                                  |
+---------------------------------------------------------------------------------+
                                         |
                       Calls render_auth_ui() from streamlit_auth.py
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                           Supabase Auth Session State                           |
|                                                                                 |
|  • User Registration                                                            |
|  • User Login                                                                   |
|  • Session Management                                                           |
|  • Access Token Storage                                                         |
|                                                                                 |
|  Stores JWT in:                                                                 |
|  st.session_state["access_token"]                                               |
+---------------------------------------------------------------------------------+
                                         |
                     Authorization: Bearer <access_token>
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                                 FastAPI Backend                                 |
|                                    (app.py)                                     |
+---------------------------------------------------------------------------------+
                                         |
                       Depends(get_current_user)
                           from fastapi_backend.py
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                           JWT Validation Layer                                  |
|                                                                                 |
|  • Signature Verification                                                       |
|  • Expiration Validation                                                        |
|  • Claims Validation                                                            |
|  • User Context Extraction                                                      |
|                                                                                 |
+---------------------------------------------------------------------------------+
                                         |
                                         v
+---------------------------------------------------------------------------------+
|                            Protected API Routes                                |
|                                                                                 |
|  • /predict/brain-mri                                                          |
|  • /predict/knee-xray                                                          |
|  • /consult                                                                    |
|  • /find-doctors                                                               |
+---------------------------------------------------------------------------------+
```

---

# 3. Core Components

---

## `streamlit_auth.py`

Responsible for frontend authentication workflows.

### Responsibilities

- User registration
- User login
- Session persistence
- Logout handling
- Access token management
- User metadata retrieval

### Session Storage

Authenticated sessions store the access token in:

```python
st.session_state["access_token"]
```

and user information in:

```python
st.session_state["user"]
```

### Returned Values

```python
is_authenticated, user = render_auth_ui()
```

| Variable | Description |
|-----------|-------------|
| is_authenticated | Boolean authentication status |
| user | Supabase user profile information |

---

## `fastapi_backend.py`

Provides backend authentication middleware and dependency injection.

### Primary Function

```python
get_current_user()
```

### Responsibilities

- Extract Bearer token
- Verify JWT signature
- Validate token expiration
- Validate token claims
- Extract authenticated user identity
- Reject unauthorized requests

### Security Layer

Uses:

```python
HTTPBearer
```

from FastAPI security utilities.

Example:

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()
```

---

## `app.py`

FastAPI backend service exposing protected endpoints.

### Protected Resources

- Brain MRI Classification
- Knee Osteoarthritis Grading
- Medical Consultation Engine
- Doctor Locator Service

Authentication is enforced through dependency injection.

---

## `frontend.py`

Primary Streamlit dashboard application.

Acts as an authentication gatekeeper before rendering application functionality.

Unauthenticated users cannot access:

- Upload interfaces
- AI predictions
- Medical consultation
- Doctor locator services

---

# 4. Authentication Flow

## User Registration

```text
User
  │
  ▼
Signup Form
  │
  ▼
Supabase Auth API
  │
  ▼
Account Created
  │
  ▼
User Logged In
```

---

## User Login

```text
User Credentials
        │
        ▼
Supabase Auth
        │
        ▼
Access JWT Token
        │
        ▼
Stored in Session State
        │
        ▼
Authenticated Session
```

---

## API Authorization Flow

```text
Streamlit Frontend
        │
        ▼
Bearer Token Attached
        │
        ▼
FastAPI Endpoint
        │
        ▼
get_current_user()
        │
        ▼
JWT Validation
        │
        ├── Invalid → 401 Unauthorized
        │
        └── Valid
                │
                ▼
Route Logic Executes
```

---

# 5. FastAPI Integration

## Dependency Injection Pattern

Protected endpoints require successful authentication before route execution.

### Example

```python
from fastapi import Depends
from fastapi_backend import get_current_user

@app.post(
    "/predict/brain-mri",
    response_model=BrainMRIPredictionResponse
)
async def predict_brain_mri(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    ...
```

### Execution Sequence

```text
Request Received
        │
        ▼
Extract Authorization Header
        │
        ▼
Verify JWT
        │
        ├── Fail → 401
        │
        └── Pass
                │
                ▼
Inject current_user
                │
                ▼
Execute Endpoint Logic
```

---

## Accessing User Context

Authenticated user information becomes available inside route handlers.

Example:

```python
@app.post("/consult")
async def consult(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["sub"]
```

Common claims include:

| Claim | Description |
|---------|-------------|
| sub | User ID |
| email | User email |
| role | User role |
| aud | Audience |
| exp | Expiration timestamp |

---

# 6. Streamlit Integration

## Authentication Gatekeeper

Authentication is verified before rendering any protected interface components.

### Example

```python
from streamlit_auth import render_auth_ui

def main():

    is_authenticated, user = render_auth_ui(
        location="sidebar"
    )

    if not is_authenticated:
        st.warning(
            "🔒 Please sign in or register an account in the sidebar to access the AI Medical Assistant."
        )
        st.stop()

    # Protected UI
```

---

## Session State Structure

Example:

```python
st.session_state = {
    "access_token": "...",
    "user": {
        "id": "...",
        "email": "user@example.com"
    }
}
```

---

## Sending Authenticated Requests

Frontend requests include the stored JWT token.

```python
headers = {
    "Authorization": f"Bearer {token}"
}
```

Example:

```python
response = requests.post(
    API_URL,
    headers=headers,
    files=files
)
```

---

# 7. Environment Configuration

Create a `.env` file accessible to both frontend and backend environments.

```env
# Supabase Configuration

SUPABASE_URL="https://your-project-id.supabase.co"
SUPABASE_KEY="your-supabase-anon-key"
SUPABASE_JWT_SECRET="your-supabase-jwt-secret"

# External AI Services

MISTRAL_API_KEY="your-mistral-api-key"
```

---

# 8. JWT Validation Process

The backend validates incoming tokens using either:

```text
SUPABASE_JWT_SECRET
```

or

```text
Supabase JWKS Endpoint
```

Validation steps:

```text
1. Extract Token
2. Verify Signature
3. Verify Issuer
4. Verify Audience
5. Verify Expiration
6. Decode Claims
7. Return User Context
```

---

# 9. Protected Endpoints

The following routes require authentication.

| Endpoint | Method | Authentication Required |
|-----------|----------|-------------------------|
| `/predict/brain-mri` | POST | Yes |
| `/predict/knee-xray` | POST | Yes |
| `/consult` | POST | Yes |
| `/find-doctors` | GET | Yes |

---

# 10. Error Handling

| Status Code | Cause | Resolution |
|-------------|---------|------------|
| 401 Unauthorized | Missing Authorization header | Include Bearer token |
| 401 Unauthorized | Invalid JWT signature | Login again |
| 401 Unauthorized | Expired token | Refresh session |
| 401 Unauthorized | Malformed token | Reauthenticate |
| 403 Forbidden | User lacks permissions | Verify account role |
| 500 Internal Server Error | Missing JWT secret | Configure environment variables |
| 500 Internal Server Error | Supabase unavailable | Retry request |

---

# 11. Security Best Practices

## Never Expose Secrets

Do not expose:

```env
SUPABASE_JWT_SECRET
```

to frontend applications.

Frontend should only receive:

```env
SUPABASE_URL
SUPABASE_KEY
```

---

## Use HTTPS

Production deployments should always enforce:

```text
HTTPS
```

for all authentication traffic.

---

## Token Expiration

Validate:

```text
exp
```

claim on every request.

Reject expired sessions immediately.

---

## Logout Handling

Clear all authentication state.

Example:

```python
st.session_state.clear()
```

or

```python
del st.session_state["access_token"]
```

---

# 12. Running the Application

## Start FastAPI Backend

```bash
uvicorn app:app --reload --port 8000
```

Backend URL:

```text
http://localhost:8000
```

API Documentation:

```text
http://localhost:8000/docs
```

---

## Start Streamlit Frontend

```bash
streamlit run frontend.py
```

Frontend URL:

```text
http://localhost:8501
```

---

# 13. Authentication Lifecycle

```text
User Registers
       │
       ▼
Supabase Account Created
       │
       ▼
User Logs In
       │
       ▼
JWT Access Token Issued
       │
       ▼
Stored in Session State
       │
       ▼
Attached to API Requests
       │
       ▼
FastAPI Validates Token
       │
       ▼
Authorized Resource Access
       │
       ▼
Logout / Token Expiry
       │
       ▼
Session Invalidated
```

---

# Version Information

| Component | Technology |
|------------|------------|
| Authentication Provider | Supabase Auth |
| Frontend | Streamlit |
| Backend | FastAPI |
| Security Scheme | JWT Bearer Token |
| Session Storage | Streamlit Session State |
| Token Validation | JWT Secret / JWKS |
| API Style | REST |
| Transport Security | HTTPS Recommended |

---