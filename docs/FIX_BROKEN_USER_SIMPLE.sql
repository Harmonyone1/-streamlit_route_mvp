-- =============================================
-- QUICK FIX FOR BROKEN USER REGISTRATION
-- Run this in Supabase SQL Editor
-- =============================================

-- User ID from logs: 0fe066f2-63f9-4a54-a719-4c455e80c404

-- STEP 1: Check current state
-- Run this first to see what's missing
SELECT
    u.id,
    u.email,
    u.created_at,
    CASE WHEN p.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as profile_status,
    CASE WHEN om.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as membership_status,
    CASE WHEN o.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as organization_status,
    om.organization_id,
    o.name as org_name
FROM auth.users u
LEFT JOIN profiles p ON p.id = u.id
LEFT JOIN organization_members om ON om.user_id = u.id
LEFT JOIN organizations o ON o.id = om.organization_id
WHERE u.id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- STEP 2: Create missing organization and link everything
-- This will fix the broken registration
DO $$
DECLARE
    v_user_id UUID := '0fe066f2-63f9-4a54-a719-4c455e80c404';
    v_user_email TEXT;
    v_full_name TEXT;
    v_company_name TEXT;
    v_org_slug TEXT;
    v_new_org_id UUID;
    v_existing_org_id UUID;
    v_profile_exists BOOLEAN;
    v_membership_exists BOOLEAN;
BEGIN
    -- Get user info from auth.users
    SELECT email,
           raw_user_meta_data->>'full_name',
           raw_user_meta_data->>'company_name'
    INTO v_user_email, v_full_name, v_company_name
    FROM auth.users
    WHERE id = v_user_id;

    -- Set defaults if metadata is missing
    v_full_name := COALESCE(v_full_name, 'User');
    v_company_name := COALESCE(v_company_name, SPLIT_PART(v_user_email, '@', 1) || '''s Company');

    -- Generate organization slug
    v_org_slug := LOWER(REGEXP_REPLACE(
        SPLIT_PART(v_user_email, '@', 1),
        '[^a-z0-9]+', '-', 'g'
    )) || '-' || SUBSTRING(v_user_id::TEXT, 1, 8);

    RAISE NOTICE 'Fixing user: % (email: %)', v_user_id, v_user_email;
    RAISE NOTICE 'Full name: %, Company: %', v_full_name, v_company_name;

    -- Check if profile exists
    SELECT EXISTS(SELECT 1 FROM profiles WHERE id = v_user_id)
    INTO v_profile_exists;

    -- Check if membership exists
    SELECT organization_id INTO v_existing_org_id
    FROM organization_members
    WHERE user_id = v_user_id
    LIMIT 1;

    v_membership_exists := (v_existing_org_id IS NOT NULL);

    -- Create or verify organization
    IF v_membership_exists THEN
        -- Membership exists - check if organization exists
        IF NOT EXISTS(SELECT 1 FROM organizations WHERE id = v_existing_org_id) THEN
            -- Organization is missing - create it with the expected ID
            INSERT INTO organizations (id, name, slug, plan_tier, subscription_status, trial_ends_at, is_active)
            VALUES (
                v_existing_org_id,
                v_company_name,
                v_org_slug || '-fix',  -- Add -fix to avoid slug conflicts
                'trial',
                'trialing',
                NOW() + INTERVAL '14 days',
                TRUE
            );
            RAISE NOTICE 'Created missing organization: %', v_existing_org_id;
            v_new_org_id := v_existing_org_id;
        ELSE
            RAISE NOTICE 'Organization already exists: %', v_existing_org_id;
            v_new_org_id := v_existing_org_id;
        END IF;
    ELSE
        -- No membership - create organization and membership
        INSERT INTO organizations (name, slug, plan_tier, subscription_status, trial_ends_at, is_active)
        VALUES (
            v_company_name,
            v_org_slug,
            'trial',
            'trialing',
            NOW() + INTERVAL '14 days',
            TRUE
        )
        RETURNING id INTO v_new_org_id;
        RAISE NOTICE 'Created new organization: %', v_new_org_id;

        -- Create membership
        INSERT INTO organization_members (organization_id, user_id, role, is_active)
        VALUES (v_new_org_id, v_user_id, 'owner', TRUE);
        RAISE NOTICE 'Created organization membership';
    END IF;

    -- Create profile if missing
    IF NOT v_profile_exists THEN
        INSERT INTO profiles (id, full_name, onboarding_completed)
        VALUES (v_user_id, v_full_name, FALSE);
        RAISE NOTICE 'Created profile';
    ELSE
        RAISE NOTICE 'Profile already exists';
    END IF;

    RAISE NOTICE '✅ Fix completed successfully!';
    RAISE NOTICE 'User should now be able to login';

EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE '❌ Error: %', SQLERRM;
        RAISE;
END $$;

-- STEP 3: Verify the fix worked
-- This should now show all ✅
SELECT
    u.id,
    u.email,
    u.created_at,
    CASE WHEN p.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as profile_status,
    CASE WHEN om.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as membership_status,
    CASE WHEN o.id IS NULL THEN '❌ MISSING' ELSE '✅ EXISTS' END as organization_status,
    p.full_name,
    om.role,
    o.name as org_name,
    o.plan_tier,
    o.trial_ends_at::DATE as trial_ends
FROM auth.users u
LEFT JOIN profiles p ON p.id = u.id
LEFT JOIN organization_members om ON om.user_id = u.id
LEFT JOIN organizations o ON o.id = om.organization_id
WHERE u.id = '0fe066f2-63f9-4a54-a719-4c455e80c404';

-- STEP 4: Test the login query
-- This is what failed with 500 error - should now work
SELECT
    organization_id,
    role,
    organizations.*
FROM organization_members
JOIN organizations ON organizations.id = organization_members.organization_id
WHERE user_id = '0fe066f2-63f9-4a54-a719-4c455e80c404'
  AND is_active = TRUE;

-- Expected: Should return 1 row with organization details

-- =============================================
-- After running this script:
-- 1. User should be able to login successfully
-- 2. They will see their organization dashboard
-- 3. No more 500 errors
-- =============================================
