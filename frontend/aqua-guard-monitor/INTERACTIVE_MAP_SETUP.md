# Required Dependencies for Interactive Map Feature

## Frontend Dependencies (React)

### Core Mapping Libraries
```bash
npm install react-leaflet leaflet react-leaflet-cluster
npm install @types/leaflet  # TypeScript support
```

### Material-UI Components
```bash
npm install @mui/material @emotion/react @emotion/styled
npm install @mui/icons-material
npm install @mui/x-charts  # Alternative to recharts
```

### Charts and Visualization
```bash
npm install recharts
npm install @types/recharts  # TypeScript support
```

### Leaflet CSS (Already handled in components)
The components already import the required CSS:
```javascript
import 'leaflet/dist/leaflet.css';
```

## Package Installation Commands

### All-in-one installation:
```bash
cd frontend/aqua-guard-monitor
npm install react-leaflet leaflet react-leaflet-cluster @types/leaflet @mui/material @emotion/react @emotion/styled @mui/icons-material recharts @types/recharts
```

### Individual installations:
```bash
# Mapping
npm install react-leaflet leaflet react-leaflet-cluster @types/leaflet

# UI Components  
npm install @mui/material @emotion/react @emotion/styled @mui/icons-material

# Charts
npm install recharts @types/recharts
```

## Features Implemented

### 1. Interactive Map Component (`InteractiveMap.tsx`)
- **React-Leaflet** for map rendering
- **Clustered markers** with color coding based on water quality
- **Interactive popups** showing detailed information
- **Statistics cards** with real-time data
- **Quality legend** for understanding color coding
- **Responsive design** with Material-UI

### 2. Dashboard Component (`Dashboard.tsx`)
- **Recharts** for data visualization (pie charts, bar charts, line charts)
- **Material-UI cards** for KPI display
- **Quality distribution analysis**
- **HMPI trend analysis** over time
- **Progress indicators** for each quality category

### 3. Map Page Component (`MapPage.tsx`)
- **Tabbed interface** switching between Dashboard and Map
- **Material-UI AppBar** for navigation
- **Responsive container** layout

### 4. Backend API Endpoint (`map_views.py`)
- **Django REST endpoint** at `/api/v1/map-data/`
- **Sample data generation** with coordinates and HMPI values
- **Statistics calculation** for dashboard
- **JSON response** with map data and summary stats

## Navigation

The interactive map is accessible at:
```
http://localhost:3000/map
```

## Data Flow

1. **Frontend** makes API call to `/api/v1/map-data/`
2. **Django backend** returns JSON with coordinates, HMPI values, and statistics
3. **React components** render map markers and dashboard charts
4. **User interaction** through map popups and dashboard filters

## Color Coding System

- 🟢 **Excellent** (HMPI < 25): Dark Green
- 🟡 **Good** (HMPI 25-50): Light Green  
- 🟠 **Poor** (HMPI 50-75): Orange
- 🔴 **Very Poor** (HMPI 75-100): Red Orange
- ⚫ **Unsuitable** (HMPI > 100): Red

## Next Steps

1. Install the dependencies using the commands above
2. Update the map endpoint to use real data from your database
3. Add user authentication to the map routes
4. Implement filtering and search functionality
5. Add real-time data updates