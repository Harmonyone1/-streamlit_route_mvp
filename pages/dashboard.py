import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date, timedelta, datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client, get_routes_by_date

st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

st.title('📊 Route Optimization Dashboard')
st.markdown('Real-time overview of routes, technicians, and operational metrics')

# Initialize Supabase client
client = get_supabase_client()

# Date selector in sidebar
with st.sidebar:
    st.header('Dashboard Controls')
    selected_date = st.date_input('View Date', value=date.today())

    st.divider()

    # Quick stats preferences
    st.subheader('Display Options')
    show_map_preview = st.checkbox('Show Map Preview', value=False)
    show_details = st.checkbox('Show Route Details', value=True)

    st.divider()

    # Date range selector for analytics
    st.subheader('Analytics Period')
    days_back = st.slider('Days to analyze', 1, 30, 7)

st.divider()

# Main dashboard content
if not client:
    st.error('Unable to connect to Supabase. Please check your configuration.')
    st.info('Configure your Supabase credentials in environment variables or Streamlit secrets.')
    st.code("""
# Add to .env file:
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Or add to .streamlit/secrets.toml:
[supabase]
url = "your_supabase_url"
key = "your_supabase_key"
    """)
else:
    # Fetch routes for selected date
    routes = get_routes_by_date(client, str(selected_date))

    # Top-level metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_routes = len(routes) if routes else 0
        st.metric('Total Routes', total_routes)

    with col2:
        completed_routes = len([r for r in routes if r.get('status') == 'completed']) if routes else 0
        st.metric('Completed', completed_routes)

    with col3:
        in_progress = len([r for r in routes if r.get('status') == 'in_progress']) if routes else 0
        st.metric('In Progress', in_progress)

    with col4:
        pending = len([r for r in routes if r.get('status') in ['draft', 'optimized', 'dispatched']]) if routes else 0
        st.metric('Pending', pending)

    st.divider()

    # Routes overview
    if routes and len(routes) > 0:
        st.subheader(f'Routes for {selected_date.strftime("%B %d, %Y")}')

        # Create routes dataframe
        routes_data = []
        for route in routes:
            tech_name = route.get('technician', {}).get('name', 'Unassigned') if route.get('technician') else 'Unassigned'

            routes_data.append({
                'Route Name': route.get('name', 'Unnamed Route'),
                'Technician': tech_name,
                'Status': route.get('status', 'draft').upper(),
                'Total Distance': f"{route.get('total_distance', 0):.1f} mi" if route.get('total_distance') else 'N/A',
                'Total Time': f"{route.get('total_duration', 0)} min" if route.get('total_duration') else 'N/A',
                'Created': route.get('created_at', 'N/A')[:10] if route.get('created_at') else 'N/A'
            })

        df_routes = pd.DataFrame(routes_data)

        # Display with status color coding
        st.dataframe(
            df_routes,
            use_container_width=True,
            hide_index=True
        )

        # Show detailed route information if enabled
        if show_details:
            st.divider()
            st.subheader('Route Details')

            for idx, route in enumerate(routes, 1):
                tech_name = route.get('technician', {}).get('name', 'Unassigned') if route.get('technician') else 'Unassigned'
                status = route.get('status', 'draft')

                # Status indicator
                status_colors = {
                    'draft': '🟡',
                    'optimized': '🔵',
                    'dispatched': '🟣',
                    'in_progress': '🟠',
                    'completed': '🟢',
                    'cancelled': '🔴'
                }
                status_icon = status_colors.get(status, '⚪')

                with st.expander(f"{status_icon} Route {idx}: {route.get('name', 'Unnamed')} - {tech_name}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write('**Technician:**', tech_name)
                        st.write('**Status:**', status.upper())

                    with col2:
                        st.write('**Distance:**', f"{route.get('total_distance', 0):.1f} mi" if route.get('total_distance') else 'N/A')
                        st.write('**Duration:**', f"{route.get('total_duration', 0)} min" if route.get('total_duration') else 'N/A')

                    with col3:
                        st.write('**Start:**', route.get('start_location', 'N/A'))
                        st.write('**End:**', route.get('end_location', 'N/A'))

                    # Additional info
                    if route.get('optimization_score'):
                        st.progress(float(route['optimization_score']) / 100, text=f"Efficiency Score: {route['optimization_score']}%")

    else:
        st.info(f'No routes found for {selected_date.strftime("%B %d, %Y")}')
        st.markdown('Go to the **Operations** page to create and optimize routes.')

    # Analytics section
    st.divider()
    st.subheader('📈 Recent Activity')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Quick Actions')
        if st.button('➕ Create New Route', use_container_width=True):
            st.switch_page('pages/operations.py')

        if st.button('👥 Manage Technicians', use_container_width=True):
            st.switch_page('pages/admin.py')

        if st.button('📍 Manage Stops', use_container_width=True):
            st.switch_page('pages/operations.py')

    with col2:
        st.markdown('### System Status')
        st.success('✅ Supabase Connected')
        st.info('🔧 Optimization Engine: Ready')

        # Show last optimization
        if routes:
            latest_route = max(routes, key=lambda x: x.get('created_at', ''))
            created_time = latest_route.get('created_at', '')
            if created_time:
                st.write(f"**Last Route Created:** {created_time[:16]}")

    # Summary statistics
    st.divider()
    st.subheader('Summary Statistics')

    # Placeholder for future analytics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown('### Total Routes (All Time)')
        st.write('Coming soon: Historical route analytics')

    with col2:
        st.markdown('### Avg Efficiency')
        st.write('Coming soon: Performance metrics')

    with col3:
        st.markdown('### Total Distance')
        st.write('Coming soon: Distance analytics')

# Footer
st.divider()
st.caption(f'Dashboard last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
