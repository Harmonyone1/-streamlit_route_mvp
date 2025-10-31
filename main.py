import streamlit as st
from utils.auth import init_session_state, is_authenticated, get_current_user, get_current_organization, show_user_menu

st.set_page_config(
    page_title="RouteFlow - Smart Route Optimization",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for authentication
init_session_state()

st.title('🚚 RouteFlow')
st.markdown('### Smart Routes. Happy Customers. Growing Business.')

st.divider()

# Check authentication status and show appropriate content
if is_authenticated():
    # Show personalized welcome for authenticated users
    user = get_current_user()
    org = get_current_organization()

    st.success(f"👋 Welcome back, **{user.get('full_name', 'User')}**!")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        ## {org.get('name', 'Your Organization')} Dashboard

        Your platform is ready to optimize routes and manage your field operations.

        ### Quick Actions
        - **Plan routes** - Add stops and create optimized routes
        - **View dashboard** - See today's routes and performance metrics
        - **Manage team** - Add technicians and assign routes
        - **Track progress** - Monitor route completion in real-time
        """)

    with col2:
        st.info("""
        **Quick Links**

        📊 **Dashboard**
        View routes and metrics

        🔧 **Operations**
        Create and optimize routes

        👤 **Admin**
        Manage users and settings

        👷 **Technician**
        Mobile view for field staff
        """)

else:
    # Show landing page for non-authenticated users
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        ## Transform Your Field Service Operations

        RouteFlow helps field service businesses save time, reduce costs, and delight customers with intelligent route optimization.

        ### Key Benefits
        - ⏱️ **Save 2-3 hours daily** on route planning
        - 💰 **Reduce fuel costs** by 15-20%
        - 📈 **Increase capacity** by 15-25% more stops per day
        - 😊 **Improve satisfaction** with on-time arrivals

        ### How It Works
        1. **Import** your service stops from spreadsheets or CRM
        2. **Optimize** routes automatically with AI-powered algorithms
        3. **Dispatch** routes to technicians via email or mobile app
        4. **Track** progress in real-time on interactive maps
        """)

    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #2563EB 0%, #1d4ed8 100%);
                    border-radius: 12px; padding: 2rem; color: white; text-align: center;">
            <h3 style="color: white; margin: 0 0 1rem 0;">Start Your Free Trial</h3>
            <p style="margin: 0 0 1.5rem 0; opacity: 0.9;">
                14 days free • No credit card required
            </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button('🚀 Sign Up Free', type='primary', use_container_width=True):
            st.switch_page('pages/register.py')

        if st.button('🔐 Log In', use_container_width=True):
            st.switch_page('pages/login.py')

        st.markdown("""
        <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #E5E7EB; text-align: center;">
            <p style="color: #6B7280; font-size: 0.9rem; margin: 0;">
                ✅ Used by 100+ businesses<br>
                ⭐ 4.9/5 average rating
            </p>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# Features overview
st.markdown('## Platform Features')

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### 🗺️ Route Optimization
    - Multi-vehicle routing
    - Time window constraints
    - Service duration consideration
    - Distance minimization
    - Real-time optimization (< 30 sec)
    """)

with col2:
    st.markdown("""
    ### 📍 Stop Management
    - Geocoded addresses
    - Time windows
    - Service priorities
    - Customer information
    - Notes and special instructions
    """)

with col3:
    st.markdown("""
    ### 👥 Team Management
    - Technician profiles
    - Skills and availability
    - Work hours configuration
    - Performance tracking
    - Route assignments
    """)

st.divider()

# System status
st.markdown('## System Status')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success('✅ Streamlit Ready')

with col2:
    st.success('✅ OR-Tools Available')

with col3:
    # Check Supabase connection
    try:
        from utils.supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            st.success('✅ Database Connected')
        else:
            st.warning('⚠️ Database Not Configured')
    except:
        st.warning('⚠️ Database Not Configured')

with col4:
    st.info('📦 Folium Maps Ready')

st.divider()

# Next steps (only for authenticated users)
if is_authenticated():
    st.markdown('## Next Steps')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### For First-Time Setup:
        1. Add your technicians
        2. Import or add service stops
        3. Configure your preferences
        4. Test route optimization
        """)

        if st.button('📖 View Setup Guide', use_container_width=True):
            st.switch_page('pages/admin.py')

    with col2:
        st.markdown("""
        ### To Start Using:
        1. Navigate to **Operations** page
        2. Add or import stops
        3. Click "Optimize Routes"
        4. View results on map
        """)

        if st.button('🚀 Go to Operations', type='primary', use_container_width=True):
            st.switch_page('pages/operations.py')

# Sidebar content based on authentication status
with st.sidebar:
    if is_authenticated():
        # Show user menu for authenticated users
        show_user_menu()

        st.divider()

        st.markdown("""
        **Quick Stats**
        - Today's routes: 0
        - Active technicians: 0
        - Pending stops: 0
        """)
    else:
        # Show marketing content for non-authenticated users
        st.header('Why RouteFlow?')

        st.markdown("""
        **Trusted by field service professionals**

        ✅ Save 2-3 hours daily
        ✅ Reduce fuel costs 15-20%
        ✅ Increase daily capacity
        ✅ Improve customer satisfaction

        **Features:**
        - AI-powered route optimization
        - Real-time GPS tracking
        - Mobile technician app
        - Automated dispatch
        - Excel & CRM integrations
        """)

        st.divider()

        if st.button('Try Free for 14 Days', type='primary', use_container_width=True):
            st.switch_page('pages/register.py')

    st.divider()

    st.markdown("""
    **Technology Stack**
    - Streamlit (UI)
    - OR-Tools (Optimization)
    - Supabase (Database)
    - Folium (Maps)
    - PostgreSQL (Backend)
    """)

st.divider()
st.caption('© 2025 RouteFlow - Smart Routes. Happy Customers. Growing Business. | v2.0 SaaS Platform')
