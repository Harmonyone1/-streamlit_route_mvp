-- ============================================
-- Streamlit Route Optimization Platform
-- Database Schema for Supabase (PostgreSQL)
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: users
-- Stores all system users with role-based access
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('executive', 'operations', 'admin', 'technician')),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: technicians
-- Stores technician-specific information
-- ============================================
CREATE TABLE IF NOT EXISTS technicians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    skills TEXT[],
    max_stops_per_day INTEGER DEFAULT 20,
    work_start_time TIME DEFAULT '08:00:00',
    work_end_time TIME DEFAULT '17:00:00',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: stops
-- Stores all service stop locations
-- ============================================
CREATE TABLE IF NOT EXISTS stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    service_duration INTEGER NOT NULL DEFAULT 30, -- in minutes
    time_window_start TIME,
    time_window_end TIME,
    priority INTEGER DEFAULT 1 CHECK (priority BETWEEN 1 AND 5),
    notes TEXT,
    customer_name TEXT,
    customer_phone TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: routes
-- Stores route definitions and metadata
-- ============================================
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    date DATE NOT NULL,
    technician_id UUID REFERENCES technicians(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'optimized', 'dispatched', 'in_progress', 'completed', 'cancelled')),
    total_distance DECIMAL(10, 2), -- in miles or km
    total_duration INTEGER, -- in minutes
    optimization_score DECIMAL(5, 2), -- efficiency rating
    start_location TEXT,
    end_location TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: route_stops
-- Junction table linking routes to stops with order
-- ============================================
CREATE TABLE IF NOT EXISTS route_stops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    stop_id UUID REFERENCES stops(id) ON DELETE CASCADE,
    stop_order INTEGER NOT NULL,
    estimated_arrival TIME,
    estimated_departure TIME,
    actual_arrival TIMESTAMP WITH TIME ZONE,
    actual_departure TIMESTAMP WITH TIME ZONE,
    completed BOOLEAN DEFAULT FALSE,
    distance_from_previous DECIMAL(10, 2), -- in miles or km
    travel_time_from_previous INTEGER, -- in minutes
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(route_id, stop_order)
);

-- ============================================
-- TABLE: optimization_history
-- Logs optimization runs for analytics
-- ============================================
CREATE TABLE IF NOT EXISTS optimization_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE NOT NULL,
    num_stops INTEGER,
    num_technicians INTEGER,
    total_distance DECIMAL(10, 2),
    total_duration INTEGER,
    optimization_time DECIMAL(10, 3), -- seconds
    algorithm_params JSONB,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- TABLE: dispatch_log
-- Tracks when and how routes were dispatched
-- ============================================
CREATE TABLE IF NOT EXISTS dispatch_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    technician_id UUID REFERENCES technicians(id),
    dispatch_method TEXT CHECK (dispatch_method IN ('email', 'calendar', 'sms', 'app')),
    dispatch_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_time TIMESTAMP WITH TIME ZONE,
    notes TEXT
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_routes_date ON routes(date);
CREATE INDEX IF NOT EXISTS idx_routes_technician ON routes(technician_id);
CREATE INDEX IF NOT EXISTS idx_routes_status ON routes(status);
CREATE INDEX IF NOT EXISTS idx_route_stops_route ON route_stops(route_id);
CREATE INDEX IF NOT EXISTS idx_route_stops_stop ON route_stops(stop_id);
CREATE INDEX IF NOT EXISTS idx_stops_location ON stops(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_technicians_active ON technicians(active);

-- ============================================
-- ROW LEVEL SECURITY (RLS) Policies
-- Enable RLS on all tables
-- ============================================
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE technicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
ALTER TABLE route_stops ENABLE ROW LEVEL SECURITY;
ALTER TABLE optimization_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE dispatch_log ENABLE ROW LEVEL SECURITY;

-- ============================================
-- Example RLS Policies (customize based on needs)
-- ============================================

-- Allow authenticated users to read all data
CREATE POLICY "Allow read access to authenticated users" ON users
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read access to authenticated users" ON technicians
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read access to authenticated users" ON stops
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read access to authenticated users" ON routes
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Allow read access to authenticated users" ON route_stops
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins and operations can insert/update
CREATE POLICY "Allow write access to admins and operations" ON stops
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow write access to admins and operations" ON routes
    FOR ALL USING (auth.role() = 'authenticated');

-- ============================================
-- FUNCTIONS for automation
-- ============================================

-- Update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_technicians_updated_at BEFORE UPDATE ON technicians
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_stops_updated_at BEFORE UPDATE ON stops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_route_stops_updated_at BEFORE UPDATE ON route_stops
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA (optional - for testing)
-- ============================================

-- Insert sample users
INSERT INTO users (email, name, role) VALUES
    ('admin@company.com', 'Admin User', 'admin'),
    ('operations@company.com', 'Operations Manager', 'operations'),
    ('exec@company.com', 'Executive User', 'executive')
ON CONFLICT (email) DO NOTHING;

-- Insert sample technicians
INSERT INTO technicians (name, email, phone, skills) VALUES
    ('John Smith', 'john@company.com', '555-0101', ARRAY['HVAC', 'Plumbing']),
    ('Jane Doe', 'jane@company.com', '555-0102', ARRAY['Electrical', 'HVAC']),
    ('Bob Johnson', 'bob@company.com', '555-0103', ARRAY['Plumbing', 'General'])
ON CONFLICT DO NOTHING;

-- Insert sample stops
INSERT INTO stops (name, address, service_duration, time_window_start, time_window_end) VALUES
    ('ABC Corp', '123 Main St, City, ST 12345', 45, '09:00', '12:00'),
    ('XYZ Industries', '456 Oak Ave, City, ST 12345', 30, '10:00', '14:00'),
    ('Smith Residence', '789 Pine Rd, City, ST 12345', 60, '13:00', '17:00')
ON CONFLICT DO NOTHING;
