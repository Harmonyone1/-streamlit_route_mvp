"""
Password reset page for RouteFlow SaaS platform
Handles password reset email requests
"""

import streamlit as st
from utils.auth import reset_password, init_session_state
import re

# Page configuration
st.set_page_config(
    page_title="Reset Password - RouteFlow",
    page_icon="🔑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize session state
init_session_state()

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

    /* Reset card styling */
    .reset-card {
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
</style>
""", unsafe_allow_html=True)

# Header with logo and branding
st.markdown("""
<div style="text-align: center; margin-bottom: 2rem;">
    <h1 style="color: #2563EB; font-size: 2.5rem; margin-bottom: 0.5rem;">
        🚚 RouteFlow
    </h1>
    <p style="color: #6B7280; font-size: 1.1rem; margin: 0;">
        Reset Your Password
    </p>
</div>
""", unsafe_allow_html=True)

# Password reset form
st.markdown('<div class="reset-card">', unsafe_allow_html=True)

st.markdown("### Forgot Your Password?")
st.markdown("No worries! Enter your email and we'll send you a link to reset your password.")

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Check if email was already submitted
if 'reset_email_sent' not in st.session_state:
    st.session_state.reset_email_sent = False
    st.session_state.reset_email_address = None

# Show form or success message
if not st.session_state.reset_email_sent:
    with st.form('reset_form', clear_on_submit=False):
        email = st.text_input(
            'Email Address',
            placeholder='your.email@company.com',
            key='reset_email',
            help='Enter the email address associated with your account'
        )

        st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

        submit_button = st.form_submit_button('Send Reset Link', use_container_width=True)

        if submit_button:
            if not email:
                st.error('⚠️ Please enter your email address')
            elif not is_valid_email(email):
                st.error('⚠️ Please enter a valid email address')
            else:
                with st.spinner('Sending reset email...'):
                    success, message = reset_password(email)

                    if success:
                        st.session_state.reset_email_sent = True
                        st.session_state.reset_email_address = email
                        st.rerun()
                    else:
                        st.error(f'❌ {message}')
                        st.info('💡 If you continue having issues, please contact support.')

else:
    # Show success message
    st.success('✅ Password reset email sent!')

    st.markdown(f"""
    <div style="background: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 8px; padding: 1.5rem; margin: 1.5rem 0;">
        <p style="color: #0C4A6E; margin: 0 0 0.75rem 0;">
            <strong>Check your inbox!</strong>
        </p>
        <p style="color: #075985; margin: 0; font-size: 0.95rem;">
            We've sent a password reset link to:<br>
            <strong>{st.session_state.reset_email_address}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### What's next?

    1. **Check your email** - Look for an email from RouteFlow (check spam folder too)
    2. **Click the reset link** - The link is valid for 24 hours
    3. **Create a new password** - Choose a strong, unique password
    4. **Sign in** - Use your new password to access your account
    """)

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Buttons
    col1, col2 = st.columns(2)

    with col1:
        if st.button('Back to Login', use_container_width=True):
            st.session_state.reset_email_sent = False
            st.session_state.reset_email_address = None
            st.switch_page('pages/login.py')

    with col2:
        if st.button('Resend Email', use_container_width=True):
            with st.spinner('Resending...'):
                success, message = reset_password(st.session_state.reset_email_address)
                if success:
                    st.success('✅ Email sent again!')
                else:
                    st.error(f'❌ {message}')

    st.markdown("<div style='margin: 2rem 0;'></div>", unsafe_allow_html=True)

    # Support information
    st.markdown("""
    <div style="background: #F9FAFB; border-radius: 8px; padding: 1.5rem;">
        <p style="color: #374151; margin: 0 0 0.5rem 0; font-weight: 600;">
            Didn't receive the email?
        </p>
        <ul style="color: #6B7280; margin: 0; padding-left: 1.5rem;">
            <li>Check your spam or junk folder</li>
            <li>Make sure you entered the correct email</li>
            <li>Wait a few minutes for the email to arrive</li>
            <li>Contact support if you still need help</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Back to login link (only show if form is still visible)
if not st.session_state.reset_email_sent:
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #E5E7EB;">
        <p style="color: #6B7280; margin: 0;">
            Remember your password?
            <a href="/login" style="color: #2563EB; text-decoration: none; font-weight: 600;">Back to login</a>
        </p>
    </div>
    """, unsafe_allow_html=True)

# Security information
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1.5rem; background: #F9FAFB; border-radius: 8px;">
    <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">
        🔒 Password reset links are secure and expire after 24 hours for your protection
    </p>
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #E5E7EB;">
    <p style="color: #9CA3AF; font-size: 0.85rem;">
        © 2025 RouteFlow. All rights reserved.  •
        <a href="#" style="color: #9CA3AF;">Privacy Policy</a>  •
        <a href="#" style="color: #9CA3AF;">Terms of Service</a>  •
        <a href="#" style="color: #9CA3AF;">Support</a>
    </p>
</div>
""", unsafe_allow_html=True)
