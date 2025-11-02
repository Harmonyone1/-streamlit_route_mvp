-- =============================================
-- COMPREHENSIVE RLS 403 ERROR DIAGNOSTICS
-- Run this to find out WHY 403 is still happening
-- =============================================

-- =============================================
-- CHECK 1: Verify RLS is Enabled
-- =============================================
SELECT
    tablename,
    rowsecurity as rls_enabled,
    CASE
        WHEN rowsecurity THEN '✅ RLS is ON'
        ELSE '❌ RLS is OFF'
    END as status
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename = 'organizations';

-- =============================================
-- CHECK 2: Show ALL Policies on Organizations
-- =============================================
SELECT
    policyname,
    cmd as operation,
    permissive as policy_type,  -- Should be 'PERMISSIVE'
    roles,  -- Should include {authenticated}
    CASE
        WHEN permissive = 'PERMISSIVE' THEN '✅ PERMISSIVE (good)'
        ELSE '⚠️ RESTRICTIVE (might block!)'
    END as policy_status,
    with_check::text as insert_check,
    qual::text as select_check
FROM pg_policies
WHERE tablename = 'organizations'
ORDER BY cmd, policyname;

-- =============================================
-- CHECK 3: Look for RESTRICTIVE Policies
-- =============================================
SELECT
    'RESTRICTIVE policies found!' as warning,
    COUNT(*) as count
FROM pg_policies
WHERE tablename = 'organizations'
  AND permissive = 'RESTRICTIVE';

-- =============================================
-- CHECK 4: Verify auth.uid() Works
-- =============================================
SELECT
    auth.uid() as current_user_id,
    CASE
        WHEN auth.uid() IS NOT NULL THEN '✅ You are authenticated'
        ELSE '❌ Not authenticated'
    END as auth_status,
    auth.role() as current_role;

-- =============================================
-- CHECK 5: Test the Policy Logic
-- =============================================
-- This simulates what the policy checks
SELECT
    auth.uid() IS NOT NULL as policy_would_pass,
    CASE
        WHEN auth.uid() IS NOT NULL THEN '✅ Policy check passes'
        ELSE '❌ Policy check fails'
    END as result;

-- =============================================
-- CHECK 6: Look for Table Ownership Issues
-- =============================================
SELECT
    schemaname,
    tablename,
    tableowner,
    CASE
        WHEN tableowner = 'postgres' THEN '✅ Owned by postgres'
        ELSE '⚠️ Unusual owner: ' || tableowner
    END as owner_status
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename = 'organizations';

-- =============================================
-- CHECK 7: Check Role Grants
-- =============================================
SELECT
    grantee as role,
    privilege_type,
    CASE
        WHEN privilege_type = 'INSERT' THEN '✅ INSERT granted'
        ELSE privilege_type
    END as status
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND table_name = 'organizations'
  AND grantee IN ('authenticated', 'anon', 'public')
ORDER BY grantee, privilege_type;

-- =============================================
-- DIAGNOSIS SUMMARY
-- =============================================
DO $$
DECLARE
    rls_enabled BOOLEAN;
    policy_count INTEGER;
    restrictive_count INTEGER;
    auth_check BOOLEAN;
BEGIN
    -- Check RLS enabled
    SELECT rowsecurity INTO rls_enabled
    FROM pg_tables
    WHERE schemaname = 'public' AND tablename = 'organizations';

    -- Count policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE tablename = 'organizations' AND cmd = 'INSERT';

    -- Count restrictive policies
    SELECT COUNT(*) INTO restrictive_count
    FROM pg_policies
    WHERE tablename = 'organizations' AND permissive = 'RESTRICTIVE';

    -- Check auth
    auth_check := (auth.uid() IS NOT NULL);

    RAISE NOTICE '';
    RAISE NOTICE '=== DIAGNOSIS SUMMARY ===';
    RAISE NOTICE 'RLS Enabled: %', rls_enabled;
    RAISE NOTICE 'INSERT Policies: %', policy_count;
    RAISE NOTICE 'Restrictive Policies: %', restrictive_count;
    RAISE NOTICE 'Currently Authenticated: %', auth_check;
    RAISE NOTICE '';

    IF NOT rls_enabled THEN
        RAISE NOTICE '❌ PROBLEM: RLS is disabled!';
    ELSIF policy_count = 0 THEN
        RAISE NOTICE '❌ PROBLEM: No INSERT policy exists!';
    ELSIF restrictive_count > 0 THEN
        RAISE NOTICE '⚠️ WARNING: Restrictive policies may be blocking!';
    ELSIF NOT auth_check THEN
        RAISE NOTICE '⚠️ WARNING: You are not authenticated in this session!';
    ELSE
        RAISE NOTICE '✅ Configuration looks correct';
        RAISE NOTICE '';
        RAISE NOTICE 'If still getting 403, the issue might be:';
        RAISE NOTICE '1. Policy needs explicit TO authenticated clause';
        RAISE NOTICE '2. Grant permissions are missing';
        RAISE NOTICE '3. Application is using wrong JWT token';
        RAISE NOTICE '';
        RAISE NOTICE 'Try the FIX below...';
    END IF;
END $$;

-- =============================================
-- THE FIX - Run this if diagnosis shows issues
-- =============================================

-- UNCOMMENT AND RUN THIS SECTION:
/*
-- Drop all existing policies
DROP POLICY IF EXISTS "Authenticated users can create organization" ON organizations;
DROP POLICY IF EXISTS "Members can view their organization" ON organizations;
DROP POLICY IF EXISTS "Owners can update their organization" ON organizations;
DROP POLICY IF EXISTS "Allow authenticated inserts" ON organizations;

-- Ensure table has correct grants
GRANT ALL ON organizations TO authenticated;
GRANT SELECT ON organizations TO anon;

-- Recreate policies with explicit role targeting
CREATE POLICY "authenticated_insert_organizations" ON organizations
    FOR INSERT
    TO authenticated
    WITH CHECK (true);  -- Allow any authenticated user

CREATE POLICY "authenticated_select_organizations" ON organizations
    FOR SELECT
    TO authenticated
    USING (
        id IN (SELECT get_user_organization_ids(auth.uid()))
        OR auth.uid() IS NOT NULL  -- Fallback for new users
    );

CREATE POLICY "owner_update_organizations" ON organizations
    FOR UPDATE
    TO authenticated
    USING (
        id IN (
            SELECT organization_id FROM organization_members
            WHERE user_id = auth.uid() AND role = 'owner' AND is_active = TRUE
        )
    );

-- Verify
SELECT policyname, cmd, roles
FROM pg_policies
WHERE tablename = 'organizations'
ORDER BY cmd, policyname;
*/
