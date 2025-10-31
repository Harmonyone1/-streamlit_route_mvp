# Phase 2 Setup Guide - Google Sheets & Excel Integration

This guide covers setting up Google Sheets integration and using the import/export features.

## Overview

Phase 2 adds the ability to:
- Import stops from Excel files
- Import stops from Google Sheets
- Export optimized routes to Excel
- Export optimized routes to Google Sheets
- Sync bidirectionally with Google Sheets
- Use template files for easy setup

## Excel Integration (No Setup Required)

Excel import/export works out of the box! No configuration needed.

### Import Stops from Excel

1. Go to **Import/Export** page
2. Click "Import from Excel" tab
3. Upload your .xlsx or .xls file
4. Review the parsed data
5. Click "Import to Database"

### Export Routes to Excel

1. Optimize routes in **Operations** page
2. Go to **Import/Export** page
3. Click "Export Routes" tab
4. Click "Download Excel File"
5. Save the multi-sheet workbook with:
   - Summary sheet
   - All routes combined
   - Individual sheets per technician

### Create Sample Data

Run the included script to generate sample data:

```bash
python create_sample_data.py
```

This creates `data/sample_data.xlsx` with 10 sample stops.

## Google Sheets Integration Setup

Google Sheets requires a Google Cloud service account. Follow these steps:

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Note your Project ID

### Step 2: Enable Required APIs

1. In Google Cloud Console, go to "APIs & Services" → "Library"
2. Search for and enable:
   - **Google Sheets API**
   - **Google Drive API**

### Step 3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in details:
   - Name: `route-optimizer-service`
   - Description: "Service account for route optimization platform"
4. Click "Create and Continue"
5. Skip role assignment (click "Continue")
6. Skip user access (click "Done")

### Step 4: Generate Credentials Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose **JSON** format
5. Click "Create"
6. A JSON file will download - **keep this secure!**

### Step 5: Add Credentials to Your App

#### Option A: For Local Development

Create `credentials/google_service_account.json` file:

```bash
mkdir credentials
# Copy your downloaded JSON file to:
cp ~/Downloads/your-project-*.json credentials/google_service_account.json
```

Add to `.gitignore`:
```
credentials/
```

#### Option B: For Streamlit Cloud Deployment

Add to `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id-here"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-PRIVATE-KEY-HERE\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project-id.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
```

**Note:** Copy values from your downloaded JSON file.

#### Option C: Environment Variable

```bash
export GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account","project_id":"...","private_key":"..."}'
```

### Step 6: Share Your Google Sheet

For the service account to access your Google Sheets:

1. Open your Google Sheet
2. Click "Share"
3. Paste the service account email (from JSON: `client_email`)
   - Example: `route-optimizer-service@your-project.iam.gserviceaccount.com`
4. Grant "Editor" permissions
5. Uncheck "Notify people" (it's a service account, not a person)
6. Click "Share"

Now the app can read and write to this sheet!

## Using Google Sheets

### Import from Google Sheets

1. Create or open a Google Sheet
2. Format with required columns:
   - Name
   - Address
   - Latitude
   - Longitude
   - Service Duration
   - Time Window Start
   - Time Window End
   - Priority
   - Customer Name
   - Customer Phone
   - Notes

3. Share with service account (see Step 6 above)
4. In app, go to **Import/Export** → "Import from Google Sheets"
5. Paste the sheet URL
6. Enter worksheet name (default: "Stops")
7. Click "Import from Google Sheets"
8. Review data and click "Save to Database"

### Export to Google Sheets

1. Optimize routes in **Operations** page
2. Go to **Import/Export** → "Export Routes"
3. Enter your Google Sheet URL
4. Enter worksheet name for output
5. Click "Export to Google Sheets"
6. Open your sheet to see optimized routes!

### Bidirectional Sync

Keep your sheet and database in sync:

1. Go to **Import/Export** → "Import from Google Sheets"
2. Scroll to "Bidirectional Sync" section
3. Enter sheet URL
4. Choose sync direction:
   - **Sheet → Database**: Import from sheet
   - **Database → Sheet**: Export to sheet
   - **Both Ways**: Sync bidirectionally
5. Click "Sync Now"

## Template Files

### Download Excel Template

1. Go to **Import/Export** → "Templates" tab
2. Click "Download Excel Template"
3. Open in Excel or Google Sheets
4. Fill in your data
5. Import back into the app

### Create Google Sheets Template

1. Ensure Google Sheets is configured (see setup above)
2. Go to **Import/Export** → "Templates" tab
3. Click "Create Google Sheet Template"
4. A new sheet will be created with:
   - Proper column headers
   - Sample data
   - Ready to use
5. Click the link to open
6. Share with your team
7. Start adding stops!

## Field Reference

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| Name | Text | Yes | Stop name or identifier | ABC Corp |
| Address | Text | Yes | Full street address | 123 Main St, City, ST 12345 |
| Latitude | Number | No* | Latitude coordinate (-90 to 90) | 40.7589 |
| Longitude | Number | No* | Longitude coordinate (-180 to 180) | -73.9851 |
| Service Duration | Number | No | Service time in minutes (default: 30) | 45 |
| Time Window Start | Time | No | Earliest arrival (HH:MM) | 09:00 |
| Time Window End | Time | No | Latest arrival (HH:MM) | 17:00 |
| Priority | Number | No | Priority 1-5 (1=highest) | 1 |
| Customer Name | Text | No | Customer contact name | John Smith |
| Customer Phone | Text | No | Customer phone number | 555-0101 |
| Notes | Text | No | Special instructions | Ring doorbell twice |

*Latitude/Longitude recommended for accurate routing

## Workflows

### Workflow 1: Weekly Schedule via Excel

1. Download Excel template
2. Fill with week's stops
3. Import to database
4. Optimize routes
5. Export results to Excel
6. Distribute to technicians

### Workflow 2: Daily Sync with Google Sheets

1. Office manager updates Google Sheet daily
2. Run sync before optimization
3. Optimize routes in app
4. Export back to Google Sheet
5. Technicians check sheet for updates

### Workflow 3: Hybrid Approach

1. Import bulk stops from Excel (one-time)
2. Add ad-hoc stops via app interface
3. Daily sync with Google Sheet for changes
4. Export optimized routes to both formats

## Troubleshooting

### Google Sheets Errors

**Error: "Google Sheets client not connected"**
- Check that credentials JSON is properly configured
- Verify all required fields are in secrets.toml
- Ensure private key includes newline characters (`\n`)

**Error: "Permission denied"**
- Share the Google Sheet with service account email
- Grant "Editor" permissions
- Check that APIs are enabled in Google Cloud Console

**Error: "Worksheet not found"**
- Verify worksheet name is correct (case-sensitive)
- Default worksheet is usually "Sheet1" or "Stops"

### Excel Import Errors

**Error: "Failed to parse Excel file"**
- Ensure file is .xlsx or .xls format
- Check that first row contains headers
- Verify Name and Address columns exist

**Validation errors**
- Check latitude is between -90 and 90
- Check longitude is between -180 and 180
- Ensure service duration is positive number
- Verify time format is HH:MM (e.g., 09:00)

## Security Best Practices

1. **Never commit credentials to Git**
   - Add `credentials/` to `.gitignore`
   - Never share your JSON key file

2. **Use environment-specific credentials**
   - Different service accounts for dev/prod
   - Rotate keys periodically

3. **Limit service account permissions**
   - Only grant access to specific sheets
   - Use "Editor" not "Owner" role

4. **Store secrets securely**
   - Use Streamlit secrets for deployment
   - Use environment variables locally
   - Never hardcode in source code

## Next Steps

After Phase 2 setup:
- Import your actual stops data
- Test the import/export workflow
- Set up regular syncs with Google Sheets
- Train team on using templates
- Move to Phase 3: Dispatch features

## Support

For issues:
- Check Google Cloud Console for API errors
- Verify service account email in sheet sharing
- Review Streamlit logs for error messages
- Ensure required Python packages installed

## Dependencies

Phase 2 requires these additional packages (already in requirements.txt):
```
gspread
google-auth
google-auth-oauthlib
google-auth-httplib2
xlrd
openpyxl (already included)
```

Install with:
```bash
pip install -r requirements.txt
```
