import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
from utils.supabase_client import get_supabase_client, create_stop
from utils.geocoding import geocode_address, format_coordinates

st.set_page_config(page_title="Admin Panel", page_icon="⚙️", layout="wide")

st.title("⚙️ Admin Panel")
st.markdown("System administration and management tools")

# Initialize Supabase
try:
    supabase = get_supabase_client()
    db_connected = True
except Exception as e:
    st.error(f"❌ Database connection failed: {str(e)}")
    db_connected = False

if not db_connected:
    st.stop()

# Create tabs for different admin sections
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 System Overview",
    "➕ Add Stop",
    "👥 Technician Management",
    "📍 Stop Management",
    "🗄️ Data Management"
])

# =============================================
# TAB 1: SYSTEM OVERVIEW
# =============================================
with tab1:
    st.header("System Overview")

    col1, col2, col3, col4 = st.columns(4)

    # Get counts from database
    try:
        # Count technicians
        tech_response = supabase.table('technicians').select('id', count='exact').execute()
        tech_count = len(tech_response.data) if tech_response.data else 0

        # Count stops
        stops_response = supabase.table('stops').select('id', count='exact').execute()
        stops_count = len(stops_response.data) if stops_response.data else 0

        # Count routes
        routes_response = supabase.table('routes').select('id', count='exact').execute()
        routes_count = len(routes_response.data) if routes_response.data else 0

        # Count optimization history
        opt_response = supabase.table('optimization_history').select('id', count='exact').execute()
        opt_count = len(opt_response.data) if opt_response.data else 0

        with col1:
            st.metric("Total Technicians", tech_count, delta="Active")

        with col2:
            st.metric("Total Stops", stops_count, delta="In Database")

        with col3:
            st.metric("Total Routes", routes_count, delta="Created")

        with col4:
            st.metric("Optimizations", opt_count, delta="All Time")

        st.divider()

        # Recent activity
        st.subheader("Recent Activity")

        # Get recent routes
        recent_routes = supabase.table('routes').select('*').order('created_at', desc=True).limit(5).execute()

        if recent_routes.data:
            routes_df = pd.DataFrame(recent_routes.data)
            routes_df['created_at'] = pd.to_datetime(routes_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(
                routes_df[['route_name', 'route_date', 'status', 'created_at']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent routes found")

    except Exception as e:
        st.error(f"Error loading system overview: {str(e)}")

# =============================================
# TAB 2: ADD STOP
# =============================================
with tab2:
    st.header("Add New Service Stop")
    st.markdown("Quick form to add service stops to the system")

    with st.form('admin_add_stop', clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Location Information")
            stop_name = st.text_input('Business/Stop Name*', placeholder='ABC Company')
            stop_address = st.text_input('Complete Address*', placeholder='123 Main St, New York, NY 10001')
            st.caption("📍 Include street, city, state, and ZIP code for automatic geocoding")

            st.divider()

            st.subheader("Customer Information")
            col_a, col_b = st.columns(2)
            with col_a:
                customer_name = st.text_input('Customer Contact Name', placeholder='John Smith')
            with col_b:
                customer_phone = st.text_input('Customer Phone', placeholder='555-0123')

        with col2:
            st.subheader("Service Details")

            col_c, col_d = st.columns(2)
            with col_c:
                service_duration = st.number_input('Service Duration (minutes)*', min_value=5, max_value=480, value=30, step=5)
            with col_d:
                priority = st.select_slider(
                    'Priority Level',
                    options=[1, 2, 3, 4, 5],
                    value=2,
                    format_func=lambda x: {1: '1 - Low', 2: '2 - Normal', 3: '3 - Medium', 4: '4 - High', 5: '5 - Critical'}[x]
                )

            st.divider()

            st.subheader("Time Window")
            col_e, col_f = st.columns(2)
            with col_e:
                time_start = st.time_input('Earliest Start Time*', value=time(9, 0))
            with col_f:
                time_end = st.time_input('Latest End Time*', value=time(17, 0))

        notes = st.text_area('Service Notes / Special Instructions', placeholder='Gate code, parking info, special requirements, etc.', height=100)

        submitted = st.form_submit_button('✅ Add Stop to Database', type='primary', use_container_width=True)

        if submitted:
            if not stop_name or not stop_address:
                st.error('❌ Stop Name and Address are required!')
            else:
                with st.spinner('🌍 Geocoding address...'):
                    # Geocode the address
                    coords = geocode_address(stop_address)

                    if coords:
                        lat, lon = coords
                        st.success(f'✅ Address found: {format_coordinates(lat, lon)}')

                        try:
                            new_stop = {
                                'name': stop_name,
                                'address': stop_address,
                                'latitude': lat,
                                'longitude': lon,
                                'service_duration': service_duration,
                                'time_window_start': str(time_start),
                                'time_window_end': str(time_end),
                                'priority': priority,
                                'customer_name': customer_name if customer_name else None,
                                'customer_phone': customer_phone if customer_phone else None,
                                'notes': notes if notes else None,
                                'status': 'pending'
                            }
                            result = create_stop(supabase, new_stop)
                            if result:
                                st.success(f'✅ Stop "{stop_name}" added successfully!')
                                st.balloons()
                                st.info('Go to "Stop Management" tab to view all stops')
                                # Don't rerun here to let user see the success message
                            else:
                                st.error('❌ Failed to add stop to database')
                        except Exception as e:
                            st.error(f'❌ Error adding stop: {str(e)}')
                    else:
                        st.error('❌ Could not find address coordinates')
                        st.warning('Please check the address and make sure it includes:')
                        st.write('- Street number and name')
                        st.write('- City')
                        st.write('- State')
                        st.write('- ZIP code')

# =============================================
# TAB 3: TECHNICIAN MANAGEMENT
# =============================================
with tab3:
    st.header("Technician Management")

    # Add new technician
    with st.expander("➕ Add New Technician", expanded=False):
        with st.form("add_technician_form"):
            col1, col2 = st.columns(2)

            with col1:
                new_tech_name = st.text_input("Name*")
                new_tech_email = st.text_input("Email*")

            with col2:
                new_tech_phone = st.text_input("Phone")
                new_tech_skills = st.text_input("Skills (comma-separated)", placeholder="HVAC, Plumbing, Electrical")

            new_tech_notes = st.text_area("Notes")

            submitted = st.form_submit_button("Add Technician")

            if submitted:
                if not new_tech_name or not new_tech_email:
                    st.error("Name and Email are required!")
                else:
                    try:
                        skills_list = [s.strip() for s in new_tech_skills.split(',')] if new_tech_skills else []

                        supabase.table('technicians').insert({
                            'name': new_tech_name,
                            'email': new_tech_email,
                            'phone': new_tech_phone if new_tech_phone else None,
                            'skills': skills_list,
                            'notes': new_tech_notes if new_tech_notes else None
                        }).execute()

                        st.success(f"✅ Technician '{new_tech_name}' added successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding technician: {str(e)}")

    st.divider()

    # List existing technicians
    st.subheader("Existing Technicians")

    try:
        techs = supabase.table('technicians').select('*').order('name').execute()

        if techs.data:
            for tech in techs.data:
                with st.expander(f"👤 {tech['name']}", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Email:** {tech.get('email', 'N/A')}")
                        st.write(f"**Phone:** {tech.get('phone', 'N/A')}")
                        st.write(f"**Skills:** {', '.join(tech.get('skills', [])) if tech.get('skills') else 'None'}")

                    with col2:
                        st.write(f"**ID:** {tech['id']}")
                        st.write(f"**Status:** {tech.get('status', 'active')}")
                        if tech.get('notes'):
                            st.write(f"**Notes:** {tech['notes']}")

                    # Delete button
                    if st.button(f"🗑️ Delete {tech['name']}", key=f"delete_tech_{tech['id']}"):
                        try:
                            supabase.table('technicians').delete().eq('id', tech['id']).execute()
                            st.success(f"Technician '{tech['name']}' deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting technician: {str(e)}")
        else:
            st.info("No technicians found. Add your first technician above!")

    except Exception as e:
        st.error(f"Error loading technicians: {str(e)}")

# =============================================
# TAB 4: STOP MANAGEMENT
# =============================================
with tab4:
    st.header("Stop Management")

    # Filter options
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "pending", "scheduled", "completed", "cancelled"])

    with col2:
        search_term = st.text_input("Search by Name/Address")

    with col3:
        show_count = st.number_input("Show Stops", min_value=10, max_value=100, value=25, step=5)

    # Get stops
    try:
        query = supabase.table('stops').select('*')

        if status_filter != "All":
            query = query.eq('status', status_filter)

        stops = query.order('created_at', desc=True).limit(show_count).execute()

        if stops.data:
            stops_df = pd.DataFrame(stops.data)

            # Search filter
            if search_term:
                mask = (
                    stops_df['name'].str.contains(search_term, case=False, na=False) |
                    stops_df['address'].str.contains(search_term, case=False, na=False)
                )
                stops_df = stops_df[mask]

            st.write(f"**Showing {len(stops_df)} stops**")

            # Display stops in a nice format
            for idx, stop in stops_df.iterrows():
                with st.expander(f"📍 {stop['name']} - {stop.get('status', 'pending')}", expanded=False):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(f"**Address:** {stop['address']}")
                        st.write(f"**Customer:** {stop.get('customer_name', 'N/A')}")
                        st.write(f"**Phone:** {stop.get('customer_phone', 'N/A')}")

                    with col2:
                        st.write(f"**Service Duration:** {stop['service_duration']} min")
                        st.write(f"**Priority:** {stop.get('priority', 'N/A')}")
                        st.write(f"**Time Window:** {stop.get('time_window_start', 'N/A')} - {stop.get('time_window_end', 'N/A')}")

                    with col3:
                        st.write(f"**Lat/Lng:** {stop.get('latitude', 'N/A')}, {stop.get('longitude', 'N/A')}")
                        st.write(f"**Status:** {stop.get('status', 'pending')}")
                        st.write(f"**ID:** {stop['id']}")

                    # Delete button
                    if st.button(f"🗑️ Delete Stop", key=f"delete_stop_{stop['id']}"):
                        try:
                            supabase.table('stops').delete().eq('id', stop['id']).execute()
                            st.success(f"Stop '{stop['name']}' deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        else:
            st.info("No stops found")

    except Exception as e:
        st.error(f"Error loading stops: {str(e)}")

# =============================================
# TAB 5: DATA MANAGEMENT
# =============================================
with tab5:
    st.header("Data Management")

    st.warning("⚠️ Use these tools carefully - data operations cannot be undone!")

    # Bulk delete operations
    st.subheader("Bulk Delete Operations")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Delete Old Routes**")
        days_old = st.number_input("Delete routes older than (days)", min_value=7, value=30)

        if st.button("🗑️ Delete Old Routes", type="primary"):
            try:
                cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
                result = supabase.table('routes').delete().lt('created_at', cutoff_date).execute()
                st.success(f"✅ Deleted routes older than {days_old} days")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        st.write("**Delete Completed Stops**")
        if st.button("🗑️ Delete All Completed Stops"):
            try:
                result = supabase.table('stops').delete().eq('status', 'completed').execute()
                st.success("✅ Deleted all completed stops")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.divider()

    # Database statistics
    st.subheader("Database Statistics")

    try:
        # Get detailed counts
        tech_count = len(supabase.table('technicians').select('id').execute().data)
        stops_count = len(supabase.table('stops').select('id').execute().data)
        routes_count = len(supabase.table('routes').select('id').execute().data)
        route_stops_count = len(supabase.table('route_stops').select('id').execute().data)

        stats_df = pd.DataFrame({
            'Table': ['Technicians', 'Stops', 'Routes', 'Route Stops'],
            'Record Count': [tech_count, stops_count, routes_count, route_stops_count]
        })

        st.dataframe(stats_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading statistics: {str(e)}")

    st.divider()

    # Export all data
    st.subheader("Export All Data")

    if st.button("📥 Export All Data to CSV"):
        try:
            # Export each table
            tables = {
                'technicians': supabase.table('technicians').select('*').execute().data,
                'stops': supabase.table('stops').select('*').execute().data,
                'routes': supabase.table('routes').select('*').execute().data,
            }

            for table_name, data in tables.items():
                if data:
                    df = pd.DataFrame(data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label=f"Download {table_name}.csv",
                        data=csv,
                        file_name=f"{table_name}_export_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Error exporting data: {str(e)}")


st.divider()
st.caption("Admin Panel - Route Optimization Platform v1.0.0")
