"""
This module implements Google OAuth 2.0 authentication for a Streamlit app.

It manages the full authentication flow using either a Google Cloud credentials file
or a base64-encoded secret loaded from `st.secrets`. The module handles secure login via
Google, including the exchange of authorization codes for tokens, and caches the credentials
locally for persistent sessions.

Upon successful login, the authenticated state is stored in both Streamlit's `st.session_state`
and the browser's local storage, ensuring the session persists across app refreshes.
A logout function is provided to clear the session state and stored credentials, effectively
resetting the user's authentication status.

This implementation also ensures the redirect callback is handled only once per session
to prevent multiple login prompts. Overall, the module provides a secure, user-friendly,
and seamless login experience.
"""


import json
from pathlib import Path
import base64
import streamlit as st
from googleapiclient.discovery import build
from streamlit_js import st_js, st_js_blocking
from google_auth_oauthlib.flow import Flow


# Function to retrieve data from local storage
def ls_get(k, key=None):
    if key is None:
        key = f"ls_get_{k}"
    return st_js_blocking(f"return JSON.parse(localStorage.getItem('{k}'));", key=key)

# Function to set data in local storage
def ls_set(k, v, key=None):
    if key is None:
        key = f"ls_set_{k}"
    jdata = json.dumps(v, ensure_ascii=False)
    st_js_blocking(f"localStorage.setItem('{k}', JSON.stringify({jdata}));", key=key)

# Initialize session with user info if it exists in local storage
def init_session():
    key = "user_info_init_session"
    if "user_info" not in st.session_state:
        user_info = ls_get("user_info", key=key)
        if user_info:
            st.session_state["user_info"] = user_info
    if "auth_code" not in st.session_state:
        st.session_state["auth_code"] = None
    if "credentials" not in st.session_state:
        st.session_state["credentials"] = None
    if "client_secret_uploaded" not in st.session_state:
        st.session_state.client_secret_uploaded = False
        
auth_cache_dir = Path(__file__).parent / "auth_cache"
client_secret_path = auth_cache_dir / "client_secret.json"
auth_status_path = auth_cache_dir / "auth_success.txt"
credentials_path = auth_cache_dir / "credentials.json"


scopes = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

def auth_flow():
    st.sidebar.title("Authentication")
    
    # Initialize with absolute paths
    auth_cache_dir = Path(__file__).parent / "auth_cache"
    auth_cache_dir.mkdir(parents=True, exist_ok=True)
    
    credentials_path = auth_cache_dir / "credentials.json"
    auth_status_path = auth_cache_dir / "auth_success.txt"

    if credentials_path.exists() and auth_status_path.exists():
        try:
            with open(credentials_path, "r") as f:
                credentials_json = json.load(f)

            
            # ✅ Ensure token is properly parsed (convert from string to dictionary)
            if isinstance(credentials_json.get("token"), str):
                try:
                    credentials_json["token"] = json.loads(credentials_json["token"])
                except json.JSONDecodeError:
                    st.error("Invalid token format in credentials.")
                    logout()
                    return None

            # Store credentials in session state (optional)
            st.session_state.credentials = credentials_json

            st.sidebar.success("Great! You're successfully logged in. Enjoy your session!")
            return credentials_json

        except (json.JSONDecodeError, ValueError) as e:
            st.error(f"Error loading credentials: {e}")
            logout()
            return None 
           
    try:
        client_secret_b64 = st.secrets.google_auth.client_secret_b64
        client_config = json.loads(base64.b64decode(client_secret_b64).decode())
    except Exception as e:
        st.error(f"🔒 Configuration error: {str(e)}")
        st.stop()
        
    # Handle OAuth Authentication
    redirect_uri = "https://hospitalpolicies-mwh7xj6f6vuyvnhqwqkob5.streamlit.app/"
    
    flow = Flow.from_client_config(client_config, scopes=scopes, redirect_uri=redirect_uri)
    auth_code = st.query_params.get("code")

    if auth_code:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials

        user_info_service = build("oauth2", "v2", credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()

        assert user_info.get("email"), "Email not found in response"

        # Save credentials persistently
        with open(credentials_path, "w") as f:
            json.dump({"email": user_info["email"], "token": credentials.to_json()}, f)

        # Mark authentication as successful
        auth_status_path.write_text("Authenticated")

        # Store credentials in session state
        st.session_state["credentials"] = {"email": user_info["email"], "token": credentials.to_json()}

        st.sidebar.success("✅ You’ve successfully logged in! Welcome aboard!")
        st.write("Hey there! Welcome back! Let’s generate some proposals together. 🚀")
        # Clear auth code from URL and refresh
        st.query_params.clear()
        st.rerun()
        return None

    else:
        authorization_url, state = flow.authorization_url(access_type="offline", prompt="consent")
        st.link_button("Sign in with Google", authorization_url)
        return None

def logout():
    """Completely clears all authentication artifacts"""
    
    # Remove authentication files
    if auth_status_path.exists():
        auth_status_path.unlink()
    if credentials_path.exists():
        credentials_path.unlink()

    # Ensure no residual credentials in session state
    if "credentials" in st.session_state:
        del st.session_state["credentials"]
    if "user_info" in st.session_state:
        del st.session_state["user_info"]
    st.session_state.pop("credentials", None)
    st.session_state.pop("auth_code", None)

    # Clear browser storage
    st.session_state.clear()  # Alternative to looping through keys
    st.query_params.update(logout="true")  # Force query param update
    st.sidebar.success("Logged out. Please sign in again.")

    # Force re-run
    st.rerun()
    
    
def validate_session():
    """Check for required auth state"""
    required_keys = [
        "credentials", 
        "drive_service",
        "docs_service",
        "authenticated_email"
    ]
    
    if any(key in st.session_state for key in required_keys):
        if not auth_status_path.exists():
            logout()