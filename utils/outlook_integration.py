"""
Microsoft Outlook Calendar integration using Microsoft Graph API
Create calendar events for route stops
"""
import os
import streamlit as st
from datetime import datetime, timedelta
import requests
import msal


def get_graph_config():
    """
    Get Microsoft Graph API configuration

    Returns:
        Dict with Graph API settings or None
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'microsoft_graph' in st.secrets:
            return {
                'client_id': st.secrets['microsoft_graph']['client_id'],
                'client_secret': st.secrets['microsoft_graph']['client_secret'],
                'tenant_id': st.secrets['microsoft_graph']['tenant_id'],
                'authority': f"https://login.microsoftonline.com/{st.secrets['microsoft_graph']['tenant_id']}",
                'scope': ['https://graph.microsoft.com/.default']
            }

        # Try environment variables
        client_id = os.environ.get('MS_CLIENT_ID')
        if client_id:
            tenant_id = os.environ.get('MS_TENANT_ID', 'common')
            return {
                'client_id': client_id,
                'client_secret': os.environ.get('MS_CLIENT_SECRET'),
                'tenant_id': tenant_id,
                'authority': f"https://login.microsoftonline.com/{tenant_id}",
                'scope': ['https://graph.microsoft.com/.default']
            }

        return None

    except Exception as e:
        st.error(f"Error loading Microsoft Graph config: {str(e)}")
        return None


def get_access_token(config):
    """
    Get Microsoft Graph API access token using client credentials flow

    Args:
        config: Graph API configuration dict

    Returns:
        Access token string or None
    """
    try:
        app = msal.ConfidentialClientApplication(
            config['client_id'],
            authority=config['authority'],
            client_credential=config['client_secret'],
        )

        result = app.acquire_token_for_client(scopes=config['scope'])

        if "access_token" in result:
            return result['access_token']
        else:
            error = result.get("error_description", result.get("error"))
            st.error(f"Failed to acquire token: {error}")
            return None

    except Exception as e:
        st.error(f"Error getting access token: {str(e)}")
        return None


def create_calendar_event(access_token, user_email, event_data):
    """
    Create a calendar event for a user using Microsoft Graph API

    Args:
        access_token: Microsoft Graph access token
        user_email: Email of the user whose calendar to update
        event_data: Event dictionary with start, end, subject, location, body

    Returns:
        Boolean success status
    """
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        url = f'https://graph.microsoft.com/v1.0/users/{user_email}/calendar/events'

        response = requests.post(url, headers=headers, json=event_data)

        if response.status_code == 201:
            return True
        else:
            st.error(f"Failed to create event: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        st.error(f"Error creating calendar event: {str(e)}")
        return False


def create_route_calendar_events(route_data, technician_data, route_date):
    """
    Create Outlook calendar events for all stops in a route

    Args:
        route_data: Single route dictionary
        technician_data: Technician information
        route_date: Date string (YYYY-MM-DD)

    Returns:
        Dict with success/failure counts
    """
    config = get_graph_config()

    if not config:
        return {'success': 0, 'failed': 0, 'error': 'Microsoft Graph not configured'}

    access_token = get_access_token(config)

    if not access_token:
        return {'success': 0, 'failed': 0, 'error': 'Failed to get access token'}

    tech_email = technician_data.get('email')
    if not tech_email:
        return {'success': 0, 'failed': 0, 'error': 'Technician email not found'}

    # Parse date
    date_obj = datetime.strptime(route_date, '%Y-%m-%d')

    results = {
        'success': 0,
        'failed': 0,
        'events_created': []
    }

    stops = route_data.get('stops', [])

    for idx, stop_info in enumerate(stops, 1):
        stop_data = stop_info['stop_data']
        arrival_min = stop_info['arrival_time']
        service_time = stop_info['service_time']

        # Calculate start and end times
        start_time = date_obj + timedelta(minutes=arrival_min)
        end_time = start_time + timedelta(minutes=service_time)

        # Format for Graph API (ISO 8601)
        start_str = start_time.isoformat()
        end_str = end_time.isoformat()

        # Build description
        description = f"<h3>Stop {idx} of {len(stops)}</h3>"
        description += f"<p><strong>Customer:</strong> {stop_data.get('customer_name', 'N/A')}</p>"
        description += f"<p><strong>Phone:</strong> {stop_data.get('customer_phone', 'N/A')}</p>"

        if stop_data.get('notes'):
            description += f"<p><strong>Notes:</strong> {stop_data['notes']}</p>"

        description += "<hr>"
        description += "<p><em>Created by Route Optimization Platform</em></p>"

        # Create event data
        event_data = {
            'subject': f"Stop {idx}: {stop_data['name']}",
            'body': {
                'contentType': 'HTML',
                'content': description
            },
            'start': {
                'dateTime': start_str,
                'timeZone': 'America/New_York'
            },
            'end': {
                'dateTime': end_str,
                'timeZone': 'America/New_York'
            },
            'location': {
                'displayName': stop_data['address'],
                'locationType': 'default',
                'uniqueIdType': 'unknown'
            },
            'isReminderOn': True,
            'reminderMinutesBeforeStart': 15,
            'categories': ['Route Assignment']
        }

        # Add location coordinates if available
        if stop_data.get('latitude') and stop_data.get('longitude'):
            event_data['location']['coordinates'] = {
                'latitude': float(stop_data['latitude']),
                'longitude': float(stop_data['longitude'])
            }

        # Create the event
        success = create_calendar_event(access_token, tech_email, event_data)

        if success:
            results['success'] += 1
            results['events_created'].append(stop_data['name'])
        else:
            results['failed'] += 1

    return results


def create_bulk_calendar_events(routes_data, route_date):
    """
    Create Outlook calendar events for all technicians

    Args:
        routes_data: Optimization results with multiple routes
        route_date: Date string

    Returns:
        Dict with overall success/failure counts
    """
    config = get_graph_config()

    if not config:
        return {'success': 0, 'failed': 0, 'error': 'Microsoft Graph not configured'}

    overall_results = {
        'success': 0,
        'failed': 0,
        'technicians_processed': 0,
        'errors': []
    }

    for route in routes_data['routes']:
        if not route['stops']:
            continue

        tech = route.get('technician')
        if not tech or not tech.get('email'):
            overall_results['errors'].append(f"Skipped route: missing technician email")
            continue

        results = create_route_calendar_events(route, tech, route_date)

        if 'error' in results:
            overall_results['errors'].append(f"{tech['name']}: {results['error']}")
        else:
            overall_results['success'] += results['success']
            overall_results['failed'] += results['failed']
            overall_results['technicians_processed'] += 1

    return overall_results


def delete_calendar_events(user_email, date_str, category='Route Assignment'):
    """
    Delete calendar events for a specific date and category

    Args:
        user_email: User's email address
        date_str: Date string (YYYY-MM-DD)
        category: Event category to filter

    Returns:
        Number of events deleted
    """
    config = get_graph_config()

    if not config:
        st.error('Microsoft Graph not configured')
        return 0

    access_token = get_access_token(config)

    if not access_token:
        return 0

    try:
        # Get events for the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        start_dt = date_obj.replace(hour=0, minute=0, second=0).isoformat()
        end_dt = date_obj.replace(hour=23, minute=59, second=59).isoformat()

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Query for events
        url = f'https://graph.microsoft.com/v1.0/users/{user_email}/calendar/calendarView'
        params = {
            'startDateTime': start_dt,
            'endDateTime': end_dt,
            '$filter': f"categories/any(c:c eq '{category}')"
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            st.error(f"Failed to fetch events: {response.status_code}")
            return 0

        events = response.json().get('value', [])
        deleted_count = 0

        # Delete each event
        for event in events:
            event_id = event['id']
            delete_url = f'https://graph.microsoft.com/v1.0/users/{user_email}/calendar/events/{event_id}'

            del_response = requests.delete(delete_url, headers=headers)

            if del_response.status_code == 204:
                deleted_count += 1

        return deleted_count

    except Exception as e:
        st.error(f"Error deleting events: {str(e)}")
        return 0


def check_graph_api_status():
    """
    Check if Microsoft Graph API is configured and accessible

    Returns:
        Dict with status information
    """
    config = get_graph_config()

    if not config:
        return {
            'configured': False,
            'accessible': False,
            'message': 'Microsoft Graph API not configured'
        }

    access_token = get_access_token(config)

    if not access_token:
        return {
            'configured': True,
            'accessible': False,
            'message': 'Failed to acquire access token'
        }

    return {
        'configured': True,
        'accessible': True,
        'message': 'Microsoft Graph API ready'
    }
