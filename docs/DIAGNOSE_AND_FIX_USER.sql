-- =============================================
-- DIAGNOSE AND FIX BROKEN USER REGISTRATION
-- Run this in Supabase SQL Editor
-- =============================================

-- User ID from logs: 0fe066f2-63f9-4a54-a719-4c455e80c404

-- =============================================
-- STEP 1: DIAGNOSE THE PROBLEM
-- =============================================

-- Check if user exists in auth.users
SELECT
    id,
    email,
    created_at,
    confirmed_at,
    email_confirmed_at
FROM auth.users
WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- Check if profile exists
SELECT * FROM profiles
WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- Check if organization_members record exists
SELECT * FROM organization_members
WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- Check if organization exists (if organization_members record was found)
-- Replace <org_id> with the organization_id from the previous query
-- SELECT * FROM organizations
-- WHERE id = '<org_id_from_previous_query>';

-- =============================================
-- COMPREHENSIVE CHECK FOR ALL ORPHANED USERS
-- =============================================

-- Find all users without complete registration
SELECT
    u.id,
    u.email,
    u.created_at,
    CASE WHEN p.id IS NULL THEN '❌' ELSE '✅' END as has_profile,
    CASE WHEN om.id IS NULL THEN '❌' ELSE '✅' END as has_membership,
    CASE WHEN o.id IS NULL THEN '❌' ELSE '✅' END as has_organization,
    om.organization_id,
    om.role,
    o.name as org_name
FROM auth.users u
LEFT JOIN profiles p ON p.id = u.id
LEFT JOIN organization_members om ON om.user_id = u.id
LEFT JOIN organizations o ON o.id = om.organization_id
WHERE u.created_at > NOW() - INTERVAL '7 days'  -- Recent users only
ORDER BY u.created_at DESC;

-- =============================================
-- STEP 2: FIX THE SPECIFIC USER
-- =============================================

-- Run these one at a time, checking results after each step

-- Option A: If organization_members exists but organization doesn't
-- First, check what organization_id is in organization_members:
SELECT user_id, organization_id, role
FROM organization_members
WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- If the query above shows an organization_id, check if that org exists:
-- SELECT * FROM organizations WHERE id = '<org_id_from_above>';

-- If organization doesn't exist, create it now:
-- NOTE: Update the values below with actual user data
/*
DO $$
DECLARE
    user_email TEXT;
    user_full_name TEXT;
    company_name TEXT;
    org_slug TEXT;
    new_org_id UUID;
    existing_org_id UUID;
BEGIN
    -- Get user info
    SELECT email INTO user_email
    FROM auth.users
    WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

    -- Get user metadata if available
    SELECT raw_user_meta_data->>'full_name',
           raw_user_meta_data->>'company_name'
    INTO user_full_name, company_name
    FROM auth.users
    WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

    -- Set defaults if not found
    user_full_name := COALESCE(user_full_name, 'User');
    company_name := COALESCE(company_name, 'My Company');

    -- Generate organization slug
    org_slug := LOWER(REGEXP_REPLACE(
        SPLIT_PART(user_email, '@', 1),
        '[^a-z0-9]+', '-', 'g'
    )) || '-' || SUBSTRING('0fe066f2-63f9-4a54-a719-4c455e80c404'::TEXT, 1, 8);

    -- Check if organization_members has an org_id
    SELECT organization_id INTO existing_org_id
    FROM organization_members
    WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

    IF existing_org_id IS NOT NULL THEN
        -- Organization_members has org_id but organization doesn't exist
        -- Create organization with the same ID
        INSERT INTO organizations (id, name, slug, plan_tier, subscription_status, trial_ends_at, is_active)
        VALUES (
            existing_org_id,
            company_name,
            org_slug,
            'trial',
            'trialing',
            NOW() + INTERVAL '14 days',
            TRUE
        )
        ON CONFLICT (id) DO NOTHING;

        RAISE NOTICE 'Created organization with ID: %', existing_org_id;
    ELSE
        -- No organization_members record at all - create everything

        -- Create organization
        INSERT INTO organizations (name, slug, plan_tier, subscription_status, trial_ends_at, is_active)
        VALUES (
            company_name,
            org_slug,
            'trial',
            'trialing',
            NOW() + INTERVAL '14 days',
            TRUE
        )
        RETURNING id INTO new_org_id;

        RAISE NOTICE 'Created new organization with ID: %', new_org_id;

        -- Create organization membership
        INSERT INTO organization_members (organization_id, user_id, role, is_active)
        VALUES (new_org_id, '0fe066f2-63f9-4a54-a719-4c455e80c404', 'owner', TRUE)
        ON CONFLICT (organization_id, user_id) DO NOTHING;

        RAISE NOTICE 'Created organization membership';
    END IF;

    -- Create profile if missing
    INSERT INTO profiles (id, full_name)
    VALUES ('0fe066f2-63f9-4a54-a719-4c455e80c404', user_full_name)
    ON CONFLICT (id) DO NOTHING;

    RAISE NOTICE 'Profile created or already exists';

END $$;
*/

-- =============================================
-- STEP 3: VERIFY THE FIX
-- =============================================

-- After running the fix, verify everything is correct:
SELECT
    u.id,
    u.email,
    u.created_at,
    p.full_name,
    om.role,
    o.id as org_id,
    o.name as org_name,
    o.plan_tier,
    o.trial_ends_at
FROM auth.users u
LEFT JOIN profiles p ON p.id = u.id
LEFT JOIN organization_members om ON om.user_id = u.id
LEFT JOIN organizations o ON o.id = om.organization_id
WHERE u.id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- Expected result: 1 row with all fields populated

-- =============================================
-- STEP 4: TEST LOGIN QUERY
-- =============================================

-- This is the exact query that failed with 500 error
-- It should now return results without error
SELECT
    organization_members.organization_id,
    organization_members.role,
    organizations.*
FROM organization_members
JOIN organizations ON organizations.id = organization_members.organization_id
WHERE organization_members.user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404'
  AND organization_members.is_active = TRUE;

-- =============================================
-- ALTERNATIVE: CLEAN SLATE APPROACH
-- =============================================

-- If you want to completely remove this user and let them re-register:
/*
-- WARNING: This deletes the user completely!
DELETE FROM organization_members WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404';
DELETE FROM profiles WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';
-- Note: Don't delete from organizations if other users might be linked
-- DELETE FROM organizations WHERE id IN (
--     SELECT organization_id FROM organization_members WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404'
-- );
-- Delete from auth.users (this will cascade)
DELETE FROM auth.users WHERE id = '0fe066f2-63f9-4a54-a719-4c455e80c404';
*/

-- =============================================
-- NOTES
-- =============================================
/*
The 500 error in the logs indicates:
GET /rest/v1/organization_members?select=organization_id,role,organizations(*)&user_id=eq.0fe066f2-63f9-4a54-a719-4c455e80c404&is_active=eq.True

This query is trying to:
1. SELECT from organization_members WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404'
2. JOIN with organizations table
3. Return organization details

A 500 error suggests:
- The organization_members record has an organization_id that doesn't exist in organizations
- Or the JOIN is failing due to missing data
- Or RLS policies are blocking the JOIN (less likely since we confirmed policies exist)

The fix creates the missing organization record so the JOIN succeeds.
*/
