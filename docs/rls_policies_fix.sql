-- =============================================
-- FIX: Add Missing RLS Policies for Signup
-- Run this in Supabase SQL Editor to fix RLS errors
-- =============================================

-- Drop existing policies first (if they exist)
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Authenticated users can create organization" ON organizations;
DROP POLICY IF EXISTS "Owners can update their organization" ON organizations;
DROP POLICY IF EXISTS "Authenticated users can join organization" ON organization_members;
DROP POLICY IF EXISTS "Admins can manage organization members" ON organization_members;

-- =============================================
-- PROFILES TABLE POLICIES
-- =============================================

-- Allow users to insert their own profile during signup
CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid() = id);

-- =============================================
-- ORGANIZATIONS TABLE POLICIES
-- =============================================

-- Allow any authenticated user to create an organization (for signup)
CREATE POLICY "Authenticated users can create organization" ON organizations
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Allow owners to update their organization
CREATE POLICY "Owners can update their organization" ON organizations
    FOR UPDATE USING (
        id IN (
            SELECT organization_id FROM organization_members
            WHERE user_id = auth.uid() AND role = 'owner' AND is_active = TRUE
        )
    );

-- =============================================
-- ORGANIZATION_MEMBERS TABLE POLICIES
-- =============================================

-- Allow authenticated users to join their own organization (for signup)
CREATE POLICY "Authenticated users can join organization" ON organization_members
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Allow admins to manage organization members
CREATE POLICY "Admins can manage organization members" ON organization_members
    FOR ALL USING (
        organization_id IN (
            SELECT organization_id FROM organization_members
            WHERE user_id = auth.uid() AND role IN ('owner', 'admin') AND is_active = TRUE
        )
    );

-- =============================================
-- VERIFICATION
-- =============================================

-- Check that policies were created successfully
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE tablename IN ('organizations', 'profiles', 'organization_members')
ORDER BY tablename, policyname;
