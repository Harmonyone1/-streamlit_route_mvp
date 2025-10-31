"""
Email dispatch system for sending route assignments to technicians
Supports HTML emails with ICS calendar attachments
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
import os
import streamlit as st
from typing import List, Dict
import io


def get_smtp_config():
    """
    Get SMTP configuration from environment or Streamlit secrets

    Returns:
        Dict with SMTP settings or None
    """
    try:
        # Try Streamlit secrets first
        if hasattr(st, 'secrets') and 'smtp' in st.secrets:
            return {
                'server': st.secrets['smtp']['server'],
                'port': st.secrets['smtp']['port'],
                'username': st.secrets['smtp']['username'],
                'password': st.secrets['smtp']['password'],
                'from_email': st.secrets['smtp'].get('from_email', st.secrets['smtp']['username']),
                'from_name': st.secrets['smtp'].get('from_name', 'Route Optimizer')
            }

        # Try environment variables
        server = os.environ.get('SMTP_SERVER')
        if server:
            return {
                'server': server,
                'port': int(os.environ.get('SMTP_PORT', 587)),
                'username': os.environ.get('SMTP_USERNAME'),
                'password': os.environ.get('SMTP_PASSWORD'),
                'from_email': os.environ.get('SMTP_FROM_EMAIL', os.environ.get('SMTP_USERNAME')),
                'from_name': os.environ.get('SMTP_FROM_NAME', 'Route Optimizer')
            }

        return None

    except Exception as e:
        st.error(f"Error loading SMTP config: {str(e)}")
        return None


def create_route_email_html(route_data, technician_data, route_date):
    """
    Create HTML email content for route dispatch

    Args:
        route_data: Single route dictionary from optimization results
        technician_data: Technician information
        route_date: Date of the route

    Returns:
        HTML string
    """
    tech_name = technician_data.get('name', 'Technician')
    stops = route_data.get('stops', [])

    # Build stops table HTML
    stops_html = ""
    for idx, stop_info in enumerate(stops, 1):
        stop_data = stop_info['stop_data']
        arrival_min = stop_info['arrival_time']
        arrival_time = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"

        stops_html += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 12px; text-align: center; font-weight: bold; color: #2563eb;">{idx}</td>
            <td style="padding: 12px;">
                <strong>{stop_data['name']}</strong><br>
                <span style="color: #666; font-size: 14px;">{stop_data['address']}</span>
            </td>
            <td style="padding: 12px; text-align: center;">{arrival_time}</td>
            <td style="padding: 12px; text-align: center;">{stop_info['service_time']} min</td>
            <td style="padding: 12px;">
                {stop_data.get('customer_name', '')}<br>
                <span style="color: #666; font-size: 14px;">{stop_data.get('customer_phone', '')}</span>
            </td>
            <td style="padding: 12px; font-size: 13px; color: #666;">{stop_data.get('notes', '')}</td>
        </tr>
        """

    # Calculate total time
    total_time = route_data.get('total_time', 0)
    hours = total_time // 60
    minutes = total_time % 60

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Route Assignment</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">

        <!-- Header -->
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 28px;">🚚 Route Assignment</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">{route_date}</p>
        </div>

        <!-- Technician Info -->
        <div style="background: white; padding: 25px; border-left: 4px solid #667eea;">
            <h2 style="margin-top: 0; color: #667eea;">👤 Technician: {tech_name}</h2>
            <div style="display: flex; gap: 30px; flex-wrap: wrap; margin-top: 15px;">
                <div>
                    <span style="color: #666; font-size: 14px;">Total Stops:</span>
                    <strong style="font-size: 20px; color: #667eea; display: block;">{len(stops)}</strong>
                </div>
                <div>
                    <span style="color: #666; font-size: 14px;">Estimated Time:</span>
                    <strong style="font-size: 20px; color: #667eea; display: block;">{hours}h {minutes}m</strong>
                </div>
                <div>
                    <span style="color: #666; font-size: 14px;">Distance:</span>
                    <strong style="font-size: 20px; color: #667eea; display: block;">{route_data.get('total_distance', 0):.1f} mi</strong>
                </div>
            </div>
        </div>

        <!-- Route Details -->
        <div style="background: white; padding: 25px; margin-top: 2px;">
            <h2 style="color: #667eea; margin-top: 0;">📍 Your Route</h2>
            <p style="color: #666; margin-bottom: 20px;">Follow these stops in order for optimal efficiency:</p>

            <table style="width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background: #f8f9fa; border-bottom: 2px solid #667eea;">
                        <th style="padding: 12px; text-align: center;">#</th>
                        <th style="padding: 12px; text-align: left;">Location</th>
                        <th style="padding: 12px; text-align: center;">Arrival</th>
                        <th style="padding: 12px; text-align: center;">Duration</th>
                        <th style="padding: 12px; text-align: left;">Customer</th>
                        <th style="padding: 12px; text-align: left;">Notes</th>
                    </tr>
                </thead>
                <tbody>
                    {stops_html}
                </tbody>
            </table>
        </div>

        <!-- Important Notes -->
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 20px; margin-top: 2px;">
            <h3 style="margin-top: 0; color: #856404;">⚠️ Important Reminders</h3>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Call customers if you're running more than 15 minutes late</li>
                <li>Take photos of completed work for documentation</li>
                <li>Update job status in the system after each stop</li>
                <li>Contact dispatch for any issues or emergencies</li>
            </ul>
        </div>

        <!-- Calendar Note -->
        <div style="background: #d1ecf1; border-left: 4px solid #0c5460; padding: 20px; margin-top: 2px;">
            <h3 style="margin-top: 0; color: #0c5460;">📅 Calendar Attachment</h3>
            <p style="margin: 0;">This email includes a calendar file (.ics). Click it to add these appointments to your calendar automatically.</p>
        </div>

        <!-- Footer -->
        <div style="background: #667eea; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; margin-top: 2px;">
            <p style="margin: 0;">Have a safe and productive day!</p>
            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.8;">Route Optimization Platform</p>
        </div>

        <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
            <p>Generated automatically by Route Optimization Platform</p>
            <p>For support, contact your dispatcher</p>
        </div>
    </body>
    </html>
    """

    return html


def create_ics_calendar_file(route_data, technician_data, route_date):
    """
    Create ICS calendar file for route stops

    Args:
        route_data: Single route dictionary
        technician_data: Technician information
        route_date: Date string (YYYY-MM-DD)

    Returns:
        ICS file content as string
    """
    tech_name = technician_data.get('name', 'Technician')
    stops = route_data.get('stops', [])

    # Parse date
    date_obj = datetime.strptime(route_date, '%Y-%m-%d')

    # Start building ICS file
    ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Route Optimizer//Route Dispatch//EN
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Route Assignment
X-WR-TIMEZONE:America/New_York
X-WR-CALDESC:Optimized route for {tech_name}

""".format(tech_name=tech_name)

    # Add event for each stop
    for idx, stop_info in enumerate(stops, 1):
        stop_data = stop_info['stop_data']
        arrival_min = stop_info['arrival_time']
        service_time = stop_info['service_time']

        # Calculate start and end times
        start_time = date_obj + timedelta(minutes=arrival_min)
        end_time = start_time + timedelta(minutes=service_time)

        # Format for ICS (yyyymmddThhmmss)
        start_str = start_time.strftime('%Y%m%dT%H%M%S')
        end_str = end_time.strftime('%Y%m%dT%H%M%S')
        timestamp = datetime.now().strftime('%Y%m%dT%H%M%SZ')

        # Create unique UID
        uid = f"{route_date}-{idx}-{tech_name.replace(' ', '-')}@routeoptimizer.com"

        # Build description
        description = f"Customer: {stop_data.get('customer_name', 'N/A')}\\n"
        description += f"Phone: {stop_data.get('customer_phone', 'N/A')}\\n"
        if stop_data.get('notes'):
            description += f"Notes: {stop_data['notes']}\\n"
        description += f"\\nStop {idx} of {len(stops)}"

        # Add event
        ics_content += f"""BEGIN:VEVENT
UID:{uid}
DTSTAMP:{timestamp}
DTSTART:{start_str}
DTEND:{end_str}
SUMMARY:Stop {idx}: {stop_data['name']}
LOCATION:{stop_data['address']}
DESCRIPTION:{description}
STATUS:CONFIRMED
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT15M
DESCRIPTION:Reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT

"""

    ics_content += "END:VCALENDAR"

    return ics_content


def send_route_email(to_email, to_name, route_data, technician_data, route_date, smtp_config=None):
    """
    Send route assignment email with calendar attachment

    Args:
        to_email: Recipient email address
        to_name: Recipient name
        route_data: Route dictionary
        technician_data: Technician info
        route_date: Date string
        smtp_config: SMTP configuration dict (optional, will fetch if not provided)

    Returns:
        Boolean success status
    """
    try:
        # Get SMTP config if not provided
        if not smtp_config:
            smtp_config = get_smtp_config()

        if not smtp_config:
            st.error("SMTP not configured. Cannot send email.")
            return False

        # Create message
        msg = MIMEMultipart('mixed')
        msg['From'] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        msg['To'] = f"{to_name} <{to_email}>"
        msg['Subject'] = f"Route Assignment for {route_date} - {len(route_data['stops'])} Stops"

        # Create HTML body
        html_content = create_route_email_html(route_data, technician_data, route_date)
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        # Create and attach ICS file
        ics_content = create_ics_calendar_file(route_data, technician_data, route_date)
        ics_attachment = MIMEBase('text', 'calendar', method='REQUEST', name='route.ics')
        ics_attachment.set_payload(ics_content.encode('utf-8'))
        encoders.encode_base64(ics_attachment)
        ics_attachment.add_header('Content-Disposition', 'attachment', filename='route.ics')
        msg.attach(ics_attachment)

        # Send email
        with smtplib.SMTP(smtp_config['server'], smtp_config['port']) as server:
            server.starttls()
            server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Error sending email to {to_email}: {str(e)}")
        return False


def send_bulk_dispatch(routes_data, route_date, send_to='technician'):
    """
    Send route emails to all technicians

    Args:
        routes_data: Optimization results with multiple routes
        route_date: Date string
        send_to: 'technician' or 'test' (for testing, uses tech email or a test address)

    Returns:
        Dict with success/failure counts
    """
    smtp_config = get_smtp_config()

    if not smtp_config:
        return {'success': 0, 'failed': 0, 'error': 'SMTP not configured'}

    results = {
        'success': 0,
        'failed': 0,
        'emails_sent': []
    }

    for route in routes_data['routes']:
        if not route['stops']:
            continue

        tech = route.get('technician')
        if not tech:
            results['failed'] += 1
            continue

        # Get email address
        if send_to == 'test':
            # For testing, use a test email from config
            to_email = os.environ.get('TEST_EMAIL', smtp_config['from_email'])
            to_name = f"TEST - {tech['name']}"
        else:
            to_email = tech.get('email')
            to_name = tech['name']

        if not to_email:
            results['failed'] += 1
            continue

        # Send email
        success = send_route_email(to_email, to_name, route, tech, route_date, smtp_config)

        if success:
            results['success'] += 1
            results['emails_sent'].append(to_email)
        else:
            results['failed'] += 1

    return results

