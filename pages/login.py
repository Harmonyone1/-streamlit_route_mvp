"""
Login page for RouteFlow SaaS platform
Handles user authentication with email/password and Google SSO
"""

import streamlit as st
from utils.auth import login, init_session_state, is_authenticated
from utils.supabase_client import get_supabase_client

# Page configuration
st.set_page_config(
    page_title="Login - RouteFlow",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

# If already authenticated, redirect to operations
if is_authenticated():
    st.switch_page('pages/operations.py')

# Apply RouteFlow branding
st.markdown("""
<style>
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }

    /* Center content */
    .block-container {
        padding-top: 3rem;
        max-width: 500px;
    }

    /* Brand colors */
    :root {
        --brand-blue: #2563EB;
        --success-green: #10B981;
        --accent-orange: #F59E0B;
    }

    /* Login card styling */
    .login-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Button styling */
    .stButton > button {
        width: 100%;
        background-color: var(--brand-blue);
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem;
        font-weight: 600;
        font-size: 16px;
    }

    .stButton > button:hover {
        background-color: #1d4ed8;
    }

    /* Google SSO button */
    .google-btn {
        width: 100%;
        background-color: white;
        color: #333;
        border: 1px solid #ddd;
        border-radius: 6px;
        padding: 0.75rem;
        font-weight: 600;
        font-size: 16px;
        margin-top: 1rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
    }

    .google-btn:hover {
        background-color: #f8f9fa;
        border-color: #999;
    }
</style>
""", unsafe_allow_html=True)

# Header with logo and branding
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #2563EB; font-size: 2.5rem; margin-bottom: 0.5rem;">
        🚚 RouteFlow
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin: 0;">
        Smart Routes. Happy Customers. Growing Business.
    </p>
</div>
""", unsafe_allow_html=True)

# Login form
st.markdown('<div class="login-card">', unsafe_allow_html=True)

st.markdown("### Welcome Back")
st.markdown("Sign in to your account to continue")

# Display any error or success messages
if 'auth_message' in st.session_state:
    message = st.session_state.auth_message
    message_type = st.session_state.get('auth_message_type', 'info')

    if message_type == 'success':
        st.success(message)
    elif message_type == 'error':
        st.error(message)
    else:
        st.info(message)

    # Clear message after displaying
    del st.session_state.auth_message
    if 'auth_message_type' in st.session_state:
        del st.session_state.auth_message_type

# Email/Password login form
with st.form('login_form', clear_on_submit=False):
    email = st.text_input(
        'Email Address',
        placeholder='your.email@company.com',
        key='login_email'
    )

    password = st.text_input(
        'Password',
        type='password',
        placeholder='Enter your password',
        key='login_password'
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        remember_me = st.checkbox('Remember me', value=True)

    with col2:
        st.markdown(
            '<div style="text-align: right; padding-top: 0.5rem;">'
            '<a href="/password_reset" style="color: #2563EB; text-decoration: none; font-size: 0.9rem;">Forgot password?</a>'
            '</div>',
            unsafe_allow_html=True
        )

    submit_button = st.form_submit_button('Sign In', use_container_width=True)

    if submit_button:
        if not email or not password:
            st.error('⚠️ Please enter both email and password')
        else:
            with st.spinner('Signing in...'):
                success, message = login(email, password)

                if success:
                    st.success(f'✅ {message}')
                    st.balloons()

                    # Brief pause to show success message
                    import time
                    time.sleep(1)

                    # Redirect to operations page
                    st.switch_page('pages/operations.py')
                else:
                    st.error(f'❌ {message}')

st.markdown('</div>', unsafe_allow_html=True)

# Divider
st.markdown('<div style="text-align: center; margin: 1.5rem 0; color: #9CA3AF;">or</div>', unsafe_allow_html=True)

# Google SSO button (placeholder - will be implemented with Supabase Auth)
st.markdown("""
<button class="google-btn" onclick="alert('Google Sign-In will be implemented with Supabase Auth')">
    <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg">
        <g fill="none" fill-rule="evenodd">
            <path d="M17.6 9.2l-.1-1.8H9v3.4h4.8C13.6 12 13 13 12 13.6v2.2h3a8.8 8.8 0 0 0 2.6-6.6z" fill="#4285F4"/>
            <path d="M9 18c2.4 0 4.5-.8 6-2.2l-3-2.2a5.4 5.4 0 0 1-8-2.9H1V13a9 9 0 0 0 8 5z" fill="#34A853"/>
            <path d="M4 10.7a5.4 5.4 0 0 1 0-3.4V5H1a9 9 0 0 0 0 8l3-2.3z" fill="#FBBC05"/>
            <path d="M9 3.6c1.3 0 2.5.4 3.4 1.3L15 2.3A9 9 0 0 0 1 5l3 2.4a5.4 5.4 0 0 1 5-3.7z" fill="#EA4335"/>
        </g>
    </svg>
    Continue with Google
</button>
""", unsafe_allow_html=True)

st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)

# Sign up link
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #E5E7EB;">
    <p style="color: #6B7280; margin: 0;">
        Don't have an account?
        <a href="/register" style="color: #2563EB; text-decoration: none; font-weight: 600;">Start your free trial</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Trust indicators
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1.5rem; background: #F9FAFB; border-radius: 8px;">
    <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">
        ✅ 14-day free trial  •  🔒 Secure & encrypted  •  ❌ No credit card required
    </p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #E5E7EB;">
    <p style="color: #9CA3AF; font-size: 0.85rem;">
        © 2025 RouteFlow. All rights reserved.  •
        <a href="#" style="color: #9CA3AF;">Privacy Policy</a>  •
        <a href="#" style="color: #9CA3AF;">Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)
