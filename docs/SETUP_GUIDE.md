# Setup Guide - Route Optimization Platform

Complete setup instructions for deploying the Route Optimization Platform.

## Prerequisites

- Python 3.8 or higher
- Supabase account (free tier available)
- Git (for deployment)
- Optional: Google Maps API key (for real distance calculations)

## Step 1: Clone and Install

```bash
# Clone the repository
cd streamlit_route_mvp

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Supabase Setup

### 2.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Sign up or log in
3. Click "New Project"
4. Fill in project details
5. Wait for project to be created (~2 minutes)

### 2.2 Get Your Credentials

1. In your Supabase project dashboard
2. Go to **Settings** → **API**
3. Copy:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon/public key** (long string starting with `eyJ...`)

### 2.3 Create Database Tables

1. In Supabase, go to **SQL Editor**
2. Open the file `docs/database_schema.sql`
3. Copy the entire SQL content
4. Paste into the SQL Editor
5. Click **Run** to create all tables

## Step 3: Configure Application

### Option A: Using .env File (Local Development)

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your credentials
SUPABASE_URL=https://your-project-url.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### Option B: Using Streamlit Secrets (Deployment)

Create file: `.streamlit/secrets.toml`

```toml
[supabase]
url = "https://your-project-url.supabase.co"
key = "your-supabase-anon-key"
```

## Step 4: Add Sample Data (Optional)

### Add Sample Technicians

In Supabase SQL Editor, run:

```sql
INSERT INTO technicians (name, email, phone, skills) VALUES
    ('John Smith', 'john@company.com', '555-0101', ARRAY['HVAC', 'Plumbing']),
    ('Jane Doe', 'jane@company.com', '555-0102', ARRAY['Electrical', 'HVAC']),
    ('Bob Johnson', 'bob@company.com', '555-0103', ARRAY['Plumbing', 'General']);
```

### Add Sample Stops

In Supabase SQL Editor, run:

```sql
INSERT INTO stops (name, address, latitude, longitude, service_duration, time_window_start, time_window_end) VALUES
    ('ABC Corp', '123 Main St, New York, NY 10001', 40.7589, -73.9851, 45, '09:00', '12:00'),
    ('XYZ Industries', '456 Park Ave, New York, NY 10022', 40.7614, -73.9776, 30, '10:00', '14:00'),
    ('Smith Residence', '789 Broadway, New York, NY 10003', 40.7338, -73.9910, 60, '13:00', '17:00');
```

## Step 5: Run the Application

### Local Development

```bash
# Make sure virtual environment is activated
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

### Using Streamlit Cloud

1. Push code to GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repository
5. Main file: `main.py`
6. Add secrets in Streamlit Cloud dashboard
7. Deploy!

## Step 6: Test the Platform

1. **Visit Home Page** - Check system status indicators
2. **Go to Operations** - Add a few stops using the sidebar form
3. **Optimize Routes** - Select technicians and click "Optimize Routes"
4. **View Results** - Check the map and route details tabs
5. **Visit Dashboard** - See route overview

## Troubleshooting

### Supabase Connection Error

- Verify your URL and key are correct
- Check if you're using the **anon/public** key, not the service role key
- Ensure database tables are created

### No Routes Generated

- Make sure technicians exist in the database
- Ensure stops have valid latitude/longitude values
- Check that stops have time windows within work hours (8 AM - 5 PM default)

### Map Not Showing

- Verify stops have latitude and longitude values
- Check browser console for JavaScript errors
- Ensure `streamlit-folium` is installed

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

## Advanced Configuration

### Google Maps Distance Matrix API

For real driving distances instead of Euclidean approximation:

1. Get API key from [Google Cloud Console](https://console.cloud.google.com)
2. Enable "Distance Matrix API"
3. Add to `.env`:
   ```
   GOOGLE_MAPS_API_KEY=your-api-key
   ```
4. Modify `utils/optimization.py` to use the API

### Email Dispatch

Configure SMTP for email notifications:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Microsoft Outlook Calendar

For calendar integration:

1. Register app in Azure Portal
2. Get Client ID, Secret, and Tenant ID
3. Add to `.env`
4. Implement in `utils/email_dispatch.py`

## Next Steps

- Explore the **Operations** page to create routes
- Check **Dashboard** for route overview
- Customize optimization parameters
- Add real addresses with geocoding
- Implement dispatch features (Phase 3)
- Add reporting and analytics (Phase 5)

## Support

For issues or questions:
- Check `docs/architecture.md` for system overview
- Review `docs/database_schema.sql` for data structure
- See original plan in project root

## Security Notes

- Never commit `.env` or `secrets.toml` to Git
- Use Row Level Security (RLS) in Supabase for production
- Rotate API keys regularly
- Use service accounts for automation
