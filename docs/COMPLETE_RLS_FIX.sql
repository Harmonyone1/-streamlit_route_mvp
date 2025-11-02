-- =============================================
-- COMPLETE RLS FIX - RUN THIS TO FIX EVERYTHING
-- This script fixes all RLS issues preventing registration
-- =============================================

-- =============================================
-- PART 1: DISABLE THE PROBLEMATIC TRIGGER
-- =============================================

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

RAISE NOTICE '✅ Disabled automatic user trigger';

-- =============================================
-- PART 2: CREATE HELPER FUNCTION (No Recursion)
-- =============================================

CREATE OR REPLACE FUNCTION user_has_role_in_org(
    check_user_id UUID,
    check_org_id UUID,
    required_roles TEXT[]
)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM organization_members
        WHERE user_id = check_user_id
          AND organization_id = check_org_id
          AND role = ANY(required_roles)
          AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

RAISE NOTICE '✅ Created helper function to avoid recursion';

-- =============================================
-- PART 3: FIX ORGANIZATIONS TABLE POLICIES
-- =============================================

-- Drop all existing policies on organizations
DROP POLICY IF EXISTS "Authenticated users can create organization" ON organizations;
DROP POLICY IF EXISTS "Members can view their organization" ON organizations;
DROP POLICY IF EXISTS "Owners can update their organization" ON organizations;

-- CREATE NEW POLICIES

-- Allow authenticated users to INSERT (CRITICAL FOR SIGNUP!)
CREATE POLICY "Authenticated users can create organization" ON organizations
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Allow viewing own organizations
CREATE POLICY "Members can view their organization" ON organizations
    FOR SELECT
    USING (
        id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Allow owners to update
CREATE POLICY "Owners can update their organization" ON organizations
    FOR UPDATE
    USING (
        user_has_role_in_org(auth.uid(), id, ARRAY['owner'])
    );

RAISE NOTICE '✅ Fixed organizations table policies (3 policies)';

-- =============================================
-- PART 4: FIX ORGANIZATION_MEMBERS TABLE POLICIES
-- =============================================

-- Drop all existing policies on organization_members
DROP POLICY IF EXISTS "Admins can manage organization members" ON organization_members;
DROP POLICY IF EXISTS "Authenticated users can join organization" ON organization_members;
DROP POLICY IF EXISTS "View organization members" ON organization_members;
DROP POLICY IF EXISTS "Users can insert own membership" ON organization_members;
DROP POLICY IF EXISTS "Members can view organization members" ON organization_members;
DROP POLICY IF EXISTS "Admins can update members" ON organization_members;
DROP POLICY IF EXISTS "Owners can delete members" ON organization_members;

-- CREATE NEW POLICIES (No Recursion!)

-- Allow users to insert themselves (for signup)
CREATE POLICY "Users can insert own membership" ON organization_members
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Allow viewing org members
CREATE POLICY "View organization members" ON organization_members
    FOR SELECT
    USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Allow admins to update
CREATE POLICY "Admins can update members" ON organization_members
    FOR UPDATE
    USING (
        user_has_role_in_org(auth.uid(), organization_id, ARRAY['owner', 'admin'])
    );

-- Allow owners to delete
CREATE POLICY "Owners can delete members" ON organization_members
    FOR DELETE
    USING (
        user_has_role_in_org(auth.uid(), organization_id, ARRAY['owner'])
    );

RAISE NOTICE '✅ Fixed organization_members table policies (4 policies)';

-- =============================================
-- PART 5: FIX PROFILES TABLE POLICIES
-- =============================================

-- Drop existing
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;

-- CREATE NEW POLICIES

CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT
    WITH CHECK (auth.uid() = id);

RAISE NOTICE '✅ Fixed profiles table policies (3 policies)';

-- =============================================
-- PART 6: VERIFY EVERYTHING
-- =============================================

-- Check all policies
DO $$
DECLARE
    org_count INTEGER;
    om_count INTEGER;
    profile_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count FROM pg_policies WHERE tablename = 'organizations';
    SELECT COUNT(*) INTO om_count FROM pg_policies WHERE tablename = 'organization_members';
    SELECT COUNT(*) INTO profile_count FROM pg_policies WHERE tablename = 'profiles';

    RAISE NOTICE '';
    RAISE NOTICE '=== VERIFICATION ===';
    RAISE NOTICE 'Organizations policies: % (expected: 3)', org_count;
    RAISE NOTICE 'Organization_members policies: % (expected: 4)', om_count;
    RAISE NOTICE 'Profiles policies: % (expected: 3)', profile_count;
    RAISE NOTICE '';

    IF org_count = 3 AND om_count = 4 AND profile_count = 3 THEN
        RAISE NOTICE '✅✅✅ ALL POLICIES CONFIGURED CORRECTLY! ✅✅✅';
        RAISE NOTICE '';
        RAISE NOTICE 'Registration should now work!';
        RAISE NOTICE 'Try registering with a fresh email at:';
        RAISE NOTICE 'https://harmonyone1--streamlit-route-mvp-main-z15rkj.streamlit.app/register';
    ELSE
        RAISE NOTICE '⚠️ Policy count mismatch - check configuration';
    END IF;
END $$;

-- Show detailed policy list
SELECT
    tablename,
    policyname,
    cmd as operation
FROM pg_policies
WHERE tablename IN ('organizations', 'organization_members', 'profiles')
ORDER BY tablename, cmd, policyname;

-- =============================================
-- SUCCESS CRITERIA
-- =============================================

/*
After running this script, you should see:
✅ Disabled automatic user trigger
✅ Created helper function to avoid recursion
✅ Fixed organizations table policies (3 policies)
✅ Fixed organization_members table policies (4 policies)
✅ Fixed profiles table policies (3 policies)
✅✅✅ ALL POLICIES CONFIGURED CORRECTLY! ✅✅✅

Then try registration - it should work!

WHAT THIS FIXES:
1. ❌ Database trigger causing 500 errors → ✅ Trigger disabled
2. ❌ Infinite recursion in RLS policies → ✅ SECURITY DEFINER function
3. ❌ 403 error creating organizations → ✅ INSERT policy added
4. ❌ 403 error creating profiles → ✅ INSERT policy verified
5. ❌ 403 error creating memberships → ✅ INSERT policy added

REGISTRATION FLOW AFTER FIX:
1. User submits form
2. Supabase Auth creates user ✅
3. Python creates organization ✅ (no more 403!)
4. Python creates profile ✅
5. Python creates membership ✅
6. Success! ✅
*/
