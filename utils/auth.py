"""
Authentication and authorization utilities for RouteFlow SaaS
Handles user sessions, roles, and permissions
"""

import streamlit as st
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets
from typing import Optional, Dict, List
from utils.supabase_client import get_supabase_client

# =============================================
# SESSION MANAGEMENT
# =============================================

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'organization' not in st.session_state:
        st.session_state.organization = None
    if 'role' not in st.session_state:
        st.session_state.role = None

def get_current_user() -> Optional[Dict]:
    """Get currently logged in user"""
    return st.session_state.get('user')

def get_current_organization() -> Optional[Dict]:
    """Get user's current organization"""
    return st.session_state.get('organization')

def get_user_role() -> Optional[str]:
    """Get user's role in current organization"""
    return st.session_state.get('role')

def is_authenticated() -> bool:
    """Check if user is authenticated"""
    return st.session_state.get('authenticated', False)

# =============================================
# AUTHENTICATION
# =============================================

def login(email: str, password: str) -> tuple[bool, str]:
    """
    Authenticate user with email and password

    Returns:
        (success: bool, message: str)
    """
    try:
        client = get_supabase_client()
        if not client:
            return False, "Database connection failed"

        # Use Supabase Auth to sign in
        response = client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            user_id = response.user.id

            # CRITICAL: Set the user's access token on the client
            # This makes subsequent requests use the authenticated role, not anon!
            if response.session and response.session.access_token:
                client.auth.set_session(response.session.access_token, response.session.refresh_token)
                print(f"Set user session token for authenticated requests")  # Debug log

            # Load user's organization and role
            org_data = client.table('organization_members')\
                .select('organization_id, role, organizations(*)')\
                .eq('user_id', user_id)\
                .eq('is_active', True)\
                .execute()

            if org_data.data and len(org_data.data) > 0:
                member = org_data.data[0]

                # Set session state
                st.session_state.authenticated = True
                st.session_state.user = {
                    'id': user_id,
                    'email': response.user.email,
                    'full_name': response.user.user_metadata.get('full_name', 'User')
                }
                st.session_state.organization = member['organizations']
                st.session_state.role = member['role']

                # Log event
                log_event('user_login', {'user_id': user_id})

                return True, "Login successful"
            else:
                # No organization found - create one for this user (backward compatibility)
                try:
                    import re
                    from datetime import datetime, timedelta

                    # Get user metadata
                    full_name = response.user.user_metadata.get('full_name', 'User')
                    company_name = response.user.user_metadata.get('company_name', f"{full_name}'s Company")

                    # Generate organization slug
                    slug_base = re.sub(r'[^a-z0-9]+', '-', email.split('@')[0].lower())
                    org_slug = f"{slug_base}-{user_id[:8]}"

                    # Create organization
                    org_response = client.table('organizations').insert({
                        'name': company_name,
                        'slug': org_slug,
                        'plan_tier': 'trial',
                        'subscription_status': 'trialing',
                        'trial_ends_at': (datetime.now() + timedelta(days=14)).isoformat(),
                        'is_active': True
                    }).execute()

                    if org_response.data and len(org_response.data) > 0:
                        org_id = org_response.data[0]['id']

                        # Create profile if doesn't exist
                        try:
                            client.table('profiles').insert({
                                'id': user_id,
                                'full_name': full_name,
                                'onboarding_completed': False
                            }).execute()
                        except:
                            pass  # Profile might already exist

                        # Create organization membership
                        client.table('organization_members').insert({
                            'organization_id': org_id,
                            'user_id': user_id,
                            'role': 'owner',
                            'is_active': True
                        }).execute()

                        # Set session state
                        st.session_state.authenticated = True
                        st.session_state.user = {
                            'id': user_id,
                            'email': response.user.email,
                            'full_name': full_name
                        }
                        st.session_state.organization = org_response.data[0]
                        st.session_state.role = 'owner'

                        return True, "Login successful! Organization created."

                except Exception as org_error:
                    return False, f"Organization setup incomplete. Please contact support. Error: {str(org_error)}"

                return False, "No organization found. Please contact support."

        return False, "Invalid credentials"

    except Exception as e:
        return False, f"Login error: {str(e)}"

def register(email: str, password: str, full_name: str, company_name: str) -> tuple[bool, str]:
    """
    Register new user and create organization

    Returns:
        (success: bool, message: str)
    """
    try:
        client = get_supabase_client()
        if not client:
            return False, "Database connection failed"

        # Create user with Supabase Auth
        # Note: Set email_confirm to False for development/testing to skip email verification
        # For production, remove this or set to True
        try:
            response = client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "company_name": company_name
                    },
                    # Uncomment the line below to skip email verification (DEVELOPMENT ONLY):
                    # "email_confirm": False
                }
            })
        except Exception as auth_error:
            error_msg = str(auth_error)
            print(f"Supabase Auth error: {error_msg}")  # Log for debugging

            # Check for common errors
            if "User already registered" in error_msg or "already registered" in error_msg.lower():
                return False, "This email is already registered. Please try logging in instead."
            elif "Invalid email" in error_msg:
                return False, "Invalid email address format."
            elif "password" in error_msg.lower():
                return False, "Password does not meet requirements (8+ characters, uppercase, lowercase, number)."
            else:
                return False, f"Registration error: {error_msg}"

        if response.user:
            user_id = response.user.id

            # CRITICAL FIX: Manually set Authorization header with JWT token
            # The client uses anon key by default, but we need to use the user's JWT for RLS
            if response.session and response.session.access_token:
                access_token = response.session.access_token
                print(f"Setting Authorization header for user {user_id}")  # Debug log

                # Set the authorization header on the postgrest client's session
                # This ensures all REST API calls use the authenticated role
                client.postgrest.auth(access_token)

                # Also update the default headers
                client.postgrest.session.headers['Authorization'] = f'Bearer {access_token}'
                print(f"Set Bearer token in Authorization header")  # Debug log

            # Manually create organization (don't rely on trigger)
            # Generate organization slug from email
            import re
            slug_base = re.sub(r'[^a-z0-9]+', '-', email.split('@')[0].lower())
            org_slug = f"{slug_base}-{user_id[:8]}"

            # Calculate trial end date (14 days from now)
            from datetime import datetime, timedelta
            trial_ends_at = (datetime.now() + timedelta(days=14)).isoformat()

            try:
                # Create organization using direct HTTP request to ensure proper auth headers
                print(f"Creating organization for user {user_id}: {company_name}")  # Debug log

                import httpx
                import os

                # Get Supabase URL
                if hasattr(st, 'secrets') and 'supabase' in st.secrets:
                    supabase_url = st.secrets['supabase']['url']
                    anon_key = st.secrets['supabase']['key']
                else:
                    supabase_url = os.environ.get('SUPABASE_URL', 'https://syrrhunexglfceovmdrd.supabase.co')
                    anon_key = os.environ.get('SUPABASE_KEY')

                # Make direct POST request with proper Authorization header
                headers = {
                    'apikey': anon_key,
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=representation'
                }

                org_data = {
                    'name': company_name,
                    'slug': org_slug,
                    'plan_tier': 'trial',
                    'subscription_status': 'trialing',
                    'trial_ends_at': trial_ends_at,
                    'is_active': True
                }

                response_http = httpx.post(
                    f"{supabase_url}/rest/v1/organizations",
                    headers=headers,
                    json=org_data,
                    timeout=30.0
                )

                print(f"HTTP Status: {response_http.status_code}")  # Debug log
                print(f"HTTP Response: {response_http.text[:200]}")  # Debug log

                if response_http.status_code in [200, 201]:
                    org_response_data = response_http.json()
                    if isinstance(org_response_data, list) and len(org_response_data) > 0:
                        org_id = org_response_data[0]['id']
                    elif isinstance(org_response_data, dict):
                        org_id = org_response_data['id']
                    else:
                        raise Exception(f"Unexpected response format: {org_response_data}")
                    print(f"Organization created with ID: {org_id}")  # Debug log

                    # Create profile using direct HTTP request
                    print(f"Creating profile for user {user_id}")  # Debug log
                    profile_response = httpx.post(
                        f"{supabase_url}/rest/v1/profiles",
                        headers=headers,
                        json={'id': user_id, 'full_name': full_name, 'onboarding_completed': False},
                        timeout=30.0
                    )
                    print(f"Profile HTTP Status: {profile_response.status_code}")  # Debug log

                    # Create organization membership with owner role using direct HTTP request
                    print(f"Creating organization membership")  # Debug log
                    membership_response = httpx.post(
                        f"{supabase_url}/rest/v1/organization_members",
                        headers=headers,
                        json={'organization_id': org_id, 'user_id': user_id, 'role': 'owner', 'is_active': True},
                        timeout=30.0
                    )
                    print(f"Membership HTTP Status: {membership_response.status_code}")  # Debug log

                    return True, "Registration successful! You can now login to your account."
                else:
                    print(f"Organization creation failed")  # Debug log
                    return False, f"Failed to create organization. Please contact support."

            except Exception as org_error:
                # IMPORTANT: If organization creation fails, user was still created in Supabase Auth
                # This creates an orphaned user account that can't login
                error_detail = str(org_error)
                print(f"Organization creation error: {error_detail}")  # Debug log

                # Check for specific RLS policy errors
                if 'policy' in error_detail.lower() or '42501' in error_detail:
                    return False, f"Database security error. Please verify RLS policies are configured. Error: {error_detail[:100]}"
                elif 'unique' in error_detail.lower() or 'duplicate' in error_detail.lower():
                    return False, f"Organization slug already exists. Please try again. Error: {error_detail[:100]}"
                else:
                    # Return detailed error for debugging
                    return False, f"Failed to create organization. Error: {error_detail[:200]}"

        return False, "Registration failed"

    except Exception as e:
        error_msg = str(e)
        if 'already registered' in error_msg.lower() or 'already exists' in error_msg.lower():
            return False, "This email is already registered. Please try logging in instead."
        return False, f"Registration error: {error_msg}"

def logout():
    """Logout current user"""
    try:
        client = get_supabase_client()
        if client:
            client.auth.sign_out()

        # Clear session state
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.organization = None
        st.session_state.role = None

        # Clear any other session data
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'user', 'organization', 'role']:
                del st.session_state[key]

    except Exception as e:
        print(f"Logout error: {str(e)}")

def reset_password(email: str) -> tuple[bool, str]:
    """
    Send password reset email

    Returns:
        (success: bool, message: str)
    """
    try:
        client = get_supabase_client()
        if not client:
            return False, "Database connection failed"

        client.auth.reset_password_for_email(email)

        return True, "Password reset email sent. Please check your inbox."

    except Exception as e:
        return False, f"Password reset error: {str(e)}"

# =============================================
# AUTHORIZATION & ROLES
# =============================================

# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'technician': 1,
    'manager': 2,
    'admin': 3,
    'owner': 4
}

def has_role(required_role: str) -> bool:
    """Check if user has at least the required role level"""
    user_role = get_user_role()
    if not user_role:
        return False

    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 999)

    return user_level >= required_level

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        init_session_state()
        if not is_authenticated():
            st.warning("⚠️ Please login to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_role(required_role: str):
    """Decorator to require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            init_session_state()
            if not is_authenticated():
                st.warning("⚠️ Please login to access this page")
                st.stop()
            if not has_role(required_role):
                st.error(f"🚫 Access denied. This page requires {required_role} role or higher.")
                st.stop()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_permission(action: str, resource: str = None) -> bool:
    """
    Check if user has permission for specific action

    Actions: create, read, update, delete
    Resources: stops, routes, technicians, team, billing, etc.
    """
    role = get_user_role()
    if not role:
        return False

    # Permission matrix
    permissions = {
        'owner': ['*'],  # All permissions
        'admin': [
            'create_stops', 'read_stops', 'update_stops', 'delete_stops',
            'create_routes', 'read_routes', 'update_routes', 'delete_routes',
            'create_technicians', 'read_technicians', 'update_technicians', 'delete_technicians',
            'read_team', 'create_team', 'update_team', 'delete_team',
            'read_analytics', 'dispatch', 'optimize'
        ],
        'manager': [
            'create_stops', 'read_stops', 'update_stops',
            'create_routes', 'read_routes', 'update_routes',
            'read_technicians',
            'read_analytics', 'dispatch', 'optimize'
        ],
        'technician': [
            'read_stops', 'read_routes', 'update_own_routes'
        ]
    }

    permission_key = f"{action}_{resource}" if resource else action

    # Owner has all permissions
    if role == 'owner':
        return True

    # Check if user's role has this permission
    return permission_key in permissions.get(role, [])

# =============================================
# ORGANIZATION MANAGEMENT
# =============================================

def get_organization_members() -> List[Dict]:
    """Get all members of current organization"""
    try:
        org = get_current_organization()
        if not org:
            return []

        client = get_supabase_client()
        if not client:
            return []

        members = client.table('organization_members')\
            .select('*, profiles(*)')\
            .eq('organization_id', org['id'])\
            .eq('is_active', True)\
            .execute()

        return members.data if members.data else []

    except Exception as e:
        print(f"Error fetching members: {str(e)}")
        return []

def invite_team_member(email: str, role: str) -> tuple[bool, str]:
    """
    Invite new team member to organization

    Returns:
        (success: bool, message: str)
    """
    try:
        if not has_role('admin'):
            return False, "Only admins can invite team members"

        org = get_current_organization()
        user = get_current_user()

        if not org or not user:
            return False, "Organization or user not found"

        client = get_supabase_client()
        if not client:
            return False, "Database connection failed"

        # Generate invitation token
        token = secrets.token_urlsafe(32)

        # Create invitation
        client.table('invitations').insert({
            'organization_id': org['id'],
            'email': email,
            'role': role,
            'token': token,
            'invited_by': user['id'],
            'expires_at': (datetime.now() + timedelta(days=7)).isoformat()
        }).execute()

        # TODO: Send invitation email with token
        # send_invitation_email(email, token, org['name'])

        return True, f"Invitation sent to {email}"

    except Exception as e:
        return False, f"Invitation error: {str(e)}"

# =============================================
# SUBSCRIPTION & USAGE
# =============================================

def get_subscription_status() -> Dict:
    """Get current organization's subscription status"""
    try:
        org = get_current_organization()
        if not org:
            return {}

        return {
            'plan_tier': org.get('plan_tier', 'trial'),
            'status': org.get('subscription_status', 'trialing'),
            'trial_ends_at': org.get('trial_ends_at'),
            'current_period_end': org.get('current_period_end'),
            'is_trial': org.get('plan_tier') == 'trial'
        }

    except Exception as e:
        print(f"Error fetching subscription: {str(e)}")
        return {}

def check_usage_limit(resource_type: str) -> tuple[bool, str]:
    """
    Check if organization is within usage limits

    resource_type: 'technicians', 'stops', 'routes'

    Returns:
        (within_limit: bool, message: str)
    """
    try:
        org = get_current_organization()
        if not org:
            return False, "No organization found"

        client = get_supabase_client()
        if not client:
            return False, "Database connection failed"

        plan = org.get('plan_tier', 'trial')

        # Get plan limits
        limits = client.table('plan_limits')\
            .select('*')\
            .eq('plan_tier', plan)\
            .execute()

        if not limits.data:
            return True, ""  # No limits for this plan

        limit_data = limits.data[0]

        # Check different resource types
        if resource_type == 'technicians':
            max_techs = limit_data.get('max_technicians')
            if max_techs is None:  # Unlimited
                return True, ""

            # Count current technicians
            count = client.table('technicians')\
                .select('id', count='exact')\
                .eq('organization_id', org['id'])\
                .eq('active', True)\
                .execute()

            current = len(count.data) if count.data else 0

            if current >= max_techs:
                return False, f"Technician limit reached ({current}/{max_techs}). Please upgrade your plan."

        elif resource_type == 'stops':
            max_stops = limit_data.get('max_stops_per_month')
            if max_stops is None:  # Unlimited
                return True, ""

            # Get current month usage
            current_month = datetime.now().strftime('%Y-%m-01')
            usage = client.table('usage_tracking')\
                .select('stops_created')\
                .eq('organization_id', org['id'])\
                .eq('month', current_month)\
                .execute()

            current = usage.data[0]['stops_created'] if usage.data else 0

            if current >= max_stops:
                return False, f"Monthly stop limit reached ({current}/{max_stops}). Resets next month or upgrade your plan."

        return True, ""

    except Exception as e:
        print(f"Error checking usage: {str(e)}")
        return True, ""  # Fail open to not block users

def increment_usage_counter(counter_type: str):
    """Increment usage counter for current organization"""
    try:
        org = get_current_organization()
        if not org:
            return

        client = get_supabase_client()
        if not client:
            return

        # Call the database function
        client.rpc('increment_usage', {
            'org_id': org['id'],
            'counter_name': counter_type,
            'increment_by': 1
        }).execute()

    except Exception as e:
        print(f"Error incrementing usage: {str(e)}")

# =============================================
# ANALYTICS & LOGGING
# =============================================

def log_event(event_type: str, event_data: Dict = None):
    """Log analytics event"""
    try:
        org = get_current_organization()
        user = get_current_user()

        client = get_supabase_client()
        if not client:
            return

        client.table('events').insert({
            'organization_id': org['id'] if org else None,
            'user_id': user['id'] if user else None,
            'event_type': event_type,
            'event_data': event_data or {}
        }).execute()

    except Exception as e:
        print(f"Error logging event: {str(e)}")

# =============================================
# UI COMPONENTS
# =============================================

def show_subscription_banner():
    """Show subscription status banner"""
    status = get_subscription_status()

    if status.get('is_trial'):
        trial_end = status.get('trial_ends_at')
        if trial_end:
            days_left = (datetime.fromisoformat(trial_end.replace('Z', '+00:00')) - datetime.now()).days
            if days_left <= 3:
                st.warning(f"⏰ Trial ends in {days_left} days. [Upgrade now](/billing) to continue using RouteFlow.")
            elif days_left <= 7:
                st.info(f"ℹ️ Trial ends in {days_left} days. Upgrade to unlock all features.")

    elif status.get('status') == 'past_due':
        st.error("⚠️ Payment failed. Please [update your payment method](/billing) to avoid service interruption.")

def show_user_menu():
    """Show user menu in sidebar"""
    init_session_state()

    if is_authenticated():
        user = get_current_user()
        org = get_current_organization()
        role = get_user_role()

        with st.sidebar:
            st.divider()

            st.write(f"**{user.get('full_name', 'User')}**")
            st.caption(f"{org.get('name', 'Organization')} • {role.title()}")

            if st.button("Logout", use_container_width=True):
                logout()
                st.rerun()
