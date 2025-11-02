-- =============================================
-- FIX INFINITE RECURSION IN RLS POLICIES
-- Run this in Supabase SQL Editor
-- =============================================

-- =============================================
-- STEP 1: DROP ALL EXISTING POLICIES (Clean Slate)
-- =============================================

-- Drop all policies on organization_members
DROP POLICY IF EXISTS "Admins can manage organization members" ON organization_members;
DROP POLICY IF EXISTS "Authenticated users can join organization" ON organization_members;
DROP POLICY IF EXISTS "View organization members" ON organization_members;
DROP POLICY IF EXISTS "Users can insert own membership" ON organization_members;
DROP POLICY IF EXISTS "Members can view organization members" ON organization_members;
DROP POLICY IF EXISTS "Admins can update members" ON organization_members;
DROP POLICY IF EXISTS "Owners can delete members" ON organization_members;

-- =============================================
-- STEP 2: CREATE SECURITY DEFINER HELPER FUNCTION
-- This function bypasses RLS to avoid infinite recursion
-- =============================================

CREATE OR REPLACE FUNCTION user_has_role_in_org(
    check_user_id UUID,
    check_org_id UUID,
    required_roles TEXT[]
)
RETURNS BOOLEAN AS $$
BEGIN
    -- This query bypasses RLS because of SECURITY DEFINER
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

-- =============================================
-- STEP 3: CREATE NEW POLICIES (No Recursion!)
-- =============================================

-- Policy 1: INSERT - Users can insert themselves (for signup)
CREATE POLICY "Users can insert own membership" ON organization_members
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy 2: SELECT - View members of organizations you belong to
CREATE POLICY "View organization members" ON organization_members
    FOR SELECT
    USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Policy 3: UPDATE - Admins and owners can update members
CREATE POLICY "Admins can update members" ON organization_members
    FOR UPDATE
    USING (
        user_has_role_in_org(auth.uid(), organization_id, ARRAY['owner', 'admin'])
    );

-- Policy 4: DELETE - Only owners can delete members
CREATE POLICY "Owners can delete members" ON organization_members
    FOR DELETE
    USING (
        user_has_role_in_org(auth.uid(), organization_id, ARRAY['owner'])
    );

-- =============================================
-- STEP 4: VERIFY POLICIES ARE CORRECT
-- =============================================

SELECT
    policyname,
    cmd as operation,
    CASE
        WHEN cmd = 'INSERT' THEN 'Allow users to create their own membership'
        WHEN cmd = 'SELECT' THEN 'Allow viewing org members'
        WHEN cmd = 'UPDATE' THEN 'Allow admins to update'
        WHEN cmd = 'DELETE' THEN 'Allow owners to delete'
    END as description
FROM pg_policies
WHERE tablename = 'organization_members'
ORDER BY cmd, policyname;

-- Expected result: 4 policies
-- 1. Users can insert own membership (INSERT)
-- 2. View organization members (SELECT)
-- 3. Admins can update members (UPDATE)
-- 4. Owners can delete members (DELETE)

-- =============================================
-- STEP 5: TEST THE FIX
-- =============================================

-- This should return TRUE/FALSE without infinite recursion
-- (Will only work if you have a membership record)
SELECT user_has_role_in_org(
    auth.uid(),
    (SELECT organization_id FROM organization_members WHERE user_id = auth.uid() LIMIT 1),
    ARRAY['owner', 'admin']
) as "I am an admin or owner";

-- =============================================
-- NOTES
-- =============================================

/*
KEY CHANGES:
1. Removed the recursive "Admins can manage organization members" policy
2. Created separate policies for each operation (INSERT, SELECT, UPDATE, DELETE)
3. Added SECURITY DEFINER function to check roles without triggering RLS
4. The helper function bypasses RLS, preventing infinite recursion

WHY THIS FIXES INFINITE RECURSION:
- Old policy: Queries organization_members → triggers policy → queries organization_members → ∞
- New approach: Queries organization_members → calls SECURITY DEFINER function → bypasses RLS → returns result ✅

SECURITY:
- SECURITY DEFINER is safe here because the function only checks membership
- It doesn't allow arbitrary queries
- The function is owned by you (the superuser) so it can read organization_members
*/
