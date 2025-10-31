import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date, datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client
from utils.maps import create_base_map, add_markers_to_map, display_map_in_streamlit
import folium

st.set_page_config(
    page_title="Technician View",
    page_icon="👷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-friendly CSS
st.markdown("""
<style>
    /* Mobile-first responsive design */
    .main {
        padding: 1rem;
    }

    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 18px;
        margin: 5px 0;
    }

    .stop-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 5px solid #4CAF50;
    }

    .stop-card.completed {
        opacity: 0.6;
        border-left-color: #9E9E9E;
    }

    .stop-card.current {
        border-left-color: #2196F3;
        background: #E3F2FD;
    }

    h1, h2, h3 {
        margin-top: 0.5rem !important;
    }

    @media (max-width: 768px) {
        .main {
            padding: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

st.title('👷 Technician Route View')

# Initialize session state for tracking
if 'current_stop_index' not in st.session_state:
    st.session_state.current_stop_index = 0

if 'completed_stops' not in st.session_state:
    st.session_state.completed_stops = set()

if 'check_in_times' not in st.session_state:
    st.session_state.check_in_times = {}

if 'technician_notes' not in st.session_state:
    st.session_state.technician_notes = {}

# Sidebar for technician selection
with st.sidebar:
    st.header('Select Your Route')

    # In a production app, this would authenticate the technician
    # For now, we'll use a simple selection

    client = get_supabase_client()

    if client:
        # Fetch technicians
        try:
            response = client.table('technicians').select('*').eq('active', True).execute()
            technicians = response.data if response.data else []

            if technicians:
                tech_names = [t['name'] for t in technicians]
                selected_tech_name = st.selectbox('Your Name', tech_names)

                selected_tech = next((t for t in technicians if t['name'] == selected_tech_name), None)

                # Date selection
                route_date = st.date_input('Route Date', value=date.today())

                st.divider()

                # Load route button
                if st.button('📥 Load My Route', use_container_width=True):
                    st.session_state.selected_technician = selected_tech
                    st.session_state.route_date = route_date
                    st.session_state.current_stop_index = 0
                    st.session_state.completed_stops = set()
                    st.rerun()

            else:
                st.warning('No technicians found')

        except Exception as e:
            st.error(f'Error loading technicians: {str(e)}')
    else:
        st.error('Database connection failed')

# Main content
if 'selected_technician' not in st.session_state:
    # Welcome screen
    st.info('👈 Use the sidebar to select your name and load your route for the day')

    st.markdown('''
    ## Welcome!

    This is your mobile-friendly route view. Features:

    - 📍 **View all stops** in order
    - ✅ **Check in** at each location
    - 📝 **Add notes** about each stop
    - 📸 **Track completion** status
    - 🗺️ **See map** with directions

    Select your name from the sidebar to get started!
    ''')

    # Sample route display
    st.subheader('Sample Route View')

    sample_stops = [
        {'name': 'ABC Corp', 'address': '123 Main St', 'time': '09:00', 'status': 'pending'},
        {'name': 'XYZ Industries', 'address': '456 Oak Ave', 'time': '10:30', 'status': 'pending'},
        {'name': 'Smith Residence', 'address': '789 Pine Rd', 'time': '13:00', 'status': 'pending'},
    ]

    for idx, stop in enumerate(sample_stops, 1):
        st.markdown(f"""
        <div class="stop-card">
            <h3>Stop {idx}: {stop['name']}</h3>
            <p><strong>📍</strong> {stop['address']}</p>
            <p><strong>🕐</strong> Arrival: {stop['time']}</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Display route for selected technician
    tech = st.session_state.selected_technician
    route_date = st.session_state.route_date

    st.markdown(f"### 👤 {tech['name']} - {route_date.strftime('%B %d, %Y')}")

    # For demo, we'll use session state routes if available
    # In production, this would fetch from database
    if 'optimized_routes' in st.session_state and st.session_state.optimized_routes:
        # Find this technician's route
        tech_route = None
        for route in st.session_state.optimized_routes['routes']:
            if route.get('technician') and route['technician']['name'] == tech['name']:
                tech_route = route
                break

        if not tech_route or not tech_route.get('stops'):
            st.warning('No route found for today. Check with your dispatcher.')
            st.stop()

        stops = tech_route['stops']

        # Progress bar
        completed_count = len(st.session_state.completed_stops)
        progress = completed_count / len(stops) if stops else 0

        st.progress(progress, text=f"{completed_count} of {len(stops)} stops completed")

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric('Total Stops', len(stops))

        with col2:
            st.metric('Completed', completed_count)

        with col3:
            remaining = len(stops) - completed_count
            st.metric('Remaining', remaining)

        st.divider()

        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(['📋 Stops List', '🗺️ Map View', '📊 Summary'])

        # TAB 1: Stops List
        with tab1:
            st.subheader('Your Route')

            # Show each stop
            for idx, stop_info in enumerate(stops):
                stop_data = stop_info['stop_data']
                arrival_min = stop_info['arrival_time']
                arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                is_completed = idx in st.session_state.completed_stops
                is_current = idx == st.session_state.current_stop_index and not is_completed

                # Determine card class
                card_class = 'stop-card'
                if is_completed:
                    card_class += ' completed'
                    status_icon = '✅'
                    status_text = 'Completed'
                elif is_current:
                    card_class += ' current'
                    status_icon = '🔵'
                    status_text = 'Current Stop'
                else:
                    status_icon = '⏱️'
                    status_text = 'Upcoming'

                with st.container():
                    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                    col1, col2 = st.columns([3, 1])

                    with col1:
                        st.markdown(f"### {status_icon} Stop {idx + 1}: {stop_data['name']}")
                        st.markdown(f"**📍 Address:** {stop_data['address']}")
                        st.markdown(f"**🕐 Arrival:** {arrival_time} | **⏱️ Duration:** {stop_info['service_time']} min")

                        if stop_data.get('customer_name'):
                            st.markdown(f"**👤 Customer:** {stop_data['customer_name']}")

                        if stop_data.get('customer_phone'):
                            st.markdown(f"**📞 Phone:** {stop_data['customer_phone']}")

                        if stop_data.get('notes'):
                            st.info(f"📝 **Notes:** {stop_data['notes']}")

                    with col2:
                        st.markdown(f"**Status:**")
                        st.markdown(f"*{status_text}*")

                    # Action buttons
                    if not is_completed:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            if st.button('🚗 Navigate', key=f'nav_{idx}', use_container_width=True):
                                # Open Google Maps
                                address_encoded = stop_data['address'].replace(' ', '+')
                                maps_url = f"https://www.google.com/maps/dir/?api=1&destination={address_encoded}"
                                st.markdown(f'[Open in Google Maps]({maps_url})')

                        with col2:
                            if st.button('📍 Check In', key=f'checkin_{idx}', use_container_width=True):
                                st.session_state.check_in_times[idx] = datetime.now()
                                st.session_state.current_stop_index = idx
                                st.success(f'Checked in at {datetime.now().strftime("%H:%M")}')
                                st.rerun()

                        with col3:
                            if st.button('✅ Complete', key=f'complete_{idx}', use_container_width=True):
                                st.session_state.completed_stops.add(idx)
                                if idx == st.session_state.current_stop_index:
                                    st.session_state.current_stop_index += 1
                                st.success('Stop marked complete!')
                                st.rerun()

                        # Notes section
                        with st.expander('📝 Add Notes'):
                            note = st.text_area(
                                'Job notes',
                                value=st.session_state.technician_notes.get(idx, ''),
                                key=f'note_{idx}',
                                help='Add any observations or issues'
                            )

                            if st.button('💾 Save Note', key=f'save_note_{idx}'):
                                st.session_state.technician_notes[idx] = note
                                st.success('Note saved!')

                    else:
                        # Show completion info
                        if idx in st.session_state.check_in_times:
                            check_in_time = st.session_state.check_in_times[idx]
                            st.success(f'✅ Completed | Check-in: {check_in_time.strftime("%H:%M")}')

                        if idx in st.session_state.technician_notes:
                            with st.expander('View Notes'):
                                st.info(st.session_state.technician_notes[idx])

                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('<br>', unsafe_allow_html=True)

        # TAB 2: Map View
        with tab2:
            st.subheader('Route Map')

            # Create map with all stops
            if stops:
                # Get coordinates
                coords = []
                for stop_info in stops:
                    stop_data = stop_info['stop_data']
                    if stop_data.get('latitude') and stop_data.get('longitude'):
                        coords.append((stop_data['latitude'], stop_data['longitude']))

                if coords:
                    # Calculate center
                    center_lat = sum(c[0] for c in coords) / len(coords)
                    center_lng = sum(c[1] for c in coords) / len(coords)

                    # Create map
                    m = folium.Map(location=[center_lat, center_lng], zoom_start=12)

                    # Add markers
                    for idx, stop_info in enumerate(stops):
                        stop_data = stop_info['stop_data']

                        if stop_data.get('latitude') and stop_data.get('longitude'):
                            is_completed = idx in st.session_state.completed_stops
                            is_current = idx == st.session_state.current_stop_index

                            # Color based on status
                            if is_completed:
                                color = 'gray'
                                icon = 'check'
                            elif is_current:
                                color = 'blue'
                                icon = 'car'
                            else:
                                color = 'red'
                                icon = 'map-marker'

                            popup_text = f"""
                            <b>Stop {idx + 1}: {stop_data['name']}</b><br>
                            {stop_data['address']}<br>
                            Status: {'Completed' if is_completed else 'Current' if is_current else 'Upcoming'}
                            """

                            folium.Marker(
                                [stop_data['latitude'], stop_data['longitude']],
                                popup=popup_text,
                                tooltip=f"{idx + 1}. {stop_data['name']}",
                                icon=folium.Icon(color=color, icon=icon)
                            ).add_to(m)

                    # Display map
                    st.components.v1.html(m._repr_html_(), height=600)

                else:
                    st.warning('No location coordinates available for mapping')

        # TAB 3: Summary
        with tab3:
            st.subheader('Route Summary')

            summary_data = []
            for idx, stop_info in enumerate(stops):
                stop_data = stop_info['stop_data']
                is_completed = idx in st.session_state.completed_stops

                arrival_min = stop_info['arrival_time']
                arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                check_in = ''
                if idx in st.session_state.check_in_times:
                    check_in = st.session_state.check_in_times[idx].strftime("%H:%M")

                summary_data.append({
                    'Stop': idx + 1,
                    'Name': stop_data['name'],
                    'Scheduled': arrival_time,
                    'Check-in': check_in,
                    'Status': '✅ Complete' if is_completed else '⏱️ Pending',
                    'Notes': 'Yes' if idx in st.session_state.technician_notes else ''
                })

            df_summary = pd.DataFrame(summary_data)
            st.dataframe(df_summary, hide_index=True, use_container_width=True)

            st.divider()

            # Performance metrics
            if len(st.session_state.check_in_times) > 1:
                st.subheader('Performance')

                col1, col2 = st.columns(2)

                with col1:
                    on_time_count = 0
                    # This would compare actual vs scheduled times
                    # Simplified for demo
                    st.metric('On-Time Arrivals', f"{on_time_count}/{len(st.session_state.check_in_times)}")

                with col2:
                    if st.session_state.check_in_times:
                        first_stop = min(st.session_state.check_in_times.keys())
                        last_stop = max(st.session_state.check_in_times.keys())

                        start_time = st.session_state.check_in_times[first_stop]
                        end_time = st.session_state.check_in_times[last_stop]

                        duration = (end_time - start_time).total_seconds() / 60
                        st.metric('Time Elapsed', f"{int(duration)} min")

    else:
        st.info('No routes available. Routes will appear here after optimization and dispatch.')

# Bottom navigation (always visible)
st.divider()

col1, col2 = st.columns(2)

with col1:
    if st.button('🏠 Home', use_container_width=True):
        st.switch_page('main.py')

with col2:
    if st.button('🔄 Refresh', use_container_width=True):
        st.rerun()
