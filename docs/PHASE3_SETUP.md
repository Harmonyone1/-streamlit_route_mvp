# Phase 3 Setup Guide - Dispatch & Communication

Complete setup instructions for email dispatch, Outlook calendar integration, and technician mobile view.

## Overview

Phase 3 enables you to:
- Send route assignments via professional HTML emails
- Attach ICS calendar files for easy import
- Create Outlook calendar events directly via Microsoft Graph API
- Provide mobile-friendly technician view with check-in tracking
- Track route completion and performance

## Email Dispatch Setup

### Requirements
- SMTP server credentials (Gmail, Outlook, or custom)
- Email account for sending

### Option 1: Gmail (Recommended for Testing)

1. **Enable 2-Factor Authentication**
   - Go to your Google Account settings
   - Security → 2-Step Verification
   - Enable if not already active

2. **Generate App Password**
   - Go to [App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Copy the 16-character password

3. **Configure in Application**

**Environment Variables (.env):**
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_FROM_NAME=Route Dispatcher
```

**Streamlit Secrets (.streamlit/secrets.toml):**
```toml
[smtp]
server = "smtp.gmail.com"
port = 587
username = "your-email@gmail.com"
password = "your-16-char-app-password"
from_name = "Route Dispatcher"
```

### Option 2: Outlook/Office 365

```toml
[smtp]
server = "smtp.office365.com"
port = 587
username = "your-email@company.com"
password = "your-password"
from_name = "Route Dispatcher"
```

### Option 3: Other SMTP Providers

**Yahoo:**
```toml
server = "smtp.mail.yahoo.com"
port = 587
```

**Custom SMTP:**
Contact your email provider for SMTP settings.

### Testing Email Dispatch

1. Configure SMTP as above
2. Go to **Dispatch** page
3. Optimize routes in **Operations** first
4. Select "Test Mode (Send to Me)"
5. Click "Send Emails Now"
6. Check your inbox

### Email Features

**What's Included:**
- Beautiful HTML formatted email
- Complete route details with arrival times
- Customer information
- Service notes
- ICS calendar attachment
- Mobile-responsive design

**ICS Calendar File:**
- Automatically attached to every email
- One-click import to any calendar app
- Individual events for each stop
- 15-minute reminders
- Works with: Google Calendar, Outlook, Apple Calendar, etc.

## Microsoft Graph API (Outlook Calendar) Setup

### Prerequisites
- Microsoft 365 or Azure AD account
- Admin access to Azure Portal
- Technician email addresses must be in same Microsoft tenant

### Step 1: Register Application in Azure

1. **Go to Azure Portal**
   - Navigate to [Azure Portal](https://portal.azure.com)
   - Go to "Azure Active Directory"

2. **Register New Application**
   - Click "App registrations" → "New registration"
   - **Name:** Route Optimization Platform
   - **Supported account types:** Single tenant
   - **Redirect URI:** Leave blank
   - Click "Register"

3. **Copy Application Details**
   - **Application (client) ID** - Save this
   - **Directory (tenant) ID** - Save this
   - These will be your `client_id` and `tenant_id`

### Step 2: Create Client Secret

1. Go to "Certificates & secrets"
2. Click "New client secret"
3. **Description:** Route Dispatcher
4. **Expires:** Choose duration (24 months recommended)
5. Click "Add"
6. **Copy the VALUE immediately** - This is your `client_secret`
   - Note: The value is only shown once!

### Step 3: Grant API Permissions

1. Go to "API permissions"
2. Click "Add a permission"
3. Choose "Microsoft Graph"
4. Select "Application permissions" (NOT Delegated)
5. Search and add these permissions:
   - `Calendars.ReadWrite` - Create and manage calendar events
   - `User.Read.All` - Read user profiles (optional)
6. Click "Add permissions"
7. **Important:** Click "Grant admin consent" button
   - This requires admin privileges
   - All users in tenant will be able to use this app

### Step 4: Configure in Application

**Environment Variables:**
```bash
MS_CLIENT_ID=your-application-client-id
MS_CLIENT_SECRET=your-client-secret-value
MS_TENANT_ID=your-directory-tenant-id
```

**Streamlit Secrets:**
```toml
[microsoft_graph]
client_id = "your-application-client-id"
client_secret = "your-client-secret-value"
tenant_id = "your-directory-tenant-id"
```

### Step 5: Test Calendar Integration

1. Configure as above
2. Go to **Dispatch** page
3. Navigate to "Calendar Dispatch" tab
4. Should see "✅ Microsoft Graph API ready"
5. Click "Create Calendar Events"
6. Check technician Outlook calendars

### Troubleshooting Graph API

**Error: "Failed to acquire token"**
- Verify client_id, client_secret, and tenant_id are correct
- Ensure no extra spaces or quotes in secrets
- Client secret may have expired (check Azure Portal)

**Error: "Permission denied"**
- Ensure admin consent was granted
- Check that Calendars.ReadWrite permission is added
- Verify it's "Application permissions" not "Delegated"

**Error: "User not found"**
- Technician email must be in same Microsoft tenant
- Check email addresses are correct in database
- Verify user exists in Azure AD

### Permissions Explanation

**Application Permissions** (what we use):
- App acts on its own behalf
- No user login required
- Can access any user's calendar
- Requires admin consent
- Best for automation

**Delegated Permissions** (alternative):
- App acts on behalf of a signed-in user
- User must login each time
- Can only access own calendar
- Not suitable for this use case

## Technician Mobile View

The technician view is automatically available at the **Technician** page.

### Features

**Mobile-Responsive:**
- Large touch-friendly buttons
- Optimized for phone screens
- Works offline for viewing routes
- Auto-adapts to screen size

**Capabilities:**
- View complete route for the day
- Check in at each stop
- Mark stops as complete
- Add notes about each job
- Navigate to stops via Google Maps
- Track progress with visual indicators
- View route on interactive map

### Using Technician View

1. **Select Technician**
   - Open sidebar
   - Choose name from dropdown
   - Select date
   - Click "Load My Route"

2. **Navigate Route**
   - See all stops in order
   - Current stop highlighted in blue
   - Completed stops shown in gray
   - Progress bar at top

3. **At Each Stop**
   - Click "🚗 Navigate" - Opens Google Maps
   - Click "📍 Check In" - Records arrival time
   - Click "✅ Complete" - Marks stop done
   - Add notes if needed

4. **View Options**
   - **Stops List** - Detailed card view
   - **Map View** - See all stops on map
   - **Summary** - Tabular overview

### Session State Tracking

Check-ins and completions are stored in session state:
- Persists during browser session
- Lost on page reload (by design for demo)
- Production version would save to database

### Future Enhancements

Planned features:
- Photo upload at each stop
- Digital signatures
- Offline mode with sync
- Push notifications
- Real-time location tracking
- Customer SMS notifications

## Testing Your Setup

### Test Email Dispatch

1. Add test stops in Operations
2. Optimize routes
3. Go to Dispatch → Email Dispatch
4. Select "Test Mode"
5. Click "Send Emails Now"
6. Check your email
7. Verify ICS attachment works

### Test Calendar Integration

1. Ensure Graph API configured
2. Go to Dispatch → Calendar Dispatch
3. Check for "✅ Microsoft Graph API ready"
4. Click "Create Calendar Events"
5. Open Outlook calendar
6. Verify events appear

### Test Technician View

1. Add sample technicians to database
2. Optimize routes assigned to them
3. Go to Technician page
4. Select a technician
5. Load route
6. Test check-in, completion, notes
7. Verify map view works

## Production Deployment

### Email Best Practices

1. **Use Dedicated Email**
   - Create `noreply@yourcompany.com`
   - Don't use personal accounts

2. **Monitor Sending**
   - Watch for bounces
   - Keep email list clean
   - Respect rate limits

3. **Test Spam Filters**
   - Send to multiple providers
   - Check spam folders
   - Adjust content if needed

### Calendar Best Practices

1. **Service Account**
   - Use dedicated Azure app registration
   - Rotate secrets annually
   - Monitor usage logs

2. **Event Management**
   - Use clear event titles
   - Include all relevant details
   - Set appropriate reminders

3. **Category Tagging**
   - All events tagged "Route Assignment"
   - Easy to filter and delete
   - Helps with cleanup

### Mobile View Best Practices

1. **Testing**
   - Test on actual mobile devices
   - Various screen sizes
   - Different browsers

2. **Offline Handling**
   - Clear messaging when offline
   - Cache route data where possible
   - Sync when connection restored

3. **User Training**
   - Show technicians the features
   - Explain check-in process
   - Demonstrate navigation

## Security Considerations

### Email Security

- Use app passwords, not account passwords
- Enable 2FA on email accounts
- Use TLS/STARTTLS for connections
- Don't hardcode credentials
- Rotate passwords regularly

### Microsoft Graph Security

- Keep client secrets secure
- Rotate secrets before expiration
- Use minimum required permissions
- Monitor access logs
- Revoke unused app registrations

### Data Privacy

- Don't expose customer data unnecessarily
- Use HTTPS in production
- Secure session state
- Log access appropriately
- Comply with privacy regulations

## Troubleshooting

### Email Not Sending

**Check:**
- SMTP credentials correct
- Port not blocked by firewall
- Email provider allows SMTP
- Technician email addresses valid
- Check spam/junk folders

**Gmail Specific:**
- App password, not account password
- 2FA must be enabled
- "Less secure app access" NOT needed with app passwords
- Check Gmail security settings

### Calendar Events Not Creating

**Check:**
- Microsoft Graph config correct
- Admin consent granted
- Technician emails in same tenant
- Calendar permissions granted
- API not rate limited

### Mobile View Issues

**Check:**
- Routes optimized first
- Technician assigned to route
- Session state not cleared
- Browser JavaScript enabled
- Internet connection for maps

## Support and Resources

### Documentation
- [Microsoft Graph API Docs](https://docs.microsoft.com/en-us/graph/)
- [Gmail SMTP Guide](https://support.google.com/mail/answer/7126229)
- [ICS File Format](https://icalendar.org/)

### Getting Help
- Check error messages in Streamlit
- Review browser console for JavaScript errors
- Test configurations step-by-step
- Verify all prerequisites met

## Next Steps

After Phase 3 setup:
1. Configure email dispatch
2. Test with team
3. Optionally set up Outlook calendars
4. Train technicians on mobile view
5. Monitor usage and feedback
6. Adjust based on needs

## Configuration Checklist

- [ ] SMTP server configured
- [ ] Test email sent successfully
- [ ] ICS attachment working
- [ ] Azure app registered (if using calendars)
- [ ] API permissions granted
- [ ] Admin consent given
- [ ] Calendar events created successfully
- [ ] Technicians can access mobile view
- [ ] Check-in/completion working
- [ ] Map view functional
- [ ] Navigation links working
- [ ] Team trained on features

---

**Phase 3 Setup Complete!**

You now have a fully functional dispatch system with email, calendar, and mobile technician features.
