"""
Route optimization using Google OR-Tools
Vehicle Routing Problem with Time Windows (VRPTW)
"""
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import requests
import numpy as np
from typing import List, Dict, Tuple
import streamlit as st


def create_data_model(stops: List[Dict], technicians: List[Dict], depot_location: Tuple[float, float] = None):
    """
    Create data model for the optimization problem.

    Args:
        stops: List of stop dictionaries with address, service_duration, time_window
        technicians: List of technician dictionaries
        depot_location: Optional (lat, lng) tuple for depot/start location

    Returns:
        Dictionary containing all problem data
    """
    data = {}

    # Number of vehicles (technicians)
    data['num_vehicles'] = len(technicians)

    # Depot is index 0 (starting location for all vehicles)
    data['depot'] = 0

    # Store stop information
    data['stops'] = stops
    data['technicians'] = technicians

    # Time windows (in minutes from start of day, e.g., 8:00 AM = 480)
    # Format: [(earliest, latest), ...]
    data['time_windows'] = []

    # Add depot time window (start of work day)
    depot_start = 480  # 8:00 AM
    depot_end = 1020   # 5:00 PM
    data['time_windows'].append((depot_start, depot_end))

    # Add time windows for each stop
    for stop in stops:
        if stop.get('time_window_start') and stop.get('time_window_end'):
            start = time_to_minutes(stop['time_window_start'])
            end = time_to_minutes(stop['time_window_end'])
        else:
            # Default: allow anytime during work hours
            start = depot_start
            end = depot_end
        data['time_windows'].append((start, end))

    # Service durations at each location (in minutes)
    data['service_times'] = [0]  # 0 for depot
    for stop in stops:
        data['service_times'].append(stop.get('service_duration', 30))

    # Store locations for distance calculation
    data['locations'] = []

    # Add depot location
    if depot_location:
        data['locations'].append(depot_location)
    else:
        # Use first stop as depot if not specified
        if stops and stops[0].get('latitude') and stops[0].get('longitude'):
            data['locations'].append((stops[0]['latitude'], stops[0]['longitude']))
        else:
            data['locations'].append((0, 0))  # Placeholder

    # Add stop locations
    for stop in stops:
        lat = stop.get('latitude', 0)
        lng = stop.get('longitude', 0)
        data['locations'].append((lat, lng))

    return data


def time_to_minutes(time_str):
    """Convert time string (HH:MM or HH:MM:SS) to minutes from midnight"""
    if isinstance(time_str, str):
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        return hours * 60 + minutes
    return 0


def compute_euclidean_distance_matrix(locations):
    """
    Compute Euclidean distance matrix from list of (lat, lng) tuples.
    For production, use Google Distance Matrix API or similar.
    """
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance (approximation)
                # For real-world: use haversine or Distance Matrix API
                lat1, lng1 = from_node
                lat2, lng2 = to_node

                # Simple Euclidean for demo
                distance = np.sqrt((lat1 - lat2)**2 + (lng1 - lng2)**2)
                # Convert to miles (rough approximation: 1 degree ≈ 69 miles)
                distance_miles = distance * 69
                # Convert to time in minutes (assuming average speed 30 mph)
                time_minutes = int((distance_miles / 30) * 60)

                distances[from_counter][to_counter] = time_minutes

    return distances


def get_distance_matrix_google(locations, api_key=None):
    """
    Use Google Distance Matrix API for real driving distances and times.
    Falls back to Euclidean if API key not available.
    """
    if not api_key:
        st.warning("Google Maps API key not configured. Using Euclidean distance approximation.")
        return compute_euclidean_distance_matrix(locations)

    # TODO: Implement Google Distance Matrix API call
    # This requires API key and proper request formatting
    return compute_euclidean_distance_matrix(locations)


def optimize_routes(data):
    """
    Solve the Vehicle Routing Problem with Time Windows using OR-Tools.

    Args:
        data: Data model dictionary from create_data_model()

    Returns:
        Dictionary with optimized routes and statistics
    """
    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(
        len(data['time_windows']),
        data['num_vehicles'],
        data['depot']
    )

    # Create routing model
    routing = pywrapcp.RoutingModel(manager)

    # Create distance callback
    distance_matrix = compute_euclidean_distance_matrix(data['locations'])

    def distance_callback(from_index, to_index):
        """Returns the travel time between two locations."""
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc (travel time)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add time window constraints
    time_dimension_name = 'Time'
    routing.AddDimension(
        transit_callback_index,
        30,  # allow waiting time (slack)
        1440,  # maximum time per vehicle (24 hours in minutes)
        False,  # Don't force start cumul to zero
        time_dimension_name
    )
    time_dimension = routing.GetDimensionOrDie(time_dimension_name)

    # Add time window constraints for each location
    for location_idx, time_window in enumerate(data['time_windows']):
        if location_idx == data['depot']:
            continue
        index = manager.NodeToIndex(location_idx)
        time_dimension.CumulVar(index).SetRange(time_window[0], time_window[1])

    # Add time window constraints for depot (start and end times)
    depot_idx = data['depot']
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        time_dimension.CumulVar(index).SetRange(
            data['time_windows'][depot_idx][0],
            data['time_windows'][depot_idx][1]
        )

    # Instantiate route start and end times to produce feasible times
    for i in range(data['num_vehicles']):
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.Start(i))
        )
        routing.AddVariableMinimizedByFinalizer(
            time_dimension.CumulVar(routing.End(i))
        )

    # Setting first solution heuristic
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 30

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    # Extract solution
    if solution:
        return extract_solution(data, manager, routing, solution, distance_matrix)
    else:
        st.error("No solution found!")
        return None


def extract_solution(data, manager, routing, solution, distance_matrix):
    """Extract the optimized routes from the solution."""
    time_dimension = routing.GetDimensionOrDie('Time')
    total_distance = 0
    total_time = 0
    routes = []

    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        route = {
            'vehicle_id': vehicle_id,
            'technician': data['technicians'][vehicle_id] if vehicle_id < len(data['technicians']) else None,
            'stops': [],
            'total_distance': 0,
            'total_time': 0
        }

        route_distance = 0
        route_time = 0

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_var = time_dimension.CumulVar(index)

            # Skip depot in stop list
            if node_index != data['depot']:
                stop_info = {
                    'stop_index': node_index - 1,  # Adjust for depot offset
                    'stop_data': data['stops'][node_index - 1] if node_index > 0 else None,
                    'arrival_time': solution.Min(time_var),
                    'time_window': data['time_windows'][node_index],
                    'service_time': data['service_times'][node_index]
                }
                route['stops'].append(stop_info)

            previous_index = index
            index = solution.Value(routing.NextVar(index))

            # Calculate distance
            from_node = manager.IndexToNode(previous_index)
            to_node = manager.IndexToNode(index)
            route_distance += distance_matrix[from_node][to_node]

        # Get final time
        time_var = time_dimension.CumulVar(index)
        route_time = solution.Min(time_var)

        route['total_distance'] = route_distance
        route['total_time'] = route_time

        # Only add routes that have stops
        if len(route['stops']) > 0:
            routes.append(route)
            total_distance += route_distance
            total_time += route_time

    result = {
        'routes': routes,
        'total_distance': total_distance,
        'total_time': total_time,
        'num_vehicles_used': len([r for r in routes if len(r['stops']) > 0]),
        'success': True
    }

    return result


def format_route_for_display(route_result):
    """Format optimized route for display in Streamlit."""
    if not route_result or not route_result.get('success'):
        return None

    formatted = []
    for route in route_result['routes']:
        if not route['stops']:
            continue

        tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

        route_info = {
            'technician': tech_name,
            'num_stops': len(route['stops']),
            'total_time': f"{route['total_time']} min",
            'stops': []
        }

        for i, stop in enumerate(route['stops'], 1):
            stop_data = stop['stop_data']
            arrival_min = stop['arrival_time']
            arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

            route_info['stops'].append({
                'order': i,
                'name': stop_data['name'] if stop_data else 'Unknown',
                'address': stop_data['address'] if stop_data else 'Unknown',
                'arrival': arrival_time,
                'service_time': stop['service_time']
            })

        formatted.append(route_info)

    return formatted
