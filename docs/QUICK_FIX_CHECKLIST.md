# 🔧 Quick Fix Checklist - Registration Not Working

**App URL:** https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register

---

## ✅ What We've Already Done

- [x] RLS policies created and confirmed (9 policies)
- [x] Database schema applied
- [x] Code deployed to Streamlit Cloud
- [x] Enhanced debugging added to registration page
- [x] Comprehensive deployment guide created

---

## 🚨 Critical Steps to Complete NOW

### Step 1: Configure Supabase Redirect URLs (5 minutes)

**Go to:** https://app.supabase.com → Your Project → Authentication → URL Configuration

**Set:**
```
Site URL: https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app

Redirect URLs (add all):
- https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app
- https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/**
```

Click **Save**

---

### Step 2: Disable Email Confirmation (2 minutes)

**Go to:** https://app.supabase.com → Your Project → Authentication → Providers → Email

**Find:** "Enable email confirmations"

**Action:** Toggle **OFF** (disabled)

Click **Save**

---

### Step 3: Reboot Streamlit App (1 minute)

**Go to:** https://share.streamlit.io/ → Your App → Menu (⋮) → **Reboot app**

**Wait:** 30-60 seconds for app to restart

---

### Step 4: Test Registration (3 minutes)

**Go to:** https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register

**Use a fresh email you've NEVER used before:**
```
Email: yourname+test123@gmail.com
Password: TestPassword123!
Full Name: Test User
Company: Test Company
```

**Submit and check for:**
- ✅ Success message with balloons
- ❌ Error message - expand "🔍 Debug Information" to see details

---

## 📋 Verification SQL (Optional)

If registration appears successful, run this in Supabase SQL Editor to verify:

```sql
-- Check if all records were created
SELECT
    u.email,
    u.created_at,
    p.full_name,
    o.name as organization,
    om.role
FROM auth.users u
LEFT JOIN profiles p ON p.id = u.id
LEFT JOIN organization_members om ON om.user_id = u.id
LEFT JOIN organizations o ON o.id = om.organization_id
WHERE u.email = 'yourname+test123@gmail.com';
```

**Expected result:** 1 row with all fields populated

---

## 🐛 If Still Failing

1. **Look at the error message** in the "🔍 Debug Information" expander
2. **Check common causes:**
   - Email already used (try different email)
   - Redirect URLs not saved (re-check Step 1)
   - Email confirmation still enabled (re-check Step 2)
   - App not rebooted (do Step 3 again)

3. **Check Supabase Logs:**
   - Supabase Dashboard → Logs
   - Look for errors at the time of registration attempt

4. **Check Browser Console:**
   - Press F12
   - Go to Console tab
   - Look for red errors
   - Take screenshot if you see CORS or network errors

---

## 📊 Success Looks Like

```
✅ Registration successful! Welcome to RouteFlow!
🎈 [Balloons animation]

Next Steps:
1. Check your email for verification link (if enabled)
2. Click the link to verify your account (if required)
3. Return to login page to sign in

Note: If email confirmation is disabled, you can login immediately.

[Go to Login] button
```

---

## 🆘 Get More Help

**Full Guide:** See `docs/DEPLOYMENT_CONFIG_GUIDE.md` for detailed instructions and troubleshooting

**Supabase Dashboard:** https://app.supabase.com
**Streamlit Dashboard:** https://share.streamlit.io/
**Deployed App:** https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app

---

**Time Estimate:** 10-15 minutes total
**Difficulty:** Easy (just configuration, no code changes)

**Last Updated:** 2025-11-01
