import streamlit as st
import pandas as pd
import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.supabase_client import get_supabase_client, create_stop, get_all_stops
from utils.excel_integration import (
    parse_excel_stops, export_routes_to_excel,
    create_stops_template_excel, validate_stops_data
)
from utils.sheets_integration import (
    get_google_sheets_client, read_stops_from_sheet,
    write_routes_to_sheet, create_stops_template_sheet,
    sync_stops_bidirectional
)

st.set_page_config(page_title="Import / Export", layout="wide")

st.title('📥📤 Import / Export Data')
st.markdown('Import stops from Excel/Google Sheets or export optimized routes')

# Initialize clients
supabase_client = get_supabase_client()

# Tabs for different operations
tab1, tab2, tab3, tab4 = st.tabs([
    '📥 Import from Excel',
    '📊 Import from Google Sheets',
    '📤 Export Routes',
    '📋 Templates'
])

# TAB 1: Import from Excel
with tab1:
    st.header('Import Stops from Excel')

    st.info('''
    Upload an Excel file (.xlsx or .xls) with stop information.
    The file should have columns: Name, Address, Latitude, Longitude, Service Duration, etc.
    ''')

    uploaded_file = st.file_uploader(
        'Choose Excel file',
        type=['xlsx', 'xls'],
        help='Upload an Excel file with stops data'
    )

    if uploaded_file:
        st.success(f'File uploaded: {uploaded_file.name}')

        # Parse the file
        with st.spinner('Parsing Excel file...'):
            stops = parse_excel_stops(uploaded_file)

        if stops:
            st.success(f'✅ Successfully parsed {len(stops)} stops from Excel')

            # Validate data
            is_valid, errors = validate_stops_data(stops)

            if not is_valid:
                st.warning(f'⚠️ Found {len(errors)} validation errors:')
                for error in errors[:10]:  # Show first 10 errors
                    st.error(error)
                if len(errors) > 10:
                    st.info(f'...and {len(errors) - 10} more errors')

            # Preview data
            st.subheader('Preview Data')
            df = pd.DataFrame(stops)
            display_cols = ['name', 'address', 'latitude', 'longitude', 'service_duration', 'time_window_start', 'time_window_end']
            display_cols = [col for col in display_cols if col in df.columns]
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

            st.divider()

            # Import options
            col1, col2, col3 = st.columns(3)

            with col1:
                import_mode = st.radio(
                    'Import Mode',
                    ['Add to existing', 'Replace all stops'],
                    help='Choose whether to add these stops to existing ones or replace all'
                )

            with col2:
                skip_geocoded = st.checkbox(
                    'Skip stops without coordinates',
                    value=False,
                    help='Only import stops that have latitude and longitude'
                )

            with col3:
                st.metric('Stops to Import', len(stops))

            st.divider()

            # Import button
            if st.button('🚀 Import to Database', type='primary', use_container_width=True):
                if not supabase_client:
                    st.error('❌ Cannot connect to database. Check your Supabase configuration.')
                else:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    imported = 0
                    skipped = 0
                    failed = 0

                    for idx, stop in enumerate(stops):
                        # Update progress
                        progress = (idx + 1) / len(stops)
                        progress_bar.progress(progress)
                        status_text.text(f'Importing stop {idx + 1} of {len(stops)}: {stop["name"]}')

                        # Skip if no coordinates and option is set
                        if skip_geocoded and (not stop.get('latitude') or not stop.get('longitude')):
                            skipped += 1
                            continue

                        # Import to database
                        result = create_stop(supabase_client, stop)

                        if result:
                            imported += 1
                        else:
                            failed += 1

                    progress_bar.empty()
                    status_text.empty()

                    # Show results
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric('✅ Imported', imported)
                    with col2:
                        st.metric('⏭️ Skipped', skipped)
                    with col3:
                        st.metric('❌ Failed', failed)

                    if imported > 0:
                        st.success(f'🎉 Successfully imported {imported} stops!')
                    if failed > 0:
                        st.warning(f'⚠️ {failed} stops failed to import (possible duplicates or database errors)')

        else:
            st.error('❌ Failed to parse Excel file. Please check the file format.')

# TAB 2: Import from Google Sheets
with tab2:
    st.header('Import Stops from Google Sheets')

    # Check if Google Sheets is configured
    sheets_client = get_google_sheets_client()

    if not sheets_client:
        st.warning('⚠️ Google Sheets integration not configured')

        st.info('''
        **To enable Google Sheets integration:**

        1. Create a Google Cloud Project
        2. Enable Google Sheets API and Google Drive API
        3. Create a Service Account
        4. Download the JSON credentials file
        5. Add credentials to Streamlit secrets or environment variables

        See documentation for detailed setup instructions.
        ''')

        with st.expander('📖 Quick Setup Guide'):
            st.markdown('''
            ```toml
            # Add to .streamlit/secrets.toml
            [gcp_service_account]
            type = "service_account"
            project_id = "your-project-id"
            private_key_id = "key-id"
            private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
            client_email = "your-service-account@project.iam.gserviceaccount.com"
            client_id = "client-id"
            auth_uri = "https://accounts.google.com/o/oauth2/auth"
            token_uri = "https://oauth2.googleapis.com/token"
            auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
            client_x509_cert_url = "cert-url"
            ```
            ''')
    else:
        st.success('✅ Google Sheets client connected')

        st.info('Enter the URL or ID of your Google Sheet. Make sure the service account has access to the sheet.')

        sheet_url = st.text_input(
            'Google Sheet URL or ID',
            placeholder='https://docs.google.com/spreadsheets/d/...',
            help='Paste the full URL or just the spreadsheet ID'
        )

        worksheet_name = st.text_input(
            'Worksheet Name',
            value='Stops',
            help='Name of the worksheet/tab containing stops data'
        )

        if sheet_url and st.button('📥 Import from Google Sheets', type='primary'):
            with st.spinner('Reading from Google Sheets...'):
                stops = read_stops_from_sheet(sheets_client, sheet_url, worksheet_name)

            if stops:
                st.success(f'✅ Successfully read {len(stops)} stops from Google Sheets')

                # Preview
                df = pd.DataFrame(stops)
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Import to database
                if st.button('💾 Save to Database'):
                    if not supabase_client:
                        st.error('Cannot connect to database')
                    else:
                        imported = 0
                        for stop in stops:
                            result = create_stop(supabase_client, stop)
                            if result:
                                imported += 1

                        st.success(f'Imported {imported} stops to database!')
            else:
                st.error('Failed to read from Google Sheets. Check the URL and permissions.')

        st.divider()

        # Sync feature
        st.subheader('🔄 Bidirectional Sync')

        st.info('Keep your Google Sheet and database in sync automatically')

        sync_sheet_url = st.text_input(
            'Sheet URL for Sync',
            placeholder='https://docs.google.com/spreadsheets/d/...',
            key='sync_url'
        )

        sync_direction = st.radio(
            'Sync Direction',
            ['Sheet → Database', 'Database → Sheet', 'Both Ways'],
            help='Choose sync direction'
        )

        direction_map = {
            'Sheet → Database': 'sheet_to_db',
            'Database → Sheet': 'db_to_sheet',
            'Both Ways': 'both'
        }

        if sync_sheet_url and st.button('🔄 Sync Now'):
            if not supabase_client:
                st.error('Cannot connect to database')
            else:
                with st.spinner('Syncing...'):
                    results = sync_stops_bidirectional(
                        sheets_client,
                        sync_sheet_url,
                        supabase_client,
                        direction=direction_map[sync_direction]
                    )

                if results['success']:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric('Imported', results['imported'])
                    with col2:
                        st.metric('Exported', results['exported'])

                    st.success('✅ Sync completed successfully!')
                else:
                    st.error('Sync failed. Check error messages.')
                    for error in results['errors']:
                        st.error(error)

# TAB 3: Export Routes
with tab3:
    st.header('Export Optimized Routes')

    # Check if there are routes in session state
    if 'optimized_routes' not in st.session_state or not st.session_state.optimized_routes:
        st.warning('⚠️ No optimized routes available to export')
        st.info('Go to the **Operations** page to create optimized routes first.')

        if st.button('🔧 Go to Operations'):
            st.switch_page('pages/operations.py')
    else:
        routes = st.session_state.optimized_routes

        st.success(f'✅ Ready to export {routes["num_vehicles_used"]} routes')

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric('Routes', routes['num_vehicles_used'])
        with col2:
            st.metric('Total Stops', sum(len(r['stops']) for r in routes['routes']))
        with col3:
            st.metric('Total Time', f"{routes['total_time']} min")

        st.divider()

        # Export options
        col1, col2 = st.columns(2)

        with col1:
            st.subheader('📥 Export to Excel')

            export_date = st.date_input('Route Date', value=date.today())

            if st.button('📥 Download Excel File', type='primary', use_container_width=True):
                excel_file = export_routes_to_excel(routes)

                if excel_file:
                    filename = f'routes_{export_date.strftime("%Y%m%d")}.xlsx'

                    st.download_button(
                        label='💾 Download Excel',
                        data=excel_file,
                        file_name=filename,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        use_container_width=True
                    )

                    st.success('✅ Excel file ready for download!')

        with col2:
            st.subheader('📊 Export to Google Sheets')

            sheets_client_export = get_google_sheets_client()

            if not sheets_client_export:
                st.warning('Google Sheets not configured')
            else:
                export_sheet_url = st.text_input(
                    'Google Sheet URL',
                    placeholder='https://docs.google.com/spreadsheets/d/...',
                    key='export_sheet_url'
                )

                export_worksheet_name = st.text_input(
                    'Worksheet Name',
                    value='Optimized Routes',
                    key='export_worksheet'
                )

                if export_sheet_url and st.button('📤 Export to Google Sheets', use_container_width=True):
                    with st.spinner('Writing to Google Sheets...'):
                        success = write_routes_to_sheet(
                            sheets_client_export,
                            export_sheet_url,
                            routes,
                            export_worksheet_name
                        )

                    if success:
                        st.success('✅ Routes exported to Google Sheets!')
                        st.markdown(f'[Open Sheet]({export_sheet_url})')
                    else:
                        st.error('❌ Failed to export to Google Sheets')

# TAB 4: Templates
with tab4:
    st.header('📋 Download Templates')

    st.info('''
    Download template files to get started with importing stops.
    Templates include sample data and format guidelines.
    ''')

    col1, col2 = st.columns(2)

    with col1:
        st.subheader('Excel Template')
        st.markdown('''
        Download an Excel template with:
        - Proper column headers
        - Sample data
        - Format instructions
        ''')

        if st.button('📥 Download Excel Template', use_container_width=True):
            template = create_stops_template_excel()

            if template:
                st.download_button(
                    label='💾 Save Template',
                    data=template,
                    file_name='stops_template.xlsx',
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    use_container_width=True
                )

    with col2:
        st.subheader('Google Sheets Template')
        st.markdown('''
        Create a new Google Sheet with:
        - Pre-configured columns
        - Sample data
        - Ready to use
        ''')

        sheets_client_template = get_google_sheets_client()

        if not sheets_client_template:
            st.warning('Google Sheets not configured')
        else:
            if st.button('📊 Create Google Sheet Template', use_container_width=True):
                with st.spinner('Creating template...'):
                    sheet_url = create_stops_template_sheet(sheets_client_template)

                if sheet_url:
                    st.success('✅ Template created!')
                    st.markdown(f'**[Open Template]({sheet_url})**')
                    st.info('The template is now ready to use. Share it with your team!')
                else:
                    st.error('Failed to create template')

    st.divider()

    # Format reference
    st.subheader('📖 Field Reference')

    format_data = {
        'Field Name': [
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
        'Type': [
            'Text',
            'Text',
            'Number',
            'Number',
            'Number',
            'Time (HH:MM)',
            'Time (HH:MM)',
            'Number (1-5)',
            'Text',
            'Text',
            'Text'
        ],
        'Required': [
            'Yes ✓',
            'Yes ✓',
            'No*',
            'No*',
            'No',
            'No',
            'No',
            'No',
            'No',
            'No',
            'No'
        ],
        'Example': [
            'ABC Corp',
            '123 Main St, City, ST 12345',
            '40.7589',
            '-73.9851',
            '45',
            '09:00',
            '17:00',
            '1',
            'John Smith',
            '555-0101',
            'Ring doorbell twice'
        ]
    }

    df_format = pd.DataFrame(format_data)
    st.dataframe(df_format, use_container_width=True, hide_index=True)

    st.caption('* Latitude and Longitude are optional but recommended for accurate route optimization')

# Sidebar info
with st.sidebar:
    st.header('Import / Export Help')

    st.markdown('''
    **Supported Formats:**
    - Excel (.xlsx, .xls)
    - Google Sheets
    - CSV (coming soon)

    **Quick Tips:**
    - Use templates for correct format
    - Include lat/lng for best results
    - Validate data before import
    - Backup before replacing stops

    **Need Help?**
    Check the documentation or use the templates provided.
    ''')
