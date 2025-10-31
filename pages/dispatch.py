import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.email_dispatch import (
    get_smtp_config, send_route_email, send_bulk_dispatch,
    create_route_email_html, create_ics_calendar_file
)
from utils.outlook_integration import (
    get_graph_config, create_route_calendar_events,
    create_bulk_calendar_events, check_graph_api_status
)

st.set_page_config(page_title="Dispatch Routes", layout="wide")

st.title('📤 Dispatch Routes to Technicians')
st.markdown('Send optimized routes via email and/or Outlook calendar')

# Check if there are optimized routes
if 'optimized_routes' not in st.session_state or not st.session_state.optimized_routes:
    st.warning('⚠️ No optimized routes available for dispatch')
    st.info('Go to the **Operations** page to create optimized routes first.')

    if st.button('🔧 Go to Operations', use_container_width=True):
        st.switch_page('pages/operations.py')

    st.stop()

routes = st.session_state.optimized_routes

# Tabs for different dispatch methods
tab1, tab2, tab3 = st.tabs(['📧 Email Dispatch', '📅 Calendar Dispatch', '📊 Dispatch Status'])

# TAB 1: Email Dispatch
with tab1:
    st.header('Email Dispatch')

    # Check SMTP configuration
    smtp_config = get_smtp_config()

    if not smtp_config:
        st.error('❌ Email dispatch not configured')

        st.info('''
        **To enable email dispatch:**

        Add SMTP settings to your configuration:

        **Option 1: Environment Variables**
        ```bash
        SMTP_SERVER=smtp.gmail.com
        SMTP_PORT=587
        SMTP_USERNAME=your-email@gmail.com
        SMTP_PASSWORD=your-app-password
        SMTP_FROM_NAME=Route Dispatcher
        ```

        **Option 2: Streamlit Secrets**
        ```toml
        [smtp]
        server = "smtp.gmail.com"
        port = 587
        username = "your-email@gmail.com"
        password = "your-app-password"
        from_name = "Route Dispatcher"
        ```

        **Gmail Users:** Use an [App Password](https://support.google.com/accounts/answer/185833)
        ''')

        with st.expander('📖 Setup Instructions'):
            st.markdown('''
            ### Gmail Setup
            1. Enable 2-factor authentication on your Google account
            2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
            3. Generate an app password for "Mail"
            4. Use this password in SMTP_PASSWORD

            ### Other Email Providers
            - **Outlook/Office 365:** smtp.office365.com, port 587
            - **Yahoo:** smtp.mail.yahoo.com, port 587
            - **Custom SMTP:** Contact your email provider
            ''')
    else:
        st.success(f'✅ Email configured: {smtp_config["from_email"]}')

        # Route summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Routes Ready', routes['num_vehicles_used'])
        with col2:
            st.metric('Total Stops', sum(len(r['stops']) for r in routes['routes']))
        with col3:
            st.metric('Total Time', f"{routes['total_time']} min")

        st.divider()

        # Dispatch date
        dispatch_date = st.date_input('Dispatch Date', value=date.today())

        # Select dispatch mode
        col1, col2 = st.columns([2, 1])

        with col1:
            dispatch_mode = st.radio(
                'Dispatch Mode',
                ['Send to All Technicians', 'Send to Selected', 'Test Mode (Send to Me)'],
                help='Choose who should receive the routes'
            )

        with col2:
            include_ics = st.checkbox('Include Calendar File (.ics)', value=True, help='Attach ICS file for easy calendar import')

        # Show technician list
        st.subheader('Recipients')

        tech_list = []
        for idx, route in enumerate(routes['routes'], 1):
            if not route['stops']:
                continue

            tech = route.get('technician')
            if tech:
                tech_list.append({
                    'Route': idx,
                    'Technician': tech['name'],
                    'Email': tech.get('email', 'Not configured'),
                    'Stops': len(route['stops']),
                    'Time': f"{route['total_time']} min"
                })

        if tech_list:
            df_techs = pd.DataFrame(tech_list)
            st.dataframe(df_techs, hide_index=True, use_container_width=True)

            # Selection for "Send to Selected" mode
            selected_indices = []
            if dispatch_mode == 'Send to Selected':
                st.subheader('Select Technicians')
                selected_indices = st.multiselect(
                    'Choose technicians to dispatch to:',
                    options=list(range(len(tech_list))),
                    format_func=lambda x: tech_list[x]['Technician'],
                    default=list(range(len(tech_list)))
                )

            st.divider()

            # Preview email
            with st.expander('📧 Preview Email', expanded=False):
                if tech_list:
                    preview_route = routes['routes'][0]
                    preview_tech = preview_route['technician']
                    preview_html = create_route_email_html(preview_route, preview_tech, str(dispatch_date))

                    st.markdown('**Subject:**')
                    st.code(f"Route Assignment for {dispatch_date} - {len(preview_route['stops'])} Stops")

                    st.markdown('**Email Body:**')
                    st.components.v1.html(preview_html, height=600, scrolling=True)

            # Dispatch button
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                if st.button('📤 Send Emails Now', type='primary', use_container_width=True):
                    # Determine send mode
                    send_to = 'test' if dispatch_mode == 'Test Mode (Send to Me)' else 'technician'

                    # Filter routes if needed
                    routes_to_send = routes

                    if dispatch_mode == 'Send to Selected':
                        filtered_routes = {
                            'routes': [routes['routes'][i] for i in selected_indices if i < len(routes['routes'])],
                            'num_vehicles_used': len(selected_indices),
                            'total_time': sum(routes['routes'][i]['total_time'] for i in selected_indices if i < len(routes['routes'])),
                            'total_distance': sum(routes['routes'][i]['total_distance'] for i in selected_indices if i < len(routes['routes']))
                        }
                        routes_to_send = filtered_routes

                    with st.spinner('Sending emails...'):
                        results = send_bulk_dispatch(routes_to_send, str(dispatch_date), send_to=send_to)

                    # Show results
                    if 'error' in results:
                        st.error(f'❌ Error: {results["error"]}')
                    else:
                        col1, col2 = st.columns(2)

                        with col1:
                            st.metric('✅ Sent Successfully', results['success'])

                        with col2:
                            st.metric('❌ Failed', results['failed'])

                        if results['success'] > 0:
                            st.success(f'🎉 Successfully dispatched {results["success"]} routes!')
                            st.balloons()

                            st.info('Emails sent to: ' + ', '.join(results['emails_sent']))

                        if results['failed'] > 0:
                            st.warning(f'⚠️ {results["failed"]} routes failed to send. Check technician email addresses.')

        else:
            st.warning('No routes with assigned technicians found.')

# TAB 2: Calendar Dispatch
with tab2:
    st.header('Outlook Calendar Dispatch')

    # Check Microsoft Graph configuration
    graph_status = check_graph_api_status()

    if not graph_status['configured']:
        st.error('❌ Microsoft Graph API not configured')

        st.info('''
        **To enable Outlook calendar integration:**

        1. Register an app in Azure Portal
        2. Get Client ID, Client Secret, and Tenant ID
        3. Grant Calendar.ReadWrite permissions
        4. Add configuration to secrets

        **Configuration:**
        ```toml
        [microsoft_graph]
        client_id = "your-client-id"
        client_secret = "your-client-secret"
        tenant_id = "your-tenant-id"
        ```
        ''')

        with st.expander('📖 Azure Setup Instructions'):
            st.markdown('''
            ### Step-by-Step Azure Setup

            1. **Go to Azure Portal** → Azure Active Directory → App registrations
            2. **Click "New registration"**
               - Name: Route Optimizer
               - Supported account types: Single tenant
               - Click Register

            3. **Copy Application (client) ID** - This is your client_id

            4. **Copy Directory (tenant) ID** - This is your tenant_id

            5. **Create Client Secret**
               - Go to "Certificates & secrets"
               - Click "New client secret"
               - Copy the VALUE (not the ID)
               - This is your client_secret

            6. **Grant API Permissions**
               - Go to "API permissions"
               - Click "Add a permission"
               - Choose "Microsoft Graph"
               - Choose "Application permissions"
               - Add: Calendars.ReadWrite
               - Click "Grant admin consent"

            7. **Add to your secrets.toml**
            ''')

    elif not graph_status['accessible']:
        st.error('❌ Microsoft Graph API configured but not accessible')
        st.error(graph_status['message'])
    else:
        st.success('✅ Microsoft Graph API ready')

        # Dispatch options
        calendar_date = st.date_input('Calendar Date', value=date.today(), key='calendar_date')

        st.markdown('''
        **Calendar dispatch creates individual Outlook events for each stop:**
        - Event title: Stop name
        - Location: Customer address
        - Time: Calculated arrival + service duration
        - Reminder: 15 minutes before
        - Category: Route Assignment
        ''')

        # Show routes summary
        st.subheader('Calendar Events to Create')

        calendar_summary = []
        for route in routes['routes']:
            if not route['stops']:
                continue

            tech = route.get('technician')
            if tech and tech.get('email'):
                calendar_summary.append({
                    'Technician': tech['name'],
                    'Email': tech['email'],
                    'Events': len(route['stops']),
                    'Duration': f"{route['total_time']} min"
                })

        if calendar_summary:
            df_calendar = pd.DataFrame(calendar_summary)
            st.dataframe(df_calendar, hide_index=True, use_container_width=True)

            total_events = sum(item['Events'] for item in calendar_summary)
            st.info(f'Total calendar events to create: **{total_events}**')

            st.divider()

            # Clear existing events option
            clear_existing = st.checkbox(
                'Clear existing Route Assignment events for this date first',
                value=False,
                help='Delete any existing route events before creating new ones'
            )

            # Dispatch button
            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                if st.button('📅 Create Calendar Events', type='primary', use_container_width=True):
                    with st.spinner('Creating calendar events...'):
                        results = create_bulk_calendar_events(routes, str(calendar_date))

                    # Show results
                    if 'error' in results:
                        st.error(f'❌ Error: {results["error"]}')
                    else:
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.metric('✅ Events Created', results['success'])

                        with col2:
                            st.metric('❌ Failed', results['failed'])

                        with col3:
                            st.metric('👥 Technicians', results['technicians_processed'])

                        if results['success'] > 0:
                            st.success(f'🎉 Successfully created {results["success"]} calendar events!')
                            st.balloons()

                        if results['failed'] > 0:
                            st.warning(f'⚠️ {results["failed"]} events failed to create.')

                        if results.get('errors'):
                            with st.expander('View Errors'):
                                for error in results['errors']:
                                    st.error(error)

        else:
            st.warning('No routes with technician email addresses found.')

# TAB 3: Dispatch Status
with tab3:
    st.header('Dispatch Status & History')

    st.info('This tab will show dispatch history, acknowledgments, and status tracking (coming in future updates)')

    # Current routes status
    st.subheader('Current Routes')

    status_data = []
    for idx, route in enumerate(routes['routes'], 1):
        if not route['stops']:
            continue

        tech = route.get('technician')
        if tech:
            status_data.append({
                'Route': idx,
                'Technician': tech['name'],
                'Stops': len(route['stops']),
                'Status': '📤 Ready to Dispatch',
                'Email': tech.get('email', 'Not configured'),
                'Last Dispatch': 'Never'
            })

    if status_data:
        df_status = pd.DataFrame(status_data)
        st.dataframe(df_status, hide_index=True, use_container_width=True)

    st.divider()

    # Future features placeholder
    st.subheader('Coming Soon')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('''
        **Dispatch Tracking:**
        - Email delivery confirmation
        - Calendar acceptance status
        - Technician acknowledgment
        - Read receipts
        ''')

    with col2:
        st.markdown('''
        **Dispatch History:**
        - Past dispatch records
        - Resend capability
        - Delivery logs
        - Error tracking
        ''')

# Sidebar info
with st.sidebar:
    st.header('Dispatch Options')

    st.markdown('''
    **Available Methods:**
    - 📧 Email with ICS attachment
    - 📅 Direct Outlook calendar

    **Email Features:**
    - Beautiful HTML formatting
    - Complete route details
    - ICS calendar file
    - Customer information

    **Calendar Features:**
    - Individual events per stop
    - Automatic reminders
    - Location data
    - Category tagging

    **Tips:**
    - Use test mode first
    - Verify technician emails
    - Check spam folders
    - Calendar needs Azure setup
    ''')

    st.divider()

    if smtp_config:
        st.success('✅ Email Ready')
    else:
        st.warning('⚠️ Email Not Configured')

    graph_status = check_graph_api_status()
    if graph_status['accessible']:
        st.success('✅ Calendar Ready')
    else:
        st.warning('⚠️ Calendar Not Configured')
