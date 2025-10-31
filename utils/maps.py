"""
Map visualization utilities using Folium
"""
import folium
from folium import plugins
import streamlit as st
from streamlit_folium import st_folium
import pandas as pd


# Color palette for different routes/technicians
ROUTE_COLORS = [
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
    '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8B195', '#6C5CE7'
]


def create_base_map(center_lat=39.8283, center_lng=-98.5795, zoom=4):
    """
    Create a base Folium map centered on the US or specified location.

    Args:
        center_lat: Latitude for map center
        center_lng: Longitude for map center
        zoom: Initial zoom level

    Returns:
        Folium Map object
    """
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=zoom,
        tiles='OpenStreetMap'
    )
    return m


def add_markers_to_map(folium_map, locations, color='blue', icon='info-sign'):
    """
    Add markers to a Folium map.

    Args:
        folium_map: Folium Map object
        locations: List of dicts with 'lat', 'lng', 'name', 'popup' keys
        color: Marker color
        icon: Marker icon
    """
    for loc in locations:
        folium.Marker(
            location=[loc['lat'], loc['lng']],
            popup=folium.Popup(loc.get('popup', loc.get('name', 'Location')), max_width=300),
            tooltip=loc.get('name', 'Location'),
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(folium_map)

    return folium_map


def add_route_to_map(folium_map, route_coords, color='blue', weight=3, opacity=0.7, popup_text=None):
    """
    Add a route line to the map.

    Args:
        folium_map: Folium Map object
        route_coords: List of [lat, lng] coordinate pairs
        color: Line color
        weight: Line weight
        opacity: Line opacity
        popup_text: Optional text for route popup
    """
    folium.PolyLine(
        locations=route_coords,
        color=color,
        weight=weight,
        opacity=opacity,
        popup=popup_text
    ).add_to(folium_map)

    return folium_map


def visualize_optimized_routes(route_result, stops_data):
    """
    Create a comprehensive map visualization of optimized routes.

    Args:
        route_result: Result from optimization.optimize_routes()
        stops_data: List of stop dictionaries with location info

    Returns:
        Folium Map object with all routes visualized
    """
    if not route_result or not route_result.get('success'):
        st.error("No valid route data to visualize")
        return None

    # Calculate center point from all stops
    all_lats = [stop['latitude'] for stop in stops_data if stop.get('latitude')]
    all_lngs = [stop['longitude'] for stop in stops_data if stop.get('longitude')]

    if not all_lats or not all_lngs:
        st.error("No valid coordinates found in stops data")
        return None

    center_lat = sum(all_lats) / len(all_lats)
    center_lng = sum(all_lngs) / len(all_lngs)

    # Create base map
    m = create_base_map(center_lat, center_lng, zoom=10)

    # Add routes
    for idx, route in enumerate(route_result['routes']):
        if not route['stops']:
            continue

        color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
        tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

        # Collect route coordinates
        route_coords = []

        # Add markers and collect coords for each stop
        for stop_idx, stop_info in enumerate(route['stops'], 1):
            stop_data = stop_info['stop_data']

            if not stop_data or not stop_data.get('latitude') or not stop_data.get('longitude'):
                continue

            lat = stop_data['latitude']
            lng = stop_data['longitude']
            route_coords.append([lat, lng])

            # Create detailed popup
            arrival_min = stop_info['arrival_time']
            arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

            popup_html = f"""
            <div style="font-family: Arial; width: 200px;">
                <h4 style="margin: 0 0 10px 0; color: {color};">Stop {stop_idx}: {stop_data['name']}</h4>
                <p style="margin: 5px 0;"><b>Technician:</b> {tech_name}</p>
                <p style="margin: 5px 0;"><b>Address:</b> {stop_data['address']}</p>
                <p style="margin: 5px 0;"><b>Arrival:</b> {arrival_time}</p>
                <p style="margin: 5px 0;"><b>Service Time:</b> {stop_info['service_time']} min</p>
            </div>
            """

            # Add numbered marker
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{stop_idx}. {stop_data['name']}",
                icon=folium.DivIcon(html=f"""
                    <div style="
                        background-color: {color};
                        border: 2px solid white;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        color: white;
                        font-size: 14px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    ">{stop_idx}</div>
                """)
            ).add_to(m)

        # Draw route line
        if len(route_coords) > 1:
            folium.PolyLine(
                locations=route_coords,
                color=color,
                weight=4,
                opacity=0.7,
                popup=f"{tech_name} - {len(route['stops'])} stops"
            ).add_to(m)

            # Add arrow decorators to show direction
            plugins.PolyLineTextPath(
                folium.PolyLine(route_coords, weight=0),
                '\u25BA',
                repeat=True,
                offset=10,
                attributes={'fill': color, 'font-size': '12'}
            ).add_to(m)

    # Add legend
    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 220px;
        background-color: white;
        border: 2px solid grey;
        border-radius: 5px;
        padding: 10px;
        font-size: 14px;
        z-index: 9999;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    ">
        <h4 style="margin-top: 0;">Routes Legend</h4>
    """

    for idx, route in enumerate(route_result['routes']):
        if not route['stops']:
            continue
        color = ROUTE_COLORS[idx % len(ROUTE_COLORS)]
        tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"
        legend_html += f"""
        <div style="margin: 5px 0;">
            <span style="
                display: inline-block;
                width: 20px;
                height: 20px;
                background-color: {color};
                border-radius: 50%;
                margin-right: 8px;
                vertical-align: middle;
            "></span>
            <span style="vertical-align: middle;">{tech_name} ({len(route['stops'])} stops)</span>
        </div>
        """

    legend_html += """
        <hr style="margin: 10px 0;">
        <div style="font-size: 12px; color: #666;">
            Click markers for details
        </div>
    </div>
    """

    m.get_root().html.add_child(folium.Element(legend_html))

    # Fit bounds to show all markers
    if route_coords:
        m.fit_bounds([[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]])

    return m


def display_map_in_streamlit(folium_map, width=None, height=600):
    """
    Display a Folium map in Streamlit.

    Args:
        folium_map: Folium Map object
        width: Map width (None for auto)
        height: Map height in pixels
    """
    if folium_map is None:
        st.error("No map to display")
        return

    st_folium(folium_map, width=width, height=height)


def create_stop_clusters_map(stops):
    """
    Create a map with clustered markers for many stops.
    Useful for visualizing all available stops before optimization.

    Args:
        stops: List of stop dictionaries with latitude, longitude

    Returns:
        Folium Map object
    """
    # Calculate center
    valid_stops = [s for s in stops if s.get('latitude') and s.get('longitude')]

    if not valid_stops:
        st.warning("No valid stop locations to display")
        return None

    center_lat = sum(s['latitude'] for s in valid_stops) / len(valid_stops)
    center_lng = sum(s['longitude'] for s in valid_stops) / len(valid_stops)

    # Create map
    m = create_base_map(center_lat, center_lng, zoom=10)

    # Add marker cluster
    marker_cluster = plugins.MarkerCluster().add_to(m)

    for stop in valid_stops:
        popup_html = f"""
        <div style="width: 200px;">
            <h4>{stop['name']}</h4>
            <p><b>Address:</b> {stop['address']}</p>
            <p><b>Service Time:</b> {stop.get('service_duration', 30)} min</p>
            {f"<p><b>Time Window:</b> {stop.get('time_window_start', 'N/A')} - {stop.get('time_window_end', 'N/A')}</p>" if stop.get('time_window_start') else ""}
        </div>
        """

        folium.Marker(
            location=[stop['latitude'], stop['longitude']],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=stop['name']
        ).add_to(marker_cluster)

    return m
