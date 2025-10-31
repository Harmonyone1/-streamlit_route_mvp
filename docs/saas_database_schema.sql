-- RouteFlow SaaS Database Schema
-- Multi-tenant architecture with authentication and billing

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- AUTHENTICATION & USER MANAGEMENT
-- =============================================

-- Organizations (Companies/Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    logo_url TEXT,
    industry TEXT,

    -- Billing
    plan_tier TEXT NOT NULL DEFAULT 'trial' CHECK (plan_tier IN ('trial', 'starter', 'professional', 'enterprise')),
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    subscription_status TEXT DEFAULT 'trialing' CHECK (subscription_status IN ('trialing', 'active', 'past_due', 'canceled', 'paused')),
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,

    -- Settings
    is_active BOOLEAN DEFAULT TRUE,
    settings JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on slug for lookups
CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_stripe_customer ON organizations(stripe_customer_id);

-- User profiles (extends Supabase auth.users)
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    phone TEXT,
    timezone TEXT DEFAULT 'UTC',
    preferences JSONB DEFAULT '{}',

    -- Onboarding
    onboarding_completed BOOLEAN DEFAULT FALSE,
    last_seen_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Organization members (links users to organizations with roles)
CREATE TABLE organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'manager', 'technician')),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    invited_by UUID REFERENCES auth.users(id),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, user_id)
);

CREATE INDEX idx_org_members_org ON organization_members(organization_id);
CREATE INDEX idx_org_members_user ON organization_members(user_id);

-- Invitations
CREATE TABLE invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'manager', 'technician')),
    token TEXT UNIQUE NOT NULL,

    invited_by UUID REFERENCES auth.users(id),
    accepted_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, email)
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);

-- =============================================
-- USAGE TRACKING & BILLING
-- =============================================

-- Usage tracking per organization
CREATE TABLE usage_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    month DATE NOT NULL, -- First day of the month

    -- Counters
    technicians_count INTEGER DEFAULT 0,
    stops_created INTEGER DEFAULT 0,
    routes_optimized INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(organization_id, month)
);

CREATE INDEX idx_usage_org_month ON usage_tracking(organization_id, month);

-- Subscription history
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    stripe_subscription_id TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT NOT NULL,

    plan_tier TEXT NOT NULL,
    status TEXT NOT NULL,

    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_org ON subscriptions(organization_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    stripe_invoice_id TEXT UNIQUE NOT NULL,

    amount_due INTEGER NOT NULL, -- in cents
    amount_paid INTEGER DEFAULT 0,
    currency TEXT DEFAULT 'usd',

    status TEXT NOT NULL CHECK (status IN ('draft', 'open', 'paid', 'void', 'uncollectible')),

    invoice_pdf_url TEXT,
    hosted_invoice_url TEXT,

    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_invoices_org ON invoices(organization_id);
CREATE INDEX idx_invoices_stripe ON invoices(stripe_invoice_id);

-- =============================================
-- UPDATE EXISTING TABLES FOR MULTI-TENANCY
-- =============================================

-- Add organization_id to existing tables
ALTER TABLE technicians ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE stops ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;
ALTER TABLE routes ADD COLUMN organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE;

-- Create indexes for organization lookups
CREATE INDEX idx_technicians_org ON technicians(organization_id);
CREATE INDEX idx_stops_org ON stops(organization_id);
CREATE INDEX idx_routes_org ON routes(organization_id);

-- =============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =============================================

-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE organization_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE technicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE route_stops ENABLE ROW LEVEL SECURITY;

-- Helper function to get user's organization IDs
CREATE OR REPLACE FUNCTION get_user_organization_ids(user_uuid UUID)
RETURNS SETOF UUID AS $$
    SELECT organization_id
    FROM organization_members
    WHERE user_id = user_uuid AND is_active = TRUE;
$$ LANGUAGE SQL STABLE;

-- Profiles: Users can read/update their own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Organizations: Members can view their organization
CREATE POLICY "Members can view their organization" ON organizations
    FOR SELECT USING (
        id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Organization members: View members of own organization
CREATE POLICY "View organization members" ON organization_members
    FOR SELECT USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Technicians: Can only access own organization's technicians
CREATE POLICY "Access own organization technicians" ON technicians
    FOR ALL USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Stops: Can only access own organization's stops
CREATE POLICY "Access own organization stops" ON stops
    FOR ALL USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Routes: Can only access own organization's routes
CREATE POLICY "Access own organization routes" ON routes
    FOR ALL USING (
        organization_id IN (SELECT get_user_organization_ids(auth.uid()))
    );

-- Route stops: Can only access own organization's route stops
CREATE POLICY "Access own organization route_stops" ON route_stops
    FOR ALL USING (
        route_id IN (
            SELECT id FROM routes
            WHERE organization_id IN (SELECT get_user_organization_ids(auth.uid()))
        )
    );

-- =============================================
-- FUNCTIONS & TRIGGERS
-- =============================================

-- Function to create organization for new user
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    new_org_id UUID;
    org_slug TEXT;
BEGIN
    -- Create profile
    INSERT INTO profiles (id, full_name, avatar_url)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        NEW.raw_user_meta_data->>'avatar_url'
    );

    -- Generate organization slug from email
    org_slug := LOWER(REGEXP_REPLACE(
        SPLIT_PART(NEW.email, '@', 1),
        '[^a-z0-9]+', '-', 'g'
    )) || '-' || SUBSTRING(NEW.id::TEXT, 1, 8);

    -- Create organization
    INSERT INTO organizations (name, slug, trial_ends_at)
    VALUES (
        COALESCE(NEW.raw_user_meta_data->>'company_name', 'My Company'),
        org_slug,
        NOW() + INTERVAL '14 days'
    )
    RETURNING id INTO new_org_id;

    -- Add user as owner
    INSERT INTO organization_members (organization_id, user_id, role)
    VALUES (new_org_id, NEW.id, 'owner');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to handle new user signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to tables
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_org_members_updated_at BEFORE UPDATE ON organization_members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function to increment usage counters
CREATE OR REPLACE FUNCTION increment_usage(
    org_id UUID,
    counter_name TEXT,
    increment_by INTEGER DEFAULT 1
)
RETURNS VOID AS $$
DECLARE
    current_month DATE;
BEGIN
    current_month := DATE_TRUNC('month', NOW());

    -- Insert or update usage record
    INSERT INTO usage_tracking (organization_id, month, stops_created, routes_optimized, api_calls)
    VALUES (
        org_id,
        current_month,
        CASE WHEN counter_name = 'stops' THEN increment_by ELSE 0 END,
        CASE WHEN counter_name = 'routes' THEN increment_by ELSE 0 END,
        CASE WHEN counter_name = 'api' THEN increment_by ELSE 0 END
    )
    ON CONFLICT (organization_id, month)
    DO UPDATE SET
        stops_created = usage_tracking.stops_created +
            CASE WHEN counter_name = 'stops' THEN increment_by ELSE 0 END,
        routes_optimized = usage_tracking.routes_optimized +
            CASE WHEN counter_name = 'routes' THEN increment_by ELSE 0 END,
        api_calls = usage_tracking.api_calls +
            CASE WHEN counter_name = 'api' THEN increment_by ELSE 0 END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- PLAN LIMITS
-- =============================================

CREATE TABLE plan_limits (
    plan_tier TEXT PRIMARY KEY,
    max_technicians INTEGER,  -- NULL = unlimited
    max_stops_per_month INTEGER,  -- NULL = unlimited
    max_routes_per_month INTEGER,  -- NULL = unlimited
    features JSONB DEFAULT '{}'
);

INSERT INTO plan_limits (plan_tier, max_technicians, max_stops_per_month, max_routes_per_month, features) VALUES
('trial', 5, 500, NULL, '{"email_dispatch": true, "google_sheets": false, "api_access": false}'),
('starter', 5, 500, NULL, '{"email_dispatch": true, "google_sheets": true, "api_access": false}'),
('professional', 20, 2000, NULL, '{"email_dispatch": true, "google_sheets": true, "api_access": true, "priority_support": true}'),
('enterprise', NULL, NULL, NULL, '{"email_dispatch": true, "google_sheets": true, "api_access": true, "priority_support": true, "white_label": true, "dedicated_support": true}');

-- =============================================
-- ANALYTICS & EVENTS
-- =============================================

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',

    ip_address INET,
    user_agent TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_events_org ON events(organization_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_created ON events(created_at);

-- =============================================
-- SAMPLE DATA FOR TESTING
-- =============================================

-- Note: Sample data will be created when users sign up
-- The trigger will automatically create organization and assign owner role

COMMENT ON TABLE organizations IS 'Companies/tenants using the platform';
COMMENT ON TABLE profiles IS 'Extended user profiles (linked to auth.users)';
COMMENT ON TABLE organization_members IS 'Links users to organizations with roles';
COMMENT ON TABLE usage_tracking IS 'Tracks monthly usage for billing';
COMMENT ON TABLE plan_limits IS 'Defines limits for each subscription tier';
COMMENT ON TABLE events IS 'Audit log and analytics events';
