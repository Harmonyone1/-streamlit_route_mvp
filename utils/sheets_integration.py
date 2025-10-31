"""
Google Sheets integration for importing and exporting route data
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import json
import os


def get_google_sheets_client():
    """
    Initialize Google Sheets client using service account credentials

    Returns:
        gspread.Client or None
    """
    try:
        # Try to get credentials from Streamlit secrets
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            credentials_dict = dict(st.secrets['gcp_service_account'])
        # Try from environment variable
        elif os.environ.get('GOOGLE_SHEETS_CREDENTIALS'):
            credentials_dict = json.loads(os.environ.get('GOOGLE_SHEETS_CREDENTIALS'))
        # Try from file
        elif os.path.exists('credentials/google_service_account.json'):
            with open('credentials/google_service_account.json', 'r') as f:
                credentials_dict = json.load(f)
        else:
            return None

        # Define the required scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]

        # Create credentials
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=scopes
        )

        # Authorize and return client
        client = gspread.authorize(credentials)
        return client

    except Exception as e:
        st.error(f"Error initializing Google Sheets client: {str(e)}")
        return None


def read_stops_from_sheet(client, spreadsheet_url_or_id, worksheet_name='Stops'):
    """
    Read stops data from a Google Sheet

    Args:
        client: gspread.Client
        spreadsheet_url_or_id: URL or ID of the spreadsheet
        worksheet_name: Name of the worksheet to read

    Returns:
        List of stop dictionaries or None
    """
    try:
        # Open the spreadsheet
        if spreadsheet_url_or_id.startswith('http'):
            sheet = client.open_by_url(spreadsheet_url_or_id)
        else:
            sheet = client.open_by_key(spreadsheet_url_or_id)

        # Get the worksheet
        worksheet = sheet.worksheet(worksheet_name)

        # Get all records (assumes first row is headers)
        records = worksheet.get_all_records()

        # Convert to stop format
        stops = []
        for record in records:
            stop = {
                'name': record.get('name') or record.get('Name') or record.get('Stop Name'),
                'address': record.get('address') or record.get('Address'),
                'latitude': float(record.get('latitude') or record.get('Latitude') or 0),
                'longitude': float(record.get('longitude') or record.get('Longitude') or 0),
                'service_duration': int(record.get('service_duration') or record.get('Service Duration') or 30),
                'time_window_start': record.get('time_window_start') or record.get('Time Window Start'),
                'time_window_end': record.get('time_window_end') or record.get('Time Window End'),
                'priority': int(record.get('priority') or record.get('Priority') or 1),
                'notes': record.get('notes') or record.get('Notes') or '',
                'customer_name': record.get('customer_name') or record.get('Customer Name') or '',
                'customer_phone': record.get('customer_phone') or record.get('Customer Phone') or ''
            }

            # Only add if has required fields
            if stop['name'] and stop['address']:
                stops.append(stop)

        return stops

    except Exception as e:
        st.error(f"Error reading from Google Sheet: {str(e)}")
        return None


def write_routes_to_sheet(client, spreadsheet_url_or_id, routes_data, worksheet_name='Optimized Routes'):
    """
    Write optimized routes to a Google Sheet

    Args:
        client: gspread.Client
        spreadsheet_url_or_id: URL or ID of the spreadsheet
        routes_data: Route result from optimization
        worksheet_name: Name of the worksheet to write to

    Returns:
        Boolean success
    """
    try:
        # Open the spreadsheet
        if spreadsheet_url_or_id.startswith('http'):
            sheet = client.open_by_url(spreadsheet_url_or_id)
        else:
            sheet = client.open_by_key(spreadsheet_url_or_id)

        # Try to get existing worksheet or create new one
        try:
            worksheet = sheet.worksheet(worksheet_name)
            worksheet.clear()  # Clear existing data
        except:
            worksheet = sheet.add_worksheet(title=worksheet_name, rows=100, cols=10)

        # Prepare data for writing
        headers = [
            'Technician',
            'Route',
            'Stop Order',
            'Stop Name',
            'Address',
            'Arrival Time',
            'Service Duration (min)',
            'Notes'
        ]

        rows = [headers]

        # Add route data
        for route_idx, route in enumerate(routes_data['routes'], 1):
            tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

            for stop_idx, stop_info in enumerate(route['stops'], 1):
                stop_data = stop_info['stop_data']
                arrival_min = stop_info['arrival_time']
                arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                row = [
                    tech_name,
                    f"Route {route_idx}",
                    stop_idx,
                    stop_data['name'],
                    stop_data['address'],
                    arrival_time,
                    stop_info['service_time'],
                    stop_data.get('notes', '')
                ]
                rows.append(row)

        # Write to sheet
        worksheet.update('A1', rows)

        # Format headers (bold)
        worksheet.format('A1:H1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })

        return True

    except Exception as e:
        st.error(f"Error writing to Google Sheet: {str(e)}")
        return False


def create_stops_template_sheet(client, title='Route Stops Template'):
    """
    Create a template Google Sheet for stops data

    Args:
        client: gspread.Client
        title: Title for the new spreadsheet

    Returns:
        Spreadsheet URL or None
    """
    try:
        # Create new spreadsheet
        spreadsheet = client.create(title)

        # Get the first worksheet
        worksheet = spreadsheet.sheet1
        worksheet.update_title('Stops')

        # Add headers and sample data
        headers = [
            'Name',
            'Address',
            'Latitude',
            'Longitude',
            'Service Duration',
            'Time Window Start',
            'Time Window End',
            'Priority',
            'Customer Name',
            'Customer Phone',
            'Notes'
        ]

        sample_data = [
            [
                'ABC Corp',
                '123 Main St, New York, NY 10001',
                40.7589,
                -73.9851,
                45,
                '09:00',
                '12:00',
                1,
                'John Smith',
                '555-0101',
                'Ring doorbell twice'
            ],
            [
                'XYZ Industries',
                '456 Park Ave, New York, NY 10022',
                40.7614,
                -73.9776,
                30,
                '10:00',
                '14:00',
                2,
                'Jane Doe',
                '555-0102',
                'Loading dock in rear'
            ]
        ]

        # Write to sheet
        worksheet.update('A1', [headers] + sample_data)

        # Format headers
        worksheet.format('A1:K1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.9}
        })

        # Make shareable
        spreadsheet.share('', perm_type='anyone', role='writer')

        return spreadsheet.url

    except Exception as e:
        st.error(f"Error creating template sheet: {str(e)}")
        return None


def sync_stops_bidirectional(client, spreadsheet_url, supabase_client, direction='sheet_to_db'):
    """
    Sync stops between Google Sheets and Supabase database

    Args:
        client: gspread.Client
        spreadsheet_url: URL of Google Sheet
        supabase_client: Supabase client
        direction: 'sheet_to_db', 'db_to_sheet', or 'both'

    Returns:
        Dictionary with sync results
    """
    from utils.supabase_client import get_all_stops, create_stop

    results = {
        'success': False,
        'imported': 0,
        'exported': 0,
        'errors': []
    }

    try:
        if direction in ['sheet_to_db', 'both']:
            # Import from sheet to database
            stops_from_sheet = read_stops_from_sheet(client, spreadsheet_url)

            if stops_from_sheet:
                for stop in stops_from_sheet:
                    result = create_stop(supabase_client, stop)
                    if result:
                        results['imported'] += 1
                    else:
                        results['errors'].append(f"Failed to import: {stop['name']}")

        if direction in ['db_to_sheet', 'both']:
            # Export from database to sheet
            stops_from_db = get_all_stops(supabase_client)

            if stops_from_db:
                # Convert to sheet format and write
                df = pd.DataFrame(stops_from_db)

                # Open sheet and write
                sheet = client.open_by_url(spreadsheet_url)
                worksheet = sheet.worksheet('Stops')

                # Prepare data
                columns = ['name', 'address', 'latitude', 'longitude', 'service_duration',
                          'time_window_start', 'time_window_end', 'priority',
                          'customer_name', 'customer_phone', 'notes']

                data = df[columns].fillna('').values.tolist()
                headers = [col.replace('_', ' ').title() for col in columns]

                worksheet.clear()
                worksheet.update('A1', [headers] + data)

                results['exported'] = len(stops_from_db)

        results['success'] = True
        return results

    except Exception as e:
        results['errors'].append(str(e))
        return results
