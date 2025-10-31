# 🚚 Streamlit Route Optimization Platform

A full-featured route optimization and dispatch platform for field service operations, built with Streamlit, Google OR-Tools, and Supabase.

![Platform Status](https://img.shields.io/badge/status-beta-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## 🎯 Overview

This platform helps field service companies optimize technician routes using advanced algorithms (Vehicle Routing Problem with Time Windows). It provides an intuitive web interface for operations managers to plan, optimize, visualize, and dispatch daily routes.

### Key Features

- **🗺️ Route Optimization** - Multi-vehicle routing with OR-Tools
- **⏰ Time Windows** - Respect customer appointment windows
- **📍 Interactive Maps** - Folium-based route visualization
- **👥 Technician Management** - Skills, availability, and assignments
- **📊 Dashboard** - Real-time route tracking and metrics
- **💾 Database Backend** - PostgreSQL via Supabase
- **📥 CSV Export** - Download optimized routes

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  OR-Tools Engine │────▶│  Supabase DB    │
│   (Frontend)    │     │  (Optimization)  │     │  (PostgreSQL)   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
        │
        ▼
┌─────────────────┐
│  Folium Maps    │
│  (Visualization)│
└─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Supabase account (free tier works)
- Git

### Installation

```bash
# Clone the repository
cd streamlit_route_mvp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Supabase credentials
```

### Configure Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Copy your project URL and anon key
3. Run SQL from `docs/database_schema.sql` in Supabase SQL Editor
4. Add credentials to `.env` or `.streamlit/secrets.toml`

### Run Locally

```bash
streamlit run main.py
```

Visit `http://localhost:8501` in your browser.

## 📖 Documentation

- **[Setup Guide](docs/SETUP_GUIDE.md)** - Complete installation and configuration
- **[Database Schema](docs/database_schema.sql)** - PostgreSQL table definitions
- **[Architecture](docs/architecture.md)** - System design and data flow
- **[User Stories](docs/user_stories.md)** - Feature requirements
- **[API Integration](docs/api_integration.md)** - External service integration
- **[Deployment Guide](docs/deployment_guide.md)** - Production deployment

## 📁 Project Structure

```
streamlit_route_mvp/
├── main.py                      # Home page and navigation
├── pages/
│   ├── dashboard.py             # Route overview and metrics
│   ├── operations.py            # Route creation and optimization
│   ├── admin.py                 # User and system management
│   └── technician.py            # Mobile-friendly technician view
├── utils/
│   ├── supabase_client.py       # Database operations
│   ├── optimization.py          # OR-Tools route optimization
│   ├── maps.py                  # Folium map visualization
│   └── email_dispatch.py        # Dispatch notifications
├── data/
│   └── sample_data.xlsx         # Sample dataset
├── docs/
│   ├── database_schema.sql      # Database setup
│   └── SETUP_GUIDE.md           # Installation guide
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Streamlit |
| **Optimization** | Google OR-Tools |
| **Database** | PostgreSQL (Supabase) |
| **Maps** | Folium + OpenStreetMap |
| **Data** | Pandas, NumPy |
| **Language** | Python 3.8+ |

## 💡 Usage

### 1. Add Technicians

Go to **Operations** → Sidebar → Add technicians to your team.

### 2. Add Stops

In **Operations** → Stops Management tab:
- Use quick add form in sidebar
- Import from Excel/CSV
- Manually enter addresses with lat/lng

### 3. Optimize Routes

In **Operations** → Optimization tab:
- Select date
- Choose technicians
- Click "Optimize Routes"
- Wait for results (~30 seconds)

### 4. View Results

- **Map View** - Color-coded routes with numbered stops
- **Route Details** - Stop order, arrival times, service duration
- **CSV Export** - Download for technician dispatch

### 5. Monitor Dashboard

Visit **Dashboard** to see:
- Active routes
- Route status (draft, dispatched, in progress, completed)
- Performance metrics

## 🗺️ Features by Page

### Home (`main.py`)
- Platform overview
- System status checks
- Quick navigation
- Setup instructions

### Dashboard (`pages/dashboard.py`)
- Route summary by date
- Status indicators
- Quick actions
- System health

### Operations (`pages/operations.py`)
- Stop management
- Technician selection
- Route optimization
- Map visualization
- CSV export

### Admin (`pages/admin.py`)
- User management (planned)
- System configuration (planned)
- Settings (planned)

### Technician (`pages/technician.py`)
- Mobile-friendly view (planned)
- Route details (planned)
- Check-in/completion (planned)

## 🎯 Optimization Algorithm

Uses Google OR-Tools to solve the **Vehicle Routing Problem with Time Windows (VRPTW)**:

- **Objective:** Minimize total travel time
- **Constraints:**
  - Time windows for each stop
  - Service duration at each location
  - Vehicle capacity (technician work hours)
  - Start/end depot (configurable)

**Algorithm:** Guided Local Search with Path Cheapest Arc heuristic

## 📊 Database Schema

Key tables:
- `users` - System users with roles
- `technicians` - Field technicians
- `stops` - Service locations
- `routes` - Optimized route plans
- `route_stops` - Junction table with stop order
- `optimization_history` - Analytics log
- `dispatch_log` - Dispatch tracking

See `docs/database_schema.sql` for complete schema.

## 🚀 Deployment

### Streamlit Cloud (Recommended)

1. Push code to GitHub
2. Connect at [share.streamlit.io](https://share.streamlit.io)
3. Add secrets in dashboard:
   ```toml
   [supabase]
   url = "your-url"
   key = "your-key"
   ```
4. Deploy!

### Docker (Alternative)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "main.py"]
```

### Other Options
- AWS EC2 / Azure VM
- Heroku
- Google Cloud Run
- Self-hosted server

## 🔐 Security

- Use environment variables for secrets
- Enable Row Level Security (RLS) in Supabase
- Use HTTPS in production
- Implement authentication (Phase 1 expansion)
- Rotate API keys regularly

## 🛣️ Roadmap

### Phase 1: Core Platform ✅
- [x] Supabase integration
- [x] OR-Tools optimization
- [x] Map visualization
- [x] Operations workflow
- [x] Dashboard

### Phase 2: Spreadsheet Integration ✅
- [x] Google Sheets import/export
- [x] Excel upload/download
- [x] Bidirectional sync
- [x] Template files
- [x] Data validation
- [x] Batch import

### Phase 3: Dispatch & Communication ✅
- [x] Email notifications with HTML
- [x] ICS calendar attachments
- [x] Outlook calendar integration (Microsoft Graph)
- [x] Mobile-friendly technician view
- [x] Check-in and completion tracking
- [x] Route navigation
- [x] Job notes

### Phase 4: Analytics (Next)
- [ ] Historical performance
- [ ] Executive dashboards
- [ ] Efficiency metrics
- [ ] Route heatmaps
- [ ] Performance reports

### Phase 5: Advanced (Future)
- [ ] Real-time traffic
- [ ] Predictive scheduling
- [ ] Machine learning ETA
- [ ] API for integrations

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Issues:** Open GitHub issue
- **Docs:** See `docs/` folder
- **Setup:** Read `docs/SETUP_GUIDE.md`

## 🙏 Acknowledgments

- **Google OR-Tools** - Optimization engine
- **Streamlit** - Web framework
- **Supabase** - Backend platform
- **Folium** - Map visualization

---

**Built with ❤️ using Streamlit and OR-Tools**

For the complete implementation plan, see the project documentation.
