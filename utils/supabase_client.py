"""
Supabase client configuration and database operations
"""
import os
from supabase import create_client, Client
import streamlit as st

def get_supabase_client() -> Client:
    """
    Initialize and return Supabase client using environment variables or Streamlit secrets
    """
    try:
        # Try to get from Streamlit secrets first (for deployment)
        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            supabase_url = st.secrets['supabase']['url']
            supabase_key = st.secrets['supabase']['key']
        else:
            # Fall back to environment variables (for local development)
            supabase_url = os.environ.get('SUPABASE_URL', 'https://syrrhunexglfceovmdrd.supabase.co')
            supabase_key = os.environ.get('SUPABASE_KEY')

        if not supabase_key:
            st.error("Supabase key not configured. Please set SUPABASE_KEY environment variable or add to secrets.")
            return None

        return create_client(supabase_url, supabase_key)
    except Exception as e:
        st.error(f"Error connecting to Supabase: {str(e)}")
        return None

def init_database_schema(client: Client):
    """
    Initialize database tables if they don't exist
    This is a reference - actual table creation should be done via Supabase SQL editor
    """
    # Note: This is documentation of the schema that should be created in Supabase
    schema = {
        'users': '''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('executive', 'operations', 'admin', 'technician')),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''',
        'technicians': '''
            CREATE TABLE IF NOT EXISTS technicians (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                user_id UUID REFERENCES users(id),
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                skills TEXT[],
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''',
        'stops': '''
            CREATE TABLE IF NOT EXISTS stops (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                latitude DECIMAL(10, 8),
                longitude DECIMAL(11, 8),
                service_duration INTEGER NOT NULL,
                time_window_start TIME,
                time_window_end TIME,
                priority INTEGER DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''',
        'routes': '''
            CREATE TABLE IF NOT EXISTS routes (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name TEXT NOT NULL,
                date DATE NOT NULL,
                technician_id UUID REFERENCES technicians(id),
                status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'optimized', 'dispatched', 'in_progress', 'completed')),
                total_distance DECIMAL(10, 2),
                total_duration INTEGER,
                created_by UUID REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''',
        'route_stops': '''
            CREATE TABLE IF NOT EXISTS route_stops (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
                stop_id UUID REFERENCES stops(id),
                stop_order INTEGER NOT NULL,
                estimated_arrival TIME,
                actual_arrival TIME,
                completed BOOLEAN DEFAULT FALSE,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        '''
    }
    return schema

# Database operation helpers
def get_all_technicians(client: Client):
    """Fetch all active technicians"""
    try:
        response = client.table('technicians').select('*').eq('active', True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching technicians: {str(e)}")
        return []

def get_all_stops(client: Client):
    """Fetch all stops"""
    try:
        response = client.table('stops').select('*').execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching stops: {str(e)}")
        return []

def create_stop(client: Client, stop_data: dict):
    """Create a new stop"""
    try:
        response = client.table('stops').insert(stop_data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error creating stop: {str(e)}")
        return None

def create_route(client: Client, route_data: dict):
    """Create a new route"""
    try:
        response = client.table('routes').insert(route_data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error creating route: {str(e)}")
        return None

def update_route(client: Client, route_id: str, updates: dict):
    """Update a route"""
    try:
        response = client.table('routes').update(updates).eq('id', route_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating route: {str(e)}")
        return None

def get_routes_by_date(client: Client, date: str):
    """Get all routes for a specific date"""
    try:
        response = client.table('routes').select('*, technician:technicians(*)').eq('date', date).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching routes: {str(e)}")
        return []
