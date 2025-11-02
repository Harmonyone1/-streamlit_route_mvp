# RouteFlow Streamlit Cloud Deployment Configuration Guide

**Deployed App URL:** https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app

This guide provides step-by-step instructions to configure Supabase for your deployed Streamlit Cloud app.

---

## ✅ Status Checklist

- [x] RLS Policies Created (9 policies confirmed)
- [x] Database Schema Applied
- [x] Code Deployed to Streamlit Cloud
- [ ] Supabase Redirect URLs Configured
- [ ] Email Confirmation Settings Configured
- [ ] Streamlit App Rebooted
- [ ] Registration Tested Successfully

---

## 🔧 Step 1: Configure Supabase Redirect URLs

**Why:** Supabase Auth needs to know which URLs are allowed to redirect after authentication. Without this, registration and login will fail.

### Instructions:

1. **Go to Supabase Dashboard**
   - URL: https://app.supabase.com
   - Navigate to your project

2. **Open Authentication Settings**
   - Click on **Authentication** in the left sidebar
   - Click on **URL Configuration**

3. **Configure Site URL**
   - **Site URL:** `https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app`
   - This is your main app URL

4. **Configure Redirect URLs**
   Add the following URLs to the **Redirect URLs** list:
   ```
   https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app
   https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/**
   https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/login
   https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register
   ```

5. **Save Configuration**
   - Click **Save** button at the bottom

### Visual Reference:
```
┌─────────────────────────────────────────────┐
│ Authentication > URL Configuration          │
├─────────────────────────────────────────────┤
│                                             │
│ Site URL                                    │
│ ┌─────────────────────────────────────────┐ │
│ │ https://harmonyone1--streamlit-route... │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ Redirect URLs                               │
│ ┌─────────────────────────────────────────┐ │
│ │ https://harmonyone1--streamlit-route... │ │
│ │ https://harmonyone1--streamlit-route../**│ │
│ │ https://harmonyone1--streamlit-route.../│ │
│ │ https://harmonyone1--streamlit-route.../│ │
│ └─────────────────────────────────────────┘ │
│                                             │
│                      [Save]                 │
└─────────────────────────────────────────────┘
```

---

## 📧 Step 2: Configure Email Confirmation Settings

**Why:** Supabase has email rate limits on free tier. For development/testing, we should disable email confirmation.

### Option A: Disable Email Confirmation (Recommended for Development)

1. **Go to Supabase Dashboard**
   - Navigate to your project

2. **Open Authentication Settings**
   - Click on **Authentication** in the left sidebar
   - Click on **Providers** or **Email**

3. **Disable Email Confirmation**
   - Find the setting **"Enable email confirmations"**
   - Toggle it **OFF** (disabled)
   - This allows users to login immediately after signup

4. **Save Settings**
   - Click **Save**

### Option B: Configure Custom SMTP (For Production)

If you want email confirmation for production:

1. **Go to Authentication > Email Templates**

2. **Set up SMTP Settings**
   - SMTP Host: `smtp.sendgrid.net` (or your provider)
   - SMTP Port: `587`
   - SMTP User: Your SendGrid username
   - SMTP Password: Your SendGrid password

3. **Customize Email Templates** (optional)
   - Confirmation email
   - Password reset email
   - Magic link email

4. **Save Configuration**

### Visual Reference:
```
┌─────────────────────────────────────────────┐
│ Authentication > Providers > Email          │
├─────────────────────────────────────────────┤
│                                             │
│ ☑ Enable email provider                    │
│                                             │
│ ☐ Enable email confirmations               │
│   ^── DISABLE THIS for development          │
│                                             │
│ ☐ Secure email change                      │
│                                             │
│                      [Save]                 │
└─────────────────────────────────────────────┘
```

---

## 🔄 Step 3: Reboot Streamlit App

**Why:** Streamlit Cloud needs to reload to pick up any environment or configuration changes.

### Instructions:

1. **Go to Streamlit Cloud Dashboard**
   - URL: https://share.streamlit.io/
   - Find your app: `harmonyone1/streamlit_route_mvp`

2. **Reboot the App**
   - Click on your app
   - Click the **three dots menu (⋮)** in the top right
   - Click **"Reboot app"**
   - Wait for the app to restart (30-60 seconds)

3. **Alternative: Use App Menu**
   - Open the deployed app
   - Click the hamburger menu (☰) in the top right
   - Click **"Reboot app"** (if available)

### Visual Reference:
```
┌─────────────────────────────────────────────┐
│ streamlit_route_mvp                    ⋮   │
├─────────────────────────────────────────────┤
│                                             │
│ Status: ● Running                           │
│                                             │
│ Click ⋮ menu:                               │
│   - Settings                                │
│   - Reboot app  <── Click here              │
│   - Delete app                              │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🧪 Step 4: Test Registration

**Why:** Verify that all configurations are working correctly.

### Test Account Information:
Use a **completely fresh email** that has never been used before:

```
Email: test+routeflow123@yourdomain.com
Password: TestPassword123!
Full Name: Test User
Company Name: Test Company
```

### Testing Steps:

1. **Open Registration Page**
   - Go to: https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register

2. **Fill Out Form**
   - Use the test account information above
   - Check "I agree to Terms of Service"

3. **Submit Registration**
   - Click **"Start Free Trial"**

4. **Expected Outcomes:**

   **✅ SUCCESS:**
   ```
   ✅ Registration successful! Welcome to RouteFlow!
   🎈 Balloons animation
   ```
   - You should see success message
   - If email confirmation is disabled, you can login immediately

   **❌ ERROR:**
   - Expand the "🔍 Debug Information" section
   - Read the error message carefully
   - Check the configuration checklist

5. **Test Login**
   - Go to: https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/login
   - Login with the test account
   - Verify you can access the Operations page

---

## 🐛 Troubleshooting Guide

### Error: "Email already registered"

**Cause:** Email has been used before (even in failed attempts)

**Solution:**
- Use a completely new email address
- Try email+alias format: `yourname+test1@gmail.com`
- Delete old test accounts from Supabase Authentication > Users

---

### Error: "RLS policy violation" or "new row violates row-level security policy"

**Cause:** Missing or incorrect RLS policies

**Solution:**
1. **Verify RLS Policies Exist**
   - Run this in Supabase SQL Editor:
   ```sql
   SELECT schemaname, tablename, policyname, cmd
   FROM pg_policies
   WHERE tablename IN ('organizations', 'profiles', 'organization_members')
   ORDER BY tablename, policyname;
   ```

2. **Expected Output:** You should see 9 policies including:
   - `Users can insert own profile` (INSERT)
   - `Authenticated users can create organization` (INSERT)
   - `Authenticated users can join organization` (INSERT)

3. **If Missing:** Re-run `docs/rls_policies_fix.sql`

---

### Error: "Email confirmation required" or "Please verify your email"

**Cause:** Email confirmation is enabled but emails are not sending

**Solution:**
- **Option 1:** Disable email confirmation (see Step 2, Option A)
- **Option 2:** Check email spam folder
- **Option 3:** Wait 1 hour for rate limit reset
- **Option 4:** Configure custom SMTP (see Step 2, Option B)

---

### Error: "Database error saving new user" or "Failed to create organization"

**Cause:** Multiple possible issues

**Solution:**
1. **Check Supabase Service Status**
   - Visit: https://status.supabase.com/

2. **Verify Database Schema**
   - Run this in Supabase SQL Editor:
   ```sql
   -- Check if tables exist
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'public'
   AND table_name IN ('organizations', 'profiles', 'organization_members');
   ```

3. **Check Supabase Logs**
   - Go to Supabase Dashboard > Logs
   - Look for recent errors around the time of registration attempt

4. **Verify Supabase Secrets**
   - Go to Streamlit Cloud app settings > Secrets
   - Verify `SUPABASE_URL` and `SUPABASE_KEY` are correct

---

### Error: "Network error" or "Failed to fetch"

**Cause:** CORS or network connectivity issues

**Solution:**
1. **Check Browser Console**
   - Open browser DevTools (F12)
   - Check Console tab for errors
   - Look for CORS errors

2. **Verify Supabase URL**
   - Ensure SUPABASE_URL in secrets is correct
   - Should look like: `https://xxxxx.supabase.co`

3. **Check Firewall/VPN**
   - Disable VPN temporarily
   - Check if corporate firewall is blocking Supabase

---

### Registration Works But Login Fails with "No organization found"

**Cause:** Organization was not created during signup

**Solution:**
1. **Check Database**
   ```sql
   -- Find user
   SELECT id, email FROM auth.users WHERE email = 'test@example.com';

   -- Check if organization_members exists for user
   SELECT * FROM organization_members WHERE user_id = '<user_id>';

   -- Check if organization exists
   SELECT * FROM organizations WHERE id IN (
       SELECT organization_id FROM organization_members WHERE user_id = '<user_id>'
   );
   ```

2. **If Missing:** The signup process didn't complete
   - This suggests a transaction failure
   - Check Supabase logs for errors
   - Verify all three tables have INSERT policies

---

## 📊 Verification SQL Queries

Run these in Supabase SQL Editor to verify setup:

### Check RLS Policies
```sql
SELECT schemaname, tablename, policyname, cmd
FROM pg_policies
WHERE tablename IN ('organizations', 'profiles', 'organization_members')
ORDER BY tablename, policyname;
```

**Expected:** 9 policies (3 for each table)

### Check Recent Registrations
```sql
-- Recent users
SELECT id, email, created_at, confirmed_at
FROM auth.users
ORDER BY created_at DESC
LIMIT 5;

-- Recent organizations
SELECT id, name, slug, plan_tier, created_at
FROM organizations
ORDER BY created_at DESC
LIMIT 5;

-- Recent memberships
SELECT om.*, u.email, o.name as org_name
FROM organization_members om
JOIN auth.users u ON om.user_id = u.id
JOIN organizations o ON om.organization_id = o.id
ORDER BY om.created_at DESC
LIMIT 5;
```

### Check for Orphaned Records
```sql
-- Users without organizations
SELECT u.id, u.email, u.created_at
FROM auth.users u
WHERE NOT EXISTS (
    SELECT 1 FROM organization_members om WHERE om.user_id = u.id
)
ORDER BY u.created_at DESC;
```

---

## 🎯 Success Criteria

Your deployment is successful when:

- ✅ Registration form loads without errors
- ✅ User can submit registration with valid data
- ✅ Success message appears: "Registration successful!"
- ✅ User record created in `auth.users`
- ✅ Profile record created in `profiles`
- ✅ Organization created in `organizations`
- ✅ Membership created in `organization_members` with role='owner'
- ✅ User can login with email/password
- ✅ User sees Operations page after login
- ✅ User's organization name appears in UI

---

## 📝 Configuration Summary

| Setting | Value |
|---------|-------|
| **App URL** | https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app |
| **Supabase Site URL** | Same as App URL |
| **Email Confirmation** | Disabled (for development) |
| **RLS Policies** | 9 policies (confirmed) |
| **Database Schema** | Applied (see `docs/saas_database_schema.sql`) |

---

## 🆘 Getting Help

If you're still experiencing issues after following this guide:

1. **Check Error Message**
   - The registration page now has detailed debug information
   - Expand the "🔍 Debug Information" section
   - Read the specific error and common causes

2. **Review Logs**
   - **Streamlit Logs:** Available in Streamlit Cloud dashboard
   - **Supabase Logs:** Dashboard > Logs section
   - **Browser Console:** F12 > Console tab

3. **Try Fresh Email**
   - Use a completely new email address
   - Previous failed attempts may have created partial records

4. **Contact Support**
   - Email: support@routeflow.com
   - Include: Error message, user email, timestamp

---

## 🚀 Next Steps After Successful Registration

Once registration is working:

1. **Test Full User Flow**
   - Register multiple users
   - Test login/logout
   - Test password reset
   - Test team invitations

2. **Phase 5: Stripe Integration**
   - Set up Stripe account
   - Create products and pricing
   - Implement subscription flow

3. **Production Preparation**
   - Enable email confirmation
   - Configure custom SMTP
   - Set up custom domain
   - Enable SSL/HTTPS

---

**Last Updated:** 2025-11-01
**Status:** Deployment in progress - awaiting configuration completion
