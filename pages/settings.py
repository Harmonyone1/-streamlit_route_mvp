"""
Organization Settings Page for RouteFlow
Manage organization settings, team members, and subscription
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client
from utils.auth import (
    init_session_state, is_authenticated, get_current_user,
    get_current_organization, has_role, get_organization_members,
    invite_team_member, get_subscription_status, show_user_menu,
    show_subscription_banner, get_user_role
)

st.set_page_config(
    page_title="Organization Settings - RouteFlow",
    page_icon="⚙️",
    layout="wide"
)

# Initialize session state for authentication
init_session_state()

# Check authentication
if not is_authenticated():
    st.warning("⚠️ Please login to access Settings")

    col1, col2 = st.columns(2)
    with col1:
        if st.button('🔐 Log In', type='primary', use_container_width=True):
            st.switch_page('pages/login.py')
    with col2:
        if st.button('🚀 Sign Up Free', use_container_width=True):
            st.switch_page('pages/register.py')

    st.stop()

# Check if user has admin permissions
if not has_role('admin'):
    st.error("🚫 Access denied. Settings requires Admin or Owner role.")
    st.info("Contact your organization owner to request admin access.")
    st.stop()

# Get current user and organization
user = get_current_user()
org = get_current_organization()
user_role = get_user_role()

st.title("⚙️ Organization Settings")
st.markdown(f"**{org.get('name', 'Organization')}** - Manage your account and team")

# Show subscription banner
show_subscription_banner()

st.divider()

# Sidebar
with st.sidebar:
    show_user_menu()

# Create tabs for different settings sections
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Organization",
    "👥 Team Members",
    "💳 Subscription & Billing",
    "📊 Usage & Limits"
])

# Initialize Supabase
client = get_supabase_client()

# =============================================
# TAB 1: ORGANIZATION SETTINGS
# =============================================
with tab1:
    st.header("Organization Settings")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Basic Information")

        with st.form("org_settings"):
            org_name = st.text_input(
                "Organization Name",
                value=org.get('name', ''),
                help="Your company or organization name"
            )

            org_industry = st.selectbox(
                "Industry",
                options=[
                    "HVAC",
                    "Plumbing",
                    "Electrical",
                    "General Contracting",
                    "Landscaping",
                    "Pest Control",
                    "Delivery Services",
                    "Healthcare (Home Health)",
                    "Other"
                ],
                index=0 if not org.get('industry') else None
            )

            st.markdown("**Business Address**")
            col_a, col_b = st.columns(2)
            with col_a:
                business_city = st.text_input("City", value="")
            with col_b:
                business_state = st.text_input("State", value="")

            col_c, col_d = st.columns(2)
            with col_c:
                business_zip = st.text_input("ZIP Code", value="")
            with col_d:
                business_phone = st.text_input("Phone", value="")

            st.markdown("**Work Hours (Default)**")
            col_e, col_f = st.columns(2)
            with col_e:
                work_start = st.time_input("Start Time", value=None)
            with col_f:
                work_end = st.time_input("End Time", value=None)

            submitted = st.form_submit_button("💾 Save Organization Settings", type="primary")

            if submitted:
                try:
                    if client:
                        # Update organization settings
                        settings = {
                            'industry': org_industry,
                            'business_city': business_city,
                            'business_state': business_state,
                            'business_zip': business_zip,
                            'business_phone': business_phone,
                            'work_start': str(work_start) if work_start else None,
                            'work_end': str(work_end) if work_end else None
                        }

                        client.table('organizations').update({
                            'name': org_name,
                            'industry': org_industry,
                            'settings': settings
                        }).eq('id', org['id']).execute()

                        st.success("✅ Organization settings saved successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Database connection failed")
                except Exception as e:
                    st.error(f"❌ Error saving settings: {str(e)}")

    with col2:
        st.subheader("Quick Info")

        st.info(f"""
        **Organization ID**
        `{org.get('id', 'N/A')}`

        **Created**
        {org.get('created_at', 'N/A')[:10] if org.get('created_at') else 'N/A'}

        **Your Role**
        {user_role.title()}
        """)

        st.divider()

        st.subheader("Danger Zone")

        with st.expander("⚠️ Advanced Actions", expanded=False):
            st.warning("""
            **Careful!** These actions cannot be undone.
            """)

            if user_role == 'owner':
                if st.button("🗑️ Delete Organization", use_container_width=True):
                    st.error("This feature will be available soon. Contact support to delete your organization.")
            else:
                st.info("Only the owner can delete the organization.")

# =============================================
# TAB 2: TEAM MEMBERS
# =============================================
with tab2:
    st.header("Team Members")

    # Show current team members
    members = get_organization_members()

    if members:
        st.success(f"👥 {len(members)} team member(s)")

        # Create DataFrame for display
        members_data = []
        for member in members:
            profile = member.get('profiles', {})
            members_data.append({
                'Name': profile.get('full_name', 'Unknown'),
                'Email': profile.get('email', 'N/A'),
                'Role': member.get('role', 'N/A').title(),
                'Joined': member.get('joined_at', 'N/A')[:10] if member.get('joined_at') else 'N/A',
                'Status': '✅ Active' if member.get('is_active') else '❌ Inactive'
            })

        df = pd.DataFrame(members_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No team members found.")

    st.divider()

    # Invite new team member
    st.subheader("Invite Team Member")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        Send an invitation to add a new team member to your organization.
        They'll receive an email with instructions to create their account.
        """)

        with st.form("invite_member"):
            invite_email = st.text_input(
                "Email Address *",
                placeholder="teammate@company.com",
                help="Enter the email address of the person you want to invite"
            )

            invite_role = st.selectbox(
                "Role *",
                options=['technician', 'manager', 'admin'],
                format_func=lambda x: {
                    'technician': '👷 Technician - View routes only',
                    'manager': '📊 Manager - Create and manage routes',
                    'admin': '⚙️ Admin - Full access except billing'
                }[x],
                help="Select the permission level for this team member"
            )

            col_a, col_b = st.columns([3, 1])
            with col_a:
                invite_message = st.text_area(
                    "Personal Message (optional)",
                    placeholder="Looking forward to having you on the team!",
                    height=100
                )

            submitted = st.form_submit_button("📧 Send Invitation", type="primary")

            if submitted:
                if not invite_email:
                    st.error("❌ Email address is required")
                else:
                    with st.spinner("Sending invitation..."):
                        success, message = invite_team_member(invite_email, invite_role)

                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")

    with col2:
        st.info("""
        **Role Permissions**

        **👷 Technician**
        - View assigned routes
        - Update stop status
        - Mobile access

        **📊 Manager**
        - All technician permissions
        - Create/edit routes
        - Manage stops
        - View analytics

        **⚙️ Admin**
        - All manager permissions
        - Manage team members
        - Organization settings
        - (No billing access)

        **👑 Owner**
        - Full access to everything
        - Billing & subscription
        - Delete organization
        """)

# =============================================
# TAB 3: SUBSCRIPTION & BILLING
# =============================================
with tab3:
    st.header("Subscription & Billing")

    subscription = get_subscription_status()

    col1, col2 = st.columns([2, 1])

    with col1:
        # Current plan
        st.subheader("Current Plan")

        plan_tier = subscription.get('plan_tier', 'trial')
        status = subscription.get('status', 'unknown')

        # Plan details
        plan_info = {
            'trial': {
                'name': 'Free Trial',
                'price': '$0',
                'color': '#10B981',
                'features': [
                    '5 technicians',
                    '500 stops/month',
                    '14-day trial period',
                    'Email support'
                ]
            },
            'starter': {
                'name': 'Starter',
                'price': '$49/month',
                'color': '#2563EB',
                'features': [
                    '5 technicians',
                    '500 stops/month',
                    'Google Sheets integration',
                    'Email support'
                ]
            },
            'professional': {
                'name': 'Professional',
                'price': '$149/month',
                'color': '#F59E0B',
                'features': [
                    '20 technicians',
                    '2,000 stops/month',
                    'All integrations',
                    'API access',
                    'Priority support'
                ]
            },
            'enterprise': {
                'name': 'Enterprise',
                'price': 'Custom',
                'color': '#8B5CF6',
                'features': [
                    'Unlimited technicians',
                    'Unlimited stops',
                    'White-label option',
                    'Dedicated support',
                    'Custom integrations'
                ]
            }
        }

        current_plan = plan_info.get(plan_tier, plan_info['trial'])

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {current_plan['color']} 0%, {current_plan['color']}dd 100%);
                    border-radius: 12px; padding: 2rem; color: white; margin: 1rem 0;">
            <h2 style="color: white; margin: 0 0 0.5rem 0;">{current_plan['name']}</h2>
            <h3 style="color: white; opacity: 0.9; margin: 0 0 1rem 0;">{current_plan['price']}</h3>
            <p style="margin: 0; opacity: 0.9;">Status: {status.title()}</p>
        </div>
        """, unsafe_allow_html=True)

        # Features
        st.markdown("**Plan Features:**")
        for feature in current_plan['features']:
            st.markdown(f"✅ {feature}")

        st.divider()

        # Upgrade/manage subscription
        if plan_tier == 'trial':
            st.subheader("Upgrade Your Plan")

            if subscription.get('trial_ends_at'):
                trial_end = datetime.fromisoformat(subscription['trial_ends_at'].replace('Z', '+00:00'))
                days_left = (trial_end - datetime.now()).days

                if days_left > 0:
                    st.warning(f"⏰ Your trial ends in {days_left} days")
                else:
                    st.error("❌ Your trial has expired")

            col_a, col_b, col_c = st.columns(3)

            with col_a:
                if st.button("Upgrade to Starter", use_container_width=True):
                    st.info("Stripe integration coming soon!")

            with col_b:
                if st.button("Upgrade to Professional", type="primary", use_container_width=True):
                    st.info("Stripe integration coming soon!")

            with col_c:
                if st.button("Contact for Enterprise", use_container_width=True):
                    st.info("Please contact sales@routeflow.com")
        else:
            st.subheader("Manage Subscription")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("📊 View Billing Portal", use_container_width=True):
                    st.info("Stripe Customer Portal integration coming soon!")

            with col_b:
                if st.button("⬆️ Upgrade Plan", use_container_width=True):
                    st.info("Plan upgrade coming soon!")

    with col2:
        st.subheader("Payment Method")

        st.info("""
        No payment method on file.

        Add a card to continue after trial.
        """)

        if st.button("💳 Add Payment Method", use_container_width=True):
            st.info("Stripe integration coming soon!")

        st.divider()

        st.subheader("Billing History")

        st.info("No invoices yet.")

        st.markdown("""
        Your invoices will appear here.
        """)

# =============================================
# TAB 4: USAGE & LIMITS
# =============================================
with tab4:
    st.header("Usage & Limits")

    st.markdown("""
    Track your usage against your plan limits. Usage resets on the first of each month.
    """)

    # Get current usage (placeholder - will be real data from database)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Technicians",
            "0 / 5",
            delta="Within limit",
            delta_color="normal"
        )
        st.progress(0.0)

    with col2:
        st.metric(
            "Stops This Month",
            "0 / 500",
            delta="Within limit",
            delta_color="normal"
        )
        st.progress(0.0)

    with col3:
        st.metric(
            "Routes Optimized",
            "0",
            delta="Unlimited",
            delta_color="off"
        )
        st.progress(0.0)

    st.divider()

    # Usage chart (placeholder)
    st.subheader("Usage Over Time")

    st.info("""
    📊 Usage analytics will be displayed here.

    Track your:
    - Daily stop count
    - Routes optimized per week
    - Technician utilization
    - Average route efficiency
    """)

    st.divider()

    # Recommendations
    st.subheader("💡 Recommendations")

    st.success("""
    **You're on track!**

    Your current usage is well within your plan limits. Keep up the great work!
    """)

st.divider()

# Footer
st.caption("Need help? Contact support at support@routeflow.com")
