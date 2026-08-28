# 🔐 Supabase Authentication System - Sign In & Sign Out

Complete, production-ready Authentication System powered by **Supabase Auth**.  
Includes **Web UI (HTML/CSS/JS)**, **Streamlit Component**, and **FastAPI Backend Middleware** for instant integration into the Medical Assistant application.

---

## 📁 Repository Overview

```
c:\Users\hp\OneDrive\Desktop\Authentication
├── index.html            # Luxury Web UI (Sign In, Sign Up, Reset Password, Dashboard)
├── styles.css            # Modern glassmorphism CSS styles & dynamic glow background
├── auth.js               # Supabase Web JS SDK Integration script
├── supabase_auth.py      # Core Python Supabase Authentication helper class
├── streamlit_auth.py     # Plug-and-Play Streamlit Sign In / Sign Out UI component
├── fastapi_backend.py    # FastAPI server with JWT authentication middleware & protected endpoints
├── .env.example          # Template for Supabase Project Keys
├── .env                  # Environment config file
└── requirements.txt      # Python dependencies
```

---

## 🚀 Step 1: Set Up Supabase Project (5 Minutes)

1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and name it (e.g. `medical-assistant-auth`).
3. Once created, navigate to **Project Settings** (gear icon) ➔ **API**.
4. Copy your credentials:
   - **Project URL**: `https://<your-project-ref>.supabase.co`
   - **API Key (anon / public)**: `eyJhbGci...`
5. Go to **Authentication** ➔ **Providers** ➔ Ensure **Email** is enabled.

---

## 🌐 Step 2: Running the Web UI Portal (`index.html`)

1. Open `auth.js` in a text editor.
2. Update the top lines with your credentials:
   ```javascript
   const SUPABASE_URL = "https://your-project-id.supabase.co";
   const SUPABASE_ANON_KEY = "your-supabase-anon-key";
   ```
3. Open `index.html` directly in any web browser!
4. Features available in Web UI:
   - 🔒 **Sign In** (Email + Password / Social Google & GitHub)
   - 📝 **Sign Up** (Email + Full Name)
   - 🔑 **Password Reset**
   - 🚪 **Sign Out** button on authenticated user dashboard
   - 📋 JWT Token Copy tool for API testing

---

## 🐍 Step 3: Integrating into Python Streamlit App (`frontend.py`)

To add Sign In & Sign Out to your friend's Streamlit frontend (`frontend.py`):

1. Copy `supabase_auth.py` and `streamlit_auth.py` into the application directory.
2. Add your credentials to your `.env` file:
   ```env
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key-here
   ```
3. At the top of `frontend.py`, add this snippet:
   ```python
   import streamlit as st
   from streamlit_auth import render_auth_ui

   st.set_page_config(page_title="Medical Assistant", page_icon="🩺")

   # Render Supabase Sign In / Sign Out UI
   is_authenticated, user = render_auth_ui(location="sidebar")

   if not is_authenticated:
       st.warning("Please sign in or create an account using the sidebar to access Medical Assistant.")
       st.stop()  # Stops execution here until user logs in

   # Rest of application logic (Consultation, Doctor Finder, etc.)...
   ```

---

## ⚡ Step 4: Integrating into FastAPI Backend (`app.py`)

To protect FastAPI API endpoints with Supabase JWT Tokens:

1. Import the dependency in `app.py`:
   ```python
   from fastapi import FastAPI, Depends
   from fastapi_backend import get_current_user

   app = FastAPI()

   @app.post("/consult")
   def consult(symptoms: str, current_user = Depends(get_current_user)):
       user_id = current_user["id"]
       user_email = current_user["email"]
       return {"advice": "Consultation results...", "user": user_email}
   ```

2. Clients pass the token in standard HTTP Authorization header:
   ```http
   Authorization: Bearer <access_token_jwt>
   ```

---

## 📦 Requirements & Installation

```bash
pip install -r requirements.txt
```

To test the FastAPI server locally:
```bash
python fastapi_backend.py
```
View interactive API docs at: `http://localhost:8000/docs`
