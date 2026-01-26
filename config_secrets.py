# config_secrets.py
# Centralized secrets management for Render and Streamlit Cloud

import os
import json
import streamlit as st


@st.cache_data
def get_secret(key_path, default=None):
    """
    Unified secret getter for Render and Streamlit Cloud.
    Cached to avoid repeated lookups.
    
    Args:
        key_path: Dot-notation path like "email.smtp_server" or "gcp.service_account_json"
        default: Fallback value if key not found
    
    Returns:
        Secret value from appropriate source
    """
    # Detect environment
    if os.getenv("RENDER"):
        # Running on Render - use environment variables
        return _get_render_secret(key_path, default)
    else:
        # Running on Streamlit Cloud - use st.secrets
        return _get_streamlit_secret(key_path, default)


def _get_render_secret(key_path, default):
    """Get secret from Render environment variables."""
    # Convert dot notation to ENV_VAR_STYLE
    # "email.smtp_server" -> "EMAIL_SMTP_SERVER"
    env_key = key_path.upper().replace(".", "_")
    value = os.getenv(env_key, default)
    
    # Special handling for JSON strings (like GCP service account)
    if key_path == "gcp.service_account_json" and value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    
    return value


def _get_streamlit_secret(key_path, default):
    """Get secret from Streamlit secrets.toml."""
    try:
        keys = key_path.split(".")
        value = st.secrets
        for key in keys:
            value = value[key]
        return value
    except (KeyError, AttributeError):
        return default


# Convenience functions for common secrets
@st.cache_data
def get_email_config():
    """Get email configuration dict. Cached for performance."""
    return {
        'smtp_server': get_secret('email.smtp_server'),
        'smtp_port': int(get_secret('email.smtp_port', 587)),
        'sender_email': get_secret('email.sender_email'),
        'sender_password': get_secret('email.sender_password'),
        'sender_name': 'Wilson Plant Co. HR',
        'company_email': get_secret('email.notify_email', 'info@wilsonnurseriesky.com')
    }


@st.cache_data
def get_gcp_service_account():
    """Get GCP service account as dict. Cached for performance."""
    sa = get_secret('gcp.service_account_json')
    if isinstance(sa, str):
        try:
            return json.loads(sa)
        except json.JSONDecodeError:
            return None
    return sa


@st.cache_data
def get_sheet_config():
    """Get Google Sheets configuration. Cached for performance."""
    return {
        'sheet_id': get_secret('gcp.sheet_id', '1QZ5gO5farg4E03dhaSINJljvn6qfocUgvHH4tjOSkIc'),
        'worksheet_name': get_secret('gcp.worksheet_name', '2026'),
        'pdf_folder_id': get_secret('gcp.pdf_folder_id', '1X5crtAwvuIgmgrGOSUR9M1gq21e0oUwh')
    }