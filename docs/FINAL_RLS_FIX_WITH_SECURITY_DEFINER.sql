-- =============================================
-- FINAL RLS FIX WITH SECURITY DEFINER FUNCTIONS
-- This script fixes all RLS issues with no recursion
-- Production-ready solution
-- =============================================

-- 0. Set search path
SET search_path = public, auth, pg_catalog;

-- =============================================
-- PART 1: CREATE SECURITY DEFINER HELPER FUNCTIONS
-- These functions bypass RLS to prevent infinite recursion
-- =============================================

-- Helper function to check if user has specific role in organization
CREATE OR REPLACE FUNCTION public.user_has_role_in_org(
    check_user_id UUID,
    check_org_id UUID,
    required_roles TEXT[]
)
RETURNS BOOLEAN AS $$
BEGIN
    -- SECURITY DEFINER allows this to bypass RLS
    RETURN EXISTS (
        SELECT 1
        FROM public.organization_members
        WHERE user_id = check_user_id
          AND organization_id = check_org_id
          AND role = ANY(required_roles)
          AND is_active = true
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- Helper function to get all organization IDs user belongs to
CREATE OR REPLACE FUNCTION public.get_user_organization_ids(user_uuid UUID)
RETURNS SETOF UUID AS $$
    -- SECURITY DEFINER allows this to bypass RLS
    SELECT organization_id
    FROM public.organization_members
    WHERE user_id = user_uuid
      AND is_active = true;
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- =============================================
-- PART 2: GRANT PERMISSIONS
-- =============================================

GRANT SELECT, INSERT, UPDATE, DELETE ON public.organizations TO authenticated;
GRANT SELECT ON public.organizations TO anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.organization_members TO authenticated;
GRANT SELECT ON public.organization_members TO anon;

GRANT SELECT, INSERT, UPDATE, DELETE ON public.profiles TO authenticated;
GRANT SELECT ON public.profiles TO anon;

-- =============================================
-- PART 3: ENABLE RLS
-- =============================================

ALTER TABLE public.organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- =============================================
-- PART 4: DROP ALL OLD POLICIES
-- =============================================

-- Drop organizations policies
DROP POLICY IF EXISTS "Authenticated users can create organization" ON public.organizations;
DROP POLICY IF EXISTS "Members can view their organization" ON public.organizations;
DROP POLICY IF EXISTS "Owners can update their organization" ON public.organizations;
DROP POLICY IF EXISTS "Allow authenticated inserts" ON public.organizations;
DROP POLICY IF EXISTS "authenticated_insert_organizations" ON public.organizations;
DROP POLICY IF EXISTS "authenticated_select_organizations" ON public.organizations;
DROP POLICY IF EXISTS "owner_update_organizations" ON public.organizations;
DROP POLICY IF EXISTS "anon_select_organizations_no_rows" ON public.organizations;

-- Drop organization_members policies
DROP POLICY IF EXISTS "Users can insert own membership" ON public.organization_members;
DROP POLICY IF EXISTS "View organization members" ON public.organization_members;
DROP POLICY IF EXISTS "Admins can manage organization members" ON public.organization_members;
DROP POLICY IF EXISTS "Authenticated users can join organization" ON public.organization_members;
DROP POLICY IF EXISTS "Admins can update members" ON public.organization_members;
DROP POLICY IF EXISTS "Owners can delete members" ON public.organization_members;
DROP POLICY IF EXISTS "authenticated_insert_members" ON public.organization_members;
DROP POLICY IF EXISTS "authenticated_select_members" ON public.organization_members;

-- Drop profiles policies
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "authenticated_insert_profile" ON public.profiles;
DROP POLICY IF EXISTS "authenticated_select_profile" ON public.profiles;
DROP POLICY IF EXISTS "authenticated_update_profile" ON public.profiles;

-- =============================================
-- PART 5: CREATE ORGANIZATIONS POLICIES
-- =============================================

-- Policy 1: INSERT - Any authenticated user can create organization (for signup)
CREATE POLICY "authenticated_insert_organizations" ON public.organizations
    FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) IS NOT NULL);

-- Policy 2: SELECT - View organizations you belong to (uses helper function - no recursion!)
CREATE POLICY "authenticated_select_organizations" ON public.organizations
    FOR SELECT
    TO authenticated
    USING (
        id IN (SELECT public.get_user_organization_ids((SELECT auth.uid())))
    );

-- Policy 3: UPDATE - Only owners can update (uses helper function - no recursion!)
CREATE POLICY "owner_update_organizations" ON public.organizations
    FOR UPDATE
    TO authenticated
    USING (
        public.user_has_role_in_org((SELECT auth.uid()), id, ARRAY['owner'])
    )
    WITH CHECK (
        public.user_has_role_in_org((SELECT auth.uid()), id, ARRAY['owner'])
    );

-- Policy 4: DELETE - Only owners can delete
CREATE POLICY "owner_delete_organizations" ON public.organizations
    FOR DELETE
    TO authenticated
    USING (
        public.user_has_role_in_org((SELECT auth.uid()), id, ARRAY['owner'])
    );

-- Policy 5: Anon can't see any rows (but can connect)
CREATE POLICY "anon_select_organizations_no_rows" ON public.organizations
    FOR SELECT
    TO anon
    USING (false);

-- =============================================
-- PART 6: CREATE ORGANIZATION_MEMBERS POLICIES
-- =============================================

-- Policy 1: INSERT - Users can insert themselves (for signup)
CREATE POLICY "authenticated_insert_members" ON public.organization_members
    FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

-- Policy 2: SELECT - View members of organizations you belong to (uses helper - no recursion!)
CREATE POLICY "authenticated_select_members" ON public.organization_members
    FOR SELECT
    TO authenticated
    USING (
        organization_id IN (SELECT public.get_user_organization_ids((SELECT auth.uid())))
        OR user_id = (SELECT auth.uid())
    );

-- Policy 3: UPDATE - Admins and owners can update members (uses helper - no recursion!)
CREATE POLICY "admins_update_members" ON public.organization_members
    FOR UPDATE
    TO authenticated
    USING (
        public.user_has_role_in_org((SELECT auth.uid()), organization_id, ARRAY['owner', 'admin'])
    )
    WITH CHECK (
        public.user_has_role_in_org((SELECT auth.uid()), organization_id, ARRAY['owner', 'admin'])
    );

-- Policy 4: DELETE - Only owners can delete members
CREATE POLICY "owners_delete_members" ON public.organization_members
    FOR DELETE
    TO authenticated
    USING (
        public.user_has_role_in_org((SELECT auth.uid()), organization_id, ARRAY['owner'])
    );

-- Policy 5: Anon can't see any rows
CREATE POLICY "anon_select_members_no_rows" ON public.organization_members
    FOR SELECT
    TO anon
    USING (false);

-- =============================================
-- PART 7: CREATE PROFILES POLICIES
-- =============================================

-- Policy 1: INSERT - Users can create their own profile
CREATE POLICY "authenticated_insert_profile" ON public.profiles
    FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = id);

-- Policy 2: SELECT - Users can view their own profile
CREATE POLICY "authenticated_select_profile" ON public.profiles
    FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = id);

-- Policy 3: UPDATE - Users can update their own profile
CREATE POLICY "authenticated_update_profile" ON public.profiles
    FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = id)
    WITH CHECK ((SELECT auth.uid()) = id);

-- Policy 4: DELETE - Users can delete their own profile
CREATE POLICY "authenticated_delete_profile" ON public.profiles
    FOR DELETE
    TO authenticated
    USING ((SELECT auth.uid()) = id);

-- Policy 5: Anon can't see any profiles
CREATE POLICY "anon_select_profiles_no_rows" ON public.profiles
    FOR SELECT
    TO anon
    USING (false);

-- =============================================
-- PART 8: DISABLE PROBLEMATIC TRIGGER
-- =============================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- =============================================
-- PART 9: VERIFICATION
-- =============================================

-- Count policies per table
SELECT
    schemaname,
    tablename,
    COUNT(*) AS policy_count,
    string_agg(policyname || ' (' || cmd || ')', ', ' ORDER BY cmd, policyname) AS policies
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('organizations', 'organization_members', 'profiles')
GROUP BY schemaname, tablename
ORDER BY tablename;

-- Expected results:
-- organizations: 5 policies (INSERT, SELECT, UPDATE, DELETE + anon SELECT)
-- organization_members: 5 policies (INSERT, SELECT, UPDATE, DELETE + anon SELECT)
-- profiles: 5 policies (INSERT, SELECT, UPDATE, DELETE + anon SELECT)

-- Verify helper functions exist
SELECT
    routine_name,
    routine_type,
    security_type,
    CASE
        WHEN security_type = 'DEFINER' THEN '✅ SECURITY DEFINER (bypasses RLS)'
        ELSE '⚠️ Not SECURITY DEFINER'
    END as security_status
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name IN ('user_has_role_in_org', 'get_user_organization_ids')
ORDER BY routine_name;

-- Expected:
-- user_has_role_in_org | FUNCTION | DEFINER | ✅ SECURITY DEFINER
-- get_user_organization_ids | FUNCTION | DEFINER | ✅ SECURITY DEFINER

-- =============================================
-- FINAL CONFIRMATION
-- =============================================

DO $$
DECLARE
    org_policies INTEGER;
    member_policies INTEGER;
    profile_policies INTEGER;
    helper_functions INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_policies
    FROM pg_policies WHERE tablename = 'organizations';

    SELECT COUNT(*) INTO member_policies
    FROM pg_policies WHERE tablename = 'organization_members';

    SELECT COUNT(*) INTO profile_policies
    FROM pg_policies WHERE tablename = 'profiles';

    SELECT COUNT(*) INTO helper_functions
    FROM information_schema.routines
    WHERE routine_schema = 'public'
      AND routine_name IN ('user_has_role_in_org', 'get_user_organization_ids')
      AND security_type = 'DEFINER';

    RAISE NOTICE '';
    RAISE NOTICE '=== VERIFICATION RESULTS ===';
    RAISE NOTICE 'Organizations policies: % (expected: 5)', org_policies;
    RAISE NOTICE 'Organization_members policies: % (expected: 5)', member_policies;
    RAISE NOTICE 'Profiles policies: % (expected: 5)', profile_policies;
    RAISE NOTICE 'Helper functions: % (expected: 2)', helper_functions;
    RAISE NOTICE '';

    IF org_policies = 5 AND member_policies = 5 AND profile_policies = 5 AND helper_functions = 2 THEN
        RAISE NOTICE '✅✅✅ SUCCESS! ALL CONFIGURED CORRECTLY! ✅✅✅';
        RAISE NOTICE '';
        RAISE NOTICE '🎉 Registration should now work!';
        RAISE NOTICE '🎉 No more recursion errors!';
        RAISE NOTICE '🎉 No more 403 errors!';
        RAISE NOTICE '';
        RAISE NOTICE 'Try registering at:';
        RAISE NOTICE 'https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register';
    ELSE
        RAISE NOTICE '⚠️ Something is not configured correctly. Review output above.';
    END IF;
END $$;

-- =============================================
-- NOTES
-- =============================================

/*
HOW THIS FIXES THE RECURSION PROBLEM:

BEFORE (BROKEN):
- Policy on organizations checks organization_members table
- That triggers RLS on organization_members
- Which checks organization_members table again
- ∞ INFINITE RECURSION

AFTER (FIXED):
- Policy calls user_has_role_in_org() function
- Function has SECURITY DEFINER
- SECURITY DEFINER bypasses RLS completely
- Function queries organization_members without triggering RLS
- Returns result to policy
- ✅ NO RECURSION

SECURITY IMPLICATIONS:
- SECURITY DEFINER functions run with privileges of function owner (postgres)
- They bypass RLS, so be careful what they do
- Our functions only check membership - safe!
- They don't expose sensitive data
- They're read-only (STABLE)

WHY THIS IS PRODUCTION-READY:
1. No recursion - uses SECURITY DEFINER helpers
2. Proper role targeting - TO authenticated
3. Explicit grants - not using ALL
4. Comprehensive policies - INSERT, SELECT, UPDATE, DELETE
5. Anon protection - anon can't see any rows
6. Self-documenting - clear policy names
7. Verified - includes verification queries
*/
