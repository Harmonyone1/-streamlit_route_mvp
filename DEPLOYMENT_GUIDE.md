# Deployment Guide - Streamlit Cloud

Complete step-by-step guide to deploy your Route Optimization Platform to Streamlit Cloud.

## Prerequisites

- [x] GitHub account (free)
- [x] Streamlit Cloud account (free - sign up at share.streamlit.io)
- [x] Supabase project URL and API key
- [x] Git installed on your computer

## Step 1: Initialize Git Repository

Open your terminal in the project directory and run:

```bash
cd "D:\streamlit_route_mvp"

# Initialize git repository
git init

# Check current status
git status
```

## Step 2: Create GitHub Repository

1. **Go to GitHub** → https://github.com
2. Click **"+"** in top right → **"New repository"**
3. **Repository name:** `route-optimizer` (or your preferred name)
4. **Description:** "Route Optimization Platform for field service operations"
5. **Visibility:** Choose Private or Public
6. **DO NOT** initialize with README, .gitignore, or license (we have these)
7. Click **"Create repository"**

## Step 3: Push Code to GitHub

Copy the commands from GitHub (they'll look like this):

```bash
# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Route Optimization Platform with 3 phases complete"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/route-optimizer.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**Alternative if using SSH:**
```bash
git remote add origin git@github.com:YOUR_USERNAME/route-optimizer.git
git push -u origin main
```

## Step 4: Sign Up for Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Click **"Sign up"** or **"Sign in"**
3. **Sign in with GitHub**
4. Authorize Streamlit Cloud to access your GitHub

## Step 5: Deploy App

1. Click **"New app"** button
2. Fill in deployment settings:

   **Repository:** Select `YOUR_USERNAME/route-optimizer`

   **Branch:** `main`

   **Main file path:** `main.py`

   **App URL (optional):** Choose a custom subdomain like `your-company-routes`
   - Will be: `your-company-routes.streamlit.app`

3. Click **"Advanced settings"** (IMPORTANT!)

## Step 6: Configure Secrets

In the Advanced settings, add your secrets in TOML format:

```toml
# Supabase Configuration (REQUIRED)
[supabase]
url = "https://syrrhunexglfceovmdrd.supabase.co"
key = "your-supabase-anon-key-here"

# SMTP Configuration (Optional - for email dispatch)
[smtp]
server = "smtp.gmail.com"
port = 587
username = "your-email@gmail.com"
password = "your-app-password-here"
from_name = "Route Dispatcher"

# Google Sheets Configuration (Optional - for Phase 2)
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR-KEY-HERE\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "your-cert-url"

# Microsoft Graph Configuration (Optional - for Outlook calendars)
[microsoft_graph]
client_id = "your-azure-client-id"
client_secret = "your-azure-client-secret"
tenant_id = "your-azure-tenant-id"
```

**Minimum Required (to get started):**
```toml
[supabase]
url = "https://syrrhunexglfceovmdrd.supabase.co"
key = "your-supabase-anon-key-here"
```

## Step 7: Get Your Supabase Key

1. Go to your **Supabase Project** → https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **API**
4. Copy the **"anon/public"** key (NOT the service_role key!)
5. Paste it in the secrets configuration above

## Step 8: Deploy!

1. After adding secrets, click **"Deploy"**
2. Streamlit will:
   - Clone your repository
   - Install dependencies from requirements.txt
   - Start the app
   - Give you a live URL

**Deployment takes 2-5 minutes**

## Step 9: Set Up Database

Your app is now live, but you need to create the database tables:

1. Go to **Supabase** → **SQL Editor**
2. Open the file `docs/database_schema.sql` from your project
3. Copy ALL the SQL
4. Paste into Supabase SQL Editor
5. Click **"Run"**
6. Verify tables created: Go to **Table Editor**

You should see these tables:
- users
- technicians
- stops
- routes
- route_stops
- optimization_history
- dispatch_log

## Step 10: Add Sample Data

In Supabase SQL Editor, run:

```sql
-- Add sample technicians
INSERT INTO technicians (name, email, phone, skills) VALUES
    ('John Smith', 'john@company.com', '555-0101', ARRAY['HVAC', 'Plumbing']),
    ('Jane Doe', 'jane@company.com', '555-0102', ARRAY['Electrical', 'HVAC']),
    ('Bob Johnson', 'bob@company.com', '555-0103', ARRAY['Plumbing', 'General']);

-- Add sample stops (New York City locations)
INSERT INTO stops (name, address, latitude, longitude, service_duration, time_window_start, time_window_end, priority, customer_name, customer_phone) VALUES
    ('ABC Corp', '123 Main St, New York, NY 10001', 40.7589, -73.9851, 45, '09:00', '12:00', 1, 'John Smith', '555-0101'),
    ('XYZ Industries', '456 Park Ave, New York, NY 10022', 40.7614, -73.9776, 30, '10:00', '14:00', 2, 'Jane Doe', '555-0102'),
    ('Smith Residence', '789 Broadway, New York, NY 10003', 40.7338, -73.9910, 60, '13:00', '17:00', 1, 'Bob Johnson', '555-0103'),
    ('Johnson Office', '321 5th Avenue, New York, NY 10016', 40.7452, -73.9820, 30, '09:00', '12:00', 3, 'Alice Williams', '555-0104'),
    ('Downtown Mall', '555 Madison Ave, New York, NY 10022', 40.7614, -73.9776, 45, '11:00', '15:00', 2, 'Charlie Brown', '555-0105');
```

## Step 11: Test Your Deployed App

1. **Open your app URL** → `https://your-app-name.streamlit.app`

2. **Test Core Features:**
   - ✅ Home page loads
   - ✅ Dashboard shows (may be empty initially)
   - ✅ Operations page opens
   - ✅ Can view stops
   - ✅ Can optimize routes
   - ✅ Map displays

3. **Test Optimization:**
   - Go to Operations → Optimization tab
   - Should see your sample technicians and stops
   - Click "Optimize Routes"
   - View results on map

4. **Test Other Features:**
   - Import/Export page
   - Dispatch page (if SMTP configured)
   - Technician view

## Step 12: Update Secrets Later (Optional)

To add more configurations later:

1. Go to **Streamlit Cloud Dashboard** → https://share.streamlit.io
2. Click on your app
3. Click **"⚙️ Settings"**
4. Go to **"Secrets"**
5. Edit the TOML configuration
6. Click **"Save"**
7. App will automatically restart

## Troubleshooting

### App Won't Start

**Check logs:**
1. In Streamlit Cloud dashboard
2. Click your app
3. View the logs in the bottom panel
4. Look for error messages

**Common issues:**
- Missing secrets → Add Supabase credentials
- Wrong Python version → Should auto-detect
- Missing dependencies → Check requirements.txt

### Database Connection Failed

- Verify Supabase URL is correct
- Verify you're using the **anon/public** key (not service_role)
- Check that tables exist (run schema SQL)
- Ensure Supabase project is active

### Import Errors

- Make sure all files pushed to GitHub
- Check requirements.txt is complete
- Verify Python 3.8+ compatibility

### Map Not Showing

- Check browser console for errors
- Verify stops have latitude/longitude
- Ensure internet connection (needs map tiles)

### Slow Performance

- Streamlit Cloud free tier has resource limits
- Consider upgrading for production use
- Optimize large datasets

## Production Recommendations

### 1. Custom Domain (Optional)

Streamlit Cloud supports custom domains:
1. Get a domain from your provider
2. Add CNAME record pointing to Streamlit
3. Configure in app settings

### 2. Enable Authentication (Future)

Consider adding:
- Email/password auth
- Google SSO
- Microsoft SSO
- Role-based access

### 3. Monitoring

Set up:
- Error tracking
- Usage analytics
- Performance monitoring
- Uptime alerts

### 4. Backups

- Regular Supabase database backups
- Export configurations
- Document setup

### 5. Security

- Use environment variables for secrets
- Enable Row Level Security in Supabase
- Set up proper CORS
- Use HTTPS (automatic with Streamlit Cloud)

## Updating Your Deployed App

When you make changes:

```bash
# Make your changes to code
# Then commit and push:

git add .
git commit -m "Description of changes"
git push

# Streamlit Cloud will auto-deploy the changes!
```

**Auto-deployment happens within 1-2 minutes of pushing to GitHub**

## Sharing Your App

Once deployed, share your URL:
- `https://your-app-name.streamlit.app`

**For team access:**
1. Share the URL
2. Consider adding password protection (Streamlit setting)
3. Train users on features

## Cost

**Streamlit Cloud Free Tier:**
- ✅ Unlimited public apps
- ✅ 1 private app
- ✅ Shared resources
- ✅ Community support

**For production:**
- Consider Streamlit Cloud paid plans
- Or self-host on AWS/Azure/GCP
- Or use Docker on your own server

## Next Steps After Deployment

1. **Test thoroughly** with your team
2. **Train users** on each feature
3. **Import real data** (stops, technicians)
4. **Configure optional features** (email, calendars)
5. **Monitor performance** and gather feedback
6. **Iterate and improve** based on usage

## Support

- **Streamlit Docs:** https://docs.streamlit.io
- **Supabase Docs:** https://supabase.com/docs
- **Streamlit Community:** https://discuss.streamlit.io

---

## Quick Reference Commands

```bash
# Initial setup
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/route-optimizer.git
git push -u origin main

# Future updates
git add .
git commit -m "Your update message"
git push

# Check status
git status

# View remote
git remote -v
```

---

**Congratulations! Your app is now live! 🎉**

Access it at: `https://your-app-name.streamlit.app`
