import streamlit as st

st.set_page_config(
    page_title="Route Optimization Platform",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title('🚚 Route Optimization Platform')
st.markdown('### Intelligent route planning and dispatch for field service operations')

st.divider()

# Introduction
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## Welcome to Your Route Optimization Solution

    This platform helps you:
    - **Plan** efficient routes for your technicians
    - **Optimize** routes using advanced algorithms (OR-Tools)
    - **Visualize** routes on interactive maps
    - **Dispatch** routes to field technicians
    - **Track** route completion and performance

    ### Getting Started

    1. **Set up your database** - Run the SQL schema in Supabase (see `docs/database_schema.sql`)
    2. **Add technicians** - Use the Admin page to add your field technicians
    3. **Add stops** - Use the Operations page to add service stops
    4. **Optimize routes** - Let the system create optimal routes
    5. **View and dispatch** - Review routes on the dashboard and dispatch to technicians
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

# Next steps
st.markdown('## Next Steps')

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### For First-Time Setup:
    1. Configure Supabase credentials (see sidebar)
    2. Run database schema SQL
    3. Add sample technicians and stops
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

# Configuration info in sidebar
with st.sidebar:
    st.header('Configuration')

    st.markdown("""
    **Supabase Setup**

    Set your credentials in:
    - `.env` file, or
    - `.streamlit/secrets.toml`

    ```toml
    [supabase]
    url = "your_url"
    key = "your_key"
    ```
    """)

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
st.caption('Route Optimization Platform v1.0 | Built with Streamlit + OR-Tools')
