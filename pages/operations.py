import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date, time

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client, get_all_stops, get_all_technicians, create_stop
from utils.optimization import create_data_model, optimize_routes, format_route_for_display
from utils.maps import visualize_optimized_routes, create_stop_clusters_map, display_map_in_streamlit
from utils.geocoding import geocode_address, format_coordinates
from utils.auth import init_session_state, is_authenticated, get_current_user, get_current_organization, check_permission, show_user_menu, show_subscription_banner

st.set_page_config(page_title="Operations - RouteFlow", layout="wide")

# Initialize session state for authentication
init_session_state()

# Check authentication
if not is_authenticated():
    st.warning("⚠️ Please login to access Operations")
    st.info("Operations page is for planning and optimizing routes. You need an account to access this feature.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button('🔐 Log In', type='primary', use_container_width=True):
            st.switch_page('pages/login.py')
    with col2:
        if st.button('🚀 Sign Up Free', use_container_width=True):
            st.switch_page('pages/register.py')

    st.stop()

# Check permission for operations
if not check_permission('read', 'stops'):
    st.error("🚫 Access denied. Your role does not have permission to view this page.")
    st.stop()

# Get current user and organization
user = get_current_user()
org = get_current_organization()

st.title('🔧 Route Optimization Operations')
st.markdown(f"**{org.get('name', 'Organization')}** - Plan, optimize, and dispatch daily routes")

# Show subscription banner if needed
show_subscription_banner()

# Initialize session state
if 'optimized_routes' not in st.session_state:
    st.session_state.optimized_routes = None
if 'stops_data' not in st.session_state:
    st.session_state.stops_data = []
if 'selected_stops' not in st.session_state:
    st.session_state.selected_stops = []

# Initialize Supabase client
client = get_supabase_client()

# Sidebar for configuration
with st.sidebar:
    # Show user menu
    show_user_menu()

    st.divider()

    st.header('⚙️ Configuration')

    # Date selection
    route_date = st.date_input('📅 Route Date', value=date.today())

    st.divider()

    st.info("💡 Add stops in the 'Stops Management' tab")

# Main content area
tab1, tab2, tab3, tab4 = st.tabs(['📋 Stops Management', '🔧 Optimization', '🗺️ Route Map', '📊 Route Details'])

# TAB 1: Stops Management
with tab1:
    st.header('Manage Stops')

    # Add Stop Form - Prominent at the top
    with st.expander('➕ Add New Stop', expanded=True):
        st.markdown("**Add a new service stop to the database**")
        st.info("📍 Address will be automatically geocoded to get location coordinates")

        with st.form('add_new_stop', clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                stop_name = st.text_input('Stop Name*', placeholder='ABC Company')
                stop_address = st.text_input('Complete Address*', placeholder='123 Main St, New York, NY 10001')

                st.caption("💡 Include city, state, and ZIP for best results")

                col_a, col_b = st.columns(2)
                with col_a:
                    customer_name = st.text_input('Customer Name', placeholder='John Smith')
                with col_b:
                    customer_phone = st.text_input('Customer Phone', placeholder='555-0123')

            with col2:
                col_e, col_f = st.columns(2)
                with col_e:
                    service_duration = st.number_input('Service Time (minutes)*', min_value=5, max_value=480, value=30)
                with col_f:
                    priority = st.slider('Priority', min_value=1, max_value=5, value=2, help='1=Low, 5=Critical')

                col3, col4 = st.columns(2)
                with col3:
                    time_start = st.time_input('Time Window Start*', value=time(9, 0))
                with col4:
                    time_end = st.time_input('Time Window End*', value=time(17, 0))

            notes = st.text_area('Service Notes', placeholder='Special instructions, access codes, etc.')

            submitted = st.form_submit_button('✅ Add Stop to Database', type='primary', use_container_width=True)

            if submitted:
                if not stop_name or not stop_address:
                    st.error('❌ Stop Name and Address are required!')
                else:
                    if client:
                        with st.spinner('🌍 Geocoding address...'):
                            # Geocode the address
                            coords = geocode_address(stop_address)

                            if coords:
                                lat, lon = coords
                                st.success(f'✅ Address geocoded: {format_coordinates(lat, lon)}')

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
                                    result = create_stop(client, new_stop)
                                    if result:
                                        st.success(f'✅ Stop "{stop_name}" added successfully!')
                                        st.balloons()
                                        st.rerun()
                                    else:
                                        st.error('❌ Failed to add stop to database')
                                except Exception as e:
                                    st.error(f'❌ Error adding stop: {str(e)}')
                            else:
                                st.error('❌ Could not geocode address. Please check the address and try again.')
                                st.info('💡 Try including more details: street, city, state, ZIP code')
                    else:
                        st.error('❌ Database connection not available')

    st.divider()

    # View existing stops section
    st.subheader('📋 Existing Stops in Database')

    col1, col2 = st.columns([3, 1])

    with col1:
        if st.button('🔄 Refresh Stops from Database', type='secondary'):
            st.rerun()

    with col2:
        show_map = st.checkbox('Show Map', value=False)

    if client:
        # Fetch all stops
        all_stops = get_all_stops(client)
        st.session_state.stops_data = all_stops

        if all_stops:
            st.info(f'Found {len(all_stops)} stops in database')

            # Display stops in editable dataframe
            df = pd.DataFrame(all_stops)

            # Select columns to display
            display_cols = ['name', 'address', 'service_duration', 'time_window_start', 'time_window_end', 'priority']
            display_cols = [col for col in display_cols if col in df.columns]

            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True
            )

            # Show map of all stops
            if show_map and all_stops:
                st.subheader('All Stops - Map View')
                stops_map = create_stop_clusters_map(all_stops)
                if stops_map:
                    display_map_in_streamlit(stops_map, height=400)

        else:
            st.warning('No stops found in database. Add stops using the sidebar form.')
    else:
        st.error('Unable to connect to Supabase. Please check your configuration.')

# TAB 2: Optimization
with tab2:
    st.header('Optimize Routes')

    if not client:
        st.error('Unable to connect to Supabase')
    else:
        # Get technicians
        technicians = get_all_technicians(client)

        if not technicians:
            st.warning('No technicians found. Please add technicians to the database first.')
        elif not st.session_state.stops_data:
            st.warning('No stops available. Please add stops first.')
        else:
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader('Available Technicians')
                tech_df = pd.DataFrame(technicians)
                if 'name' in tech_df.columns:
                    st.dataframe(tech_df[['name', 'email', 'phone', 'active']], hide_index=True)

            with col2:
                st.metric('Total Technicians', len(technicians))
                st.metric('Total Stops', len(st.session_state.stops_data))

            st.divider()

            # Optimization settings
            with st.expander('⚙️ Optimization Settings', expanded=True):
                col1, col2, col3 = st.columns(3)

                with col1:
                    use_all_stops = st.checkbox('Use all stops', value=True)

                with col2:
                    use_all_techs = st.checkbox('Use all technicians', value=True)

                with col3:
                    max_time_limit = st.number_input('Max solve time (sec)', min_value=10, max_value=300, value=30)

            # Select specific stops if not using all
            selected_stops_indices = []
            if not use_all_stops:
                st.subheader('Select Stops to Include')
                stops_df = pd.DataFrame(st.session_state.stops_data)
                selected_stops_indices = st.multiselect(
                    'Choose stops:',
                    options=range(len(st.session_state.stops_data)),
                    format_func=lambda x: st.session_state.stops_data[x]['name']
                )

            # Select specific technicians if not using all
            selected_tech_indices = []
            if not use_all_techs:
                st.subheader('Select Technicians')
                selected_tech_indices = st.multiselect(
                    'Choose technicians:',
                    options=range(len(technicians)),
                    format_func=lambda x: technicians[x]['name']
                )

            st.divider()

            # Optimization button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button('🚀 Optimize Routes', type='primary', use_container_width=True):
                    # Prepare data
                    stops_to_optimize = st.session_state.stops_data if use_all_stops else [st.session_state.stops_data[i] for i in selected_stops_indices]
                    techs_to_use = technicians if use_all_techs else [technicians[i] for i in selected_tech_indices]

                    if not stops_to_optimize:
                        st.error('Please select at least one stop')
                    elif not techs_to_use:
                        st.error('Please select at least one technician')
                    else:
                        with st.spinner('Optimizing routes... This may take up to 30 seconds.'):
                            try:
                                # Create data model
                                data = create_data_model(stops_to_optimize, techs_to_use)

                                # Run optimization
                                result = optimize_routes(data)

                                if result and result.get('success'):
                                    st.session_state.optimized_routes = result
                                    st.session_state.selected_stops = stops_to_optimize
                                    st.success(f'✅ Optimization complete! {result["num_vehicles_used"]} routes created.')

                                    # Show summary metrics
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric('Routes Created', result['num_vehicles_used'])
                                    with col2:
                                        st.metric('Total Time', f"{result['total_time']} min")
                                    with col3:
                                        st.metric('Stops Assigned', len(stops_to_optimize))

                                    st.info('View optimized routes in the "Route Map" and "Route Details" tabs')
                                else:
                                    st.error('Optimization failed. Please check your data and try again.')

                            except Exception as e:
                                st.error(f'Error during optimization: {str(e)}')

# TAB 3: Route Map
with tab3:
    st.header('Optimized Route Visualization')

    if st.session_state.optimized_routes and st.session_state.selected_stops:
        # Create and display map
        route_map = visualize_optimized_routes(
            st.session_state.optimized_routes,
            st.session_state.selected_stops
        )

        if route_map:
            display_map_in_streamlit(route_map, height=700)

            # Summary statistics
            st.divider()
            st.subheader('Route Summary')

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric('Total Routes', st.session_state.optimized_routes['num_vehicles_used'])
            with col2:
                st.metric('Total Stops', sum(len(r['stops']) for r in st.session_state.optimized_routes['routes']))
            with col3:
                st.metric('Total Time', f"{st.session_state.optimized_routes['total_time']} min")
            with col4:
                avg_stops = sum(len(r['stops']) for r in st.session_state.optimized_routes['routes']) / max(1, st.session_state.optimized_routes['num_vehicles_used'])
                st.metric('Avg Stops/Route', f"{avg_stops:.1f}")
    else:
        st.info('No optimized routes to display. Go to the "Optimization" tab to create routes.')

# TAB 4: Route Details
with tab4:
    st.header('Detailed Route Information')

    if st.session_state.optimized_routes:
        routes = st.session_state.optimized_routes['routes']

        for idx, route in enumerate(routes, 1):
            if not route['stops']:
                continue

            tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

            with st.expander(f"🚗 Route {idx}: {tech_name} - {len(route['stops'])} stops", expanded=True):
                col1, col2 = st.columns([2, 1])

                with col1:
                    # Create stops table
                    stops_data = []
                    for stop_idx, stop_info in enumerate(route['stops'], 1):
                        stop_data = stop_info['stop_data']
                        arrival_min = stop_info['arrival_time']
                        arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                        stops_data.append({
                            'Order': stop_idx,
                            'Stop Name': stop_data['name'],
                            'Address': stop_data['address'],
                            'Arrival Time': arrival_time,
                            'Service (min)': stop_info['service_time']
                        })

                    df = pd.DataFrame(stops_data)
                    st.dataframe(df, hide_index=True, use_container_width=True)

                with col2:
                    st.metric('Total Time', f"{route['total_time']} min")
                    st.metric('Number of Stops', len(route['stops']))

                    # Export buttons
                    st.download_button(
                        label='📥 Download CSV',
                        data=df.to_csv(index=False),
                        file_name=f'route_{tech_name.replace(" ", "_")}_{route_date}.csv',
                        mime='text/csv'
                    )
    else:
        st.info('No route details to display. Optimize routes first in the "Optimization" tab.')
