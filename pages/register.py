"""
Registration page for RouteFlow SaaS platform
Handles new user signup with company creation
"""

import streamlit as st
from utils.auth import register, init_session_state, is_authenticated
import re

# Page configuration
st.set_page_config(
    page_title="Sign Up - RouteFlow",
    page_icon="🚀",
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
        padding-top: 2rem;
        max-width: 550px;
    }

    /* Brand colors */
    :root {
        --brand-blue: #2563EB;
        --success-green: #10B981;
        --accent-orange: #F59E0B;
    }

    /* Registration card styling */
    .register-card {
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

    /* Input field styling */
    .stTextInput > div > div > input {
        border-radius: 6px;
    }

    /* Benefit list styling */
    .benefit-item {
        display: flex;
        align-items: center;
        margin: 0.75rem 0;
        color: #374151;
    }

    .benefit-icon {
        color: #10B981;
        font-size: 1.2rem;
        margin-right: 0.75rem;
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
        Start your 14-day free trial
    </p>
    <p style="color: #9CA3AF; font-size: 0.95rem; margin: 0.5rem 0 0 0;">
        No credit card required  •  Cancel anytime
    </p>
</div>
""", unsafe_allow_html=True)

# Registration form
st.markdown('<div class="register-card">', unsafe_allow_html=True)

st.markdown("### Create Your Account")
st.markdown("Join hundreds of field service businesses optimizing their routes")

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

# Helper function to validate password strength
def check_password_strength(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"

# Registration form
with st.form('register_form', clear_on_submit=False):
    # Personal information
    st.markdown("**Your Information**")

    full_name = st.text_input(
        'Full Name *',
        placeholder='John Doe',
        key='register_name',
        help='Your first and last name'
    )

    email = st.text_input(
        'Work Email *',
        placeholder='john@yourcompany.com',
        key='register_email',
        help='Use your work email address'
    )

    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

    # Company information
    st.markdown("**Company Information**")

    company_name = st.text_input(
        'Company Name *',
        placeholder='Your Company Inc.',
        key='register_company',
        help='Your business or organization name'
    )

    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

    # Password
    st.markdown("**Security**")

    password = st.text_input(
        'Password *',
        type='password',
        placeholder='Create a strong password',
        key='register_password',
        help='Must be at least 8 characters with uppercase, lowercase, and numbers'
    )

    password_confirm = st.text_input(
        'Confirm Password *',
        type='password',
        placeholder='Re-enter your password',
        key='register_password_confirm'
    )

    # Show password strength indicator
    if password:
        is_strong, strength_message = check_password_strength(password)
        if is_strong:
            st.success(f'✅ {strength_message}')
        else:
            st.warning(f'⚠️ {strength_message}')

    st.markdown("<div style='margin: 1.5rem 0;'></div>", unsafe_allow_html=True)

    # Terms and conditions
    agree_terms = st.checkbox(
        'I agree to the Terms of Service and Privacy Policy',
        key='agree_terms'
    )

    # Marketing opt-in
    marketing_emails = st.checkbox(
        'Send me product updates and optimization tips (optional)',
        value=True,
        key='marketing_emails'
    )

    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)

    submit_button = st.form_submit_button('Start Free Trial', use_container_width=True)

    if submit_button:
        # Validation
        errors = []

        if not full_name or len(full_name.strip()) < 2:
            errors.append('Please enter your full name')

        if not email:
            errors.append('Email address is required')
        elif not is_valid_email(email):
            errors.append('Please enter a valid email address')

        if not company_name or len(company_name.strip()) < 2:
            errors.append('Company name is required')

        if not password:
            errors.append('Password is required')
        else:
            is_strong, strength_message = check_password_strength(password)
            if not is_strong:
                errors.append(strength_message)

        if password != password_confirm:
            errors.append('Passwords do not match')

        if not agree_terms:
            errors.append('You must agree to the Terms of Service')

        # Display errors
        if errors:
            for error in errors:
                st.error(f'❌ {error}')
        else:
            # Attempt registration
            with st.spinner('Creating your account...'):
                success, message = register(
                    email=email.strip(),
                    password=password,
                    full_name=full_name.strip(),
                    company_name=company_name.strip()
                )

                if success:
                    st.success(f'✅ {message}')
                    st.balloons()

                    # Show next steps
                    st.info("""
                    **Next Steps:**
                    1. Check your email for verification link
                    2. Click the link to verify your account
                    3. Return to login page to sign in
                    """)

                    # Provide login button
                    import time
                    time.sleep(2)

                    st.markdown("""
                    <div style="text-align: center; margin-top: 1rem;">
                        <a href="/login" style="
                            display: inline-block;
                            background-color: #2563EB;
                            color: white;
                            padding: 0.75rem 2rem;
                            border-radius: 6px;
                            text-decoration: none;
                            font-weight: 600;
                        ">Go to Login</a>
                    </div>
                    """, unsafe_allow_html=True)

                else:
                    st.error(f'❌ {message}')

                    # Provide helpful suggestions
                    if 'already' in message.lower():
                        st.info('This email is already registered. Try logging in instead.')
                        st.markdown("""
                        <div style="text-align: center; margin-top: 1rem;">
                            <a href="/login" style="color: #2563EB; text-decoration: none; font-weight: 600;">
                                Go to Login →
                            </a>
                        </div>
                        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Benefits section
st.markdown("""
<div style="background: #F9FAFB; border-radius: 12px; padding: 2rem; margin-top: 2rem;">
    <h4 style="color: #374151; margin-bottom: 1rem; text-align: center;">
        What You'll Get
    </h4>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>14-day free trial</strong> with full access to all features</span>
    </div>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>Save 2-3 hours daily</strong> on route planning</span>
    </div>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>Reduce fuel costs</strong> by 15-20%</span>
    </div>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>Increase capacity</strong> by 15-25% more stops per day</span>
    </div>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>Free support</strong> during trial period</span>
    </div>
    <div class="benefit-item">
        <span class="benefit-icon">✅</span>
        <span><strong>No credit card</strong> required to start</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Already have account link
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #E5E7EB;">
    <p style="color: #6B7280; margin: 0;">
        Already have an account?
        <a href="/login" style="color: #2563EB; text-decoration: none; font-weight: 600;">Sign in</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Trust badges
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1.5rem; background: white; border-radius: 8px; border: 1px solid #E5E7EB;">
    <p style="color: #6B7280; font-size: 0.9rem; margin: 0 0 0.75rem 0; font-weight: 600;">
        Trusted by field service businesses across North America
    </p>
    <p style="color: #9CA3AF; font-size: 0.85rem; margin: 0;">
        🔒 Bank-level encryption  •  🛡️ SOC 2 compliant  •  🔐 GDPR ready
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
