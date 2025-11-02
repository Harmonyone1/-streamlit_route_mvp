-- =============================================
-- FIX ORGANIZATIONS TABLE RLS POLICIES
-- Allows authenticated users to create organizations during signup
-- =============================================

-- =============================================
-- STEP 1: CHECK CURRENT STATE
-- =============================================

-- Show current policies on organizations table
SELECT
    policyname,
    cmd as operation,
    qual as using_expression,
    with_check as with_check_expression
FROM pg_policies
WHERE tablename = 'organizations'
ORDER BY cmd, policyname;

-- =============================================
-- STEP 2: DROP EXISTING POLICIES
-- =============================================

DROP POLICY IF EXISTS "Authenticated users can create organization" ON organizations;
DROP POLICY IF EXISTS "Members can view their organization" ON organizations;
DROP POLICY IF EXISTS "Owners can update their organization" ON organizations;

-- =============================================
-- STEP 3: CREATE CORRECT POLICIES
-- =============================================

-- Policy 1: INSERT - Any authenticated user can create organization (for signup)
-- This is CRITICAL for registration to work!
CREATE POLICY "Authenticated users can create organization" ON organizations
    FOR INSERT
    WITH CHECK (auth.uid() IS NOT NULL);

-- Policy 2: SELECT - Users can view organizations they belong to
CREATE POLICY "Members can view their organization" ON organizations
    FOR SELECT
    USING (
        id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Policy 3: UPDATE - Only owners can update their organization
CREATE POLICY "Owners can update their organization" ON organizations
    FOR UPDATE
    USING (
        id IN (
            SELECT organization_id
            FROM organization_members
            WHERE user_id = auth.uid()
              AND role = 'owner'
              AND is_active = TRUE
        )
    );

-- =============================================
-- STEP 4: VERIFY POLICIES WERE CREATED
-- =============================================

SELECT
    policyname,
    cmd as operation,
    CASE cmd
        WHEN 'INSERT' THEN '✅ Allows signup'
        WHEN 'SELECT' THEN '✅ Allows viewing own org'
        WHEN 'UPDATE' THEN '✅ Allows owner updates'
    END as purpose
FROM pg_policies
WHERE tablename = 'organizations'
ORDER BY cmd, policyname;

-- Expected: 3 policies
-- 1. Authenticated users can create organization (INSERT)
-- 2. Members can view their organization (SELECT)
-- 3. Owners can update their organization (UPDATE)

-- =============================================
-- STEP 5: TEST THE INSERT POLICY
-- =============================================

-- This will test if an authenticated user can INSERT
-- (Will only work if you're currently authenticated)
SELECT
    CASE
        WHEN auth.uid() IS NOT NULL THEN '✅ You are authenticated - INSERT should work'
        ELSE '❌ Not authenticated - cannot test'
    END as auth_status;

-- =============================================
-- IMPORTANT NOTES
-- =============================================

/*
WHY THE 403 ERROR OCCURRED:
- The organizations table had RLS enabled
- But there was no INSERT policy allowing authenticated users to create organizations
- Result: 403 Forbidden when trying to INSERT

THE FIX:
- Added INSERT policy with WITH CHECK (auth.uid() IS NOT NULL)
- This allows ANY authenticated user to create an organization
- Perfect for signup flow where new users need to create their org

SECURITY:
- This is safe because:
  1. User must be authenticated (have valid JWT token)
  2. User can only create organizations, not modify others' data
  3. Once created, they become the owner via organization_members
  4. Owners can then manage their organization
*/
