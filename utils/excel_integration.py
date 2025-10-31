"""
Excel file integration for importing and exporting route data
"""
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime


def parse_excel_stops(uploaded_file):
    """
    Parse stops data from uploaded Excel file

    Args:
        uploaded_file: Streamlit UploadedFile object

    Returns:
        List of stop dictionaries or None
    """
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file, sheet_name=0)

        # Normalize column names (handle different cases and formats)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Map common column name variations
        column_mapping = {
            'stop_name': 'name',
            'location': 'address',
            'lat': 'latitude',
            'lng': 'longitude',
            'lon': 'longitude',
            'service_time': 'service_duration',
            'duration': 'service_duration',
            'time_start': 'time_window_start',
            'start_time': 'time_window_start',
            'time_end': 'time_window_end',
            'end_time': 'time_window_end',
            'customer': 'customer_name',
            'phone': 'customer_phone'
        }

        # Rename columns
        df = df.rename(columns=column_mapping)

        # Convert to list of dictionaries
        stops = []
        for _, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get('name')) or pd.isna(row.get('address')):
                continue

            stop = {
                'name': str(row.get('name', '')).strip(),
                'address': str(row.get('address', '')).strip(),
                'latitude': float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else None,
                'longitude': float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else None,
                'service_duration': int(row.get('service_duration', 30)) if pd.notna(row.get('service_duration')) else 30,
                'time_window_start': str(row.get('time_window_start', '')) if pd.notna(row.get('time_window_start')) else None,
                'time_window_end': str(row.get('time_window_end', '')) if pd.notna(row.get('time_window_end')) else None,
                'priority': int(row.get('priority', 1)) if pd.notna(row.get('priority')) else 1,
                'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else '',
                'customer_name': str(row.get('customer_name', '')) if pd.notna(row.get('customer_name')) else '',
                'customer_phone': str(row.get('customer_phone', '')) if pd.notna(row.get('customer_phone')) else ''
            }

            # Clean up time windows (handle various formats)
            if stop['time_window_start']:
                stop['time_window_start'] = clean_time_format(stop['time_window_start'])
            if stop['time_window_end']:
                stop['time_window_end'] = clean_time_format(stop['time_window_end'])

            # Only add if has required fields
            if stop['name'] and stop['address']:
                stops.append(stop)

        return stops

    except Exception as e:
        st.error(f"Error parsing Excel file: {str(e)}")
        return None


def clean_time_format(time_value):
    """
    Clean and standardize time format to HH:MM

    Args:
        time_value: Time as string or datetime

    Returns:
        String in HH:MM format or None
    """
    try:
        # If already a string in correct format
        if isinstance(time_value, str):
            # Remove any extra whitespace
            time_value = time_value.strip()

            # If already in HH:MM or HH:MM:SS format
            if ':' in time_value:
                parts = time_value.split(':')
                return f"{int(parts[0]):02d}:{int(parts[1]):02d}"

        # If it's a datetime object
        if isinstance(time_value, datetime):
            return time_value.strftime('%H:%M')

        # If it's a pandas Timestamp
        if hasattr(time_value, 'strftime'):
            return time_value.strftime('%H:%M')

        return None

    except:
        return None


def export_routes_to_excel(routes_data, filename='optimized_routes.xlsx'):
    """
    Export optimized routes to Excel file

    Args:
        routes_data: Route result from optimization
        filename: Output filename

    Returns:
        BytesIO object with Excel file
    """
    try:
        # Create a BytesIO object
        output = BytesIO()

        # Create Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': [
                    'Total Routes',
                    'Total Stops',
                    'Total Time (min)',
                    'Vehicles Used'
                ],
                'Value': [
                    len(routes_data['routes']),
                    sum(len(r['stops']) for r in routes_data['routes']),
                    routes_data['total_time'],
                    routes_data['num_vehicles_used']
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)

            # Detailed routes sheet
            routes_rows = []
            for route_idx, route in enumerate(routes_data['routes'], 1):
                tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

                for stop_idx, stop_info in enumerate(route['stops'], 1):
                    stop_data = stop_info['stop_data']
                    arrival_min = stop_info['arrival_time']
                    arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                    routes_rows.append({
                        'Route': route_idx,
                        'Technician': tech_name,
                        'Stop Order': stop_idx,
                        'Stop Name': stop_data['name'],
                        'Address': stop_data['address'],
                        'Arrival Time': arrival_time,
                        'Service Duration (min)': stop_info['service_time'],
                        'Latitude': stop_data.get('latitude', ''),
                        'Longitude': stop_data.get('longitude', ''),
                        'Notes': stop_data.get('notes', '')
                    })

            df_routes = pd.DataFrame(routes_rows)
            df_routes.to_excel(writer, sheet_name='Routes', index=False)

            # Individual sheets per technician
            for route_idx, route in enumerate(routes_data['routes'], 1):
                tech_name = route['technician']['name'] if route['technician'] else f"Vehicle {route['vehicle_id']}"

                # Clean sheet name (Excel has 31 char limit and restricted characters)
                sheet_name = tech_name[:30].replace('/', '-').replace('\\', '-').replace('*', '').replace('?', '')

                tech_rows = []
                for stop_idx, stop_info in enumerate(route['stops'], 1):
                    stop_data = stop_info['stop_data']
                    arrival_min = stop_info['arrival_time']
                    arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

                    tech_rows.append({
                        'Order': stop_idx,
                        'Stop Name': stop_data['name'],
                        'Address': stop_data['address'],
                        'Arrival Time': arrival_time,
                        'Service (min)': stop_info['service_time'],
                        'Customer': stop_data.get('customer_name', ''),
                        'Phone': stop_data.get('customer_phone', ''),
                        'Notes': stop_data.get('notes', '')
                    })

                df_tech = pd.DataFrame(tech_rows)
                df_tech.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        return output

    except Exception as e:
        st.error(f"Error creating Excel file: {str(e)}")
        return None


def create_stops_template_excel():
    """
    Create an Excel template for stops data

    Returns:
        BytesIO object with Excel template
    """
    try:
        output = BytesIO()

        # Create template data
        template_data = {
            'Name': ['ABC Corp', 'XYZ Industries', 'Smith Residence'],
            'Address': [
                '123 Main St, New York, NY 10001',
                '456 Park Ave, New York, NY 10022',
                '789 Broadway, New York, NY 10003'
            ],
            'Latitude': [40.7589, 40.7614, 40.7338],
            'Longitude': [-73.9851, -73.9776, -73.9910],
            'Service Duration': [45, 30, 60],
            'Time Window Start': ['09:00', '10:00', '13:00'],
            'Time Window End': ['12:00', '14:00', '17:00'],
            'Priority': [1, 2, 1],
            'Customer Name': ['John Smith', 'Jane Doe', 'Bob Johnson'],
            'Customer Phone': ['555-0101', '555-0102', '555-0103'],
            'Notes': ['Ring doorbell twice', 'Loading dock in rear', 'Call on arrival']
        }

        df_template = pd.DataFrame(template_data)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_template.to_excel(writer, sheet_name='Stops', index=False)

            # Get the worksheet to format
            workbook = writer.book
            worksheet = writer.sheets['Stops']

            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # Add instructions sheet
            instructions = {
                'Field': [
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
                ],
                'Description': [
                    'Stop name or identifier (REQUIRED)',
                    'Full street address (REQUIRED)',
                    'Latitude coordinate (decimal degrees)',
                    'Longitude coordinate (decimal degrees)',
                    'Service time in minutes (default: 30)',
                    'Earliest arrival time (HH:MM format, e.g., 09:00)',
                    'Latest arrival time (HH:MM format, e.g., 17:00)',
                    'Priority level 1-5 (1=highest, 5=lowest)',
                    'Customer contact name',
                    'Customer phone number',
                    'Special instructions or notes'
                ],
                'Required': [
                    'Yes', 'Yes', 'No*', 'No*', 'No', 'No', 'No', 'No', 'No', 'No', 'No'
                ]
            }

            df_instructions = pd.DataFrame(instructions)
            df_instructions.to_excel(writer, sheet_name='Instructions', index=False)

        output.seek(0)
        return output

    except Exception as e:
        st.error(f"Error creating template: {str(e)}")
        return None


def validate_stops_data(stops):
    """
    Validate imported stops data

    Args:
        stops: List of stop dictionaries

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []

    if not stops:
        return False, ['No stops data found']

    for idx, stop in enumerate(stops, 1):
        # Check required fields
        if not stop.get('name'):
            errors.append(f"Row {idx}: Missing stop name")

        if not stop.get('address'):
            errors.append(f"Row {idx}: Missing address")

        # Validate numeric fields
        if stop.get('latitude') is not None:
            try:
                lat = float(stop['latitude'])
                if not -90 <= lat <= 90:
                    errors.append(f"Row {idx}: Latitude must be between -90 and 90")
            except:
                errors.append(f"Row {idx}: Invalid latitude value")

        if stop.get('longitude') is not None:
            try:
                lng = float(stop['longitude'])
                if not -180 <= lng <= 180:
                    errors.append(f"Row {idx}: Longitude must be between -180 and 180")
            except:
                errors.append(f"Row {idx}: Invalid longitude value")

        # Validate service duration
        try:
            duration = int(stop.get('service_duration', 30))
            if duration <= 0 or duration > 480:
                errors.append(f"Row {idx}: Service duration must be between 1 and 480 minutes")
        except:
            errors.append(f"Row {idx}: Invalid service duration")

        # Validate priority
        try:
            priority = int(stop.get('priority', 1))
            if priority < 1 or priority > 5:
                errors.append(f"Row {idx}: Priority must be between 1 and 5")
        except:
            errors.append(f"Row {idx}: Invalid priority value")

    is_valid = len(errors) == 0
    return is_valid, errors
