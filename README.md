# ITSM Tickets Dashboard

An interactive ITSM analytics dashboard built with **Streamlit**, designed to support operational decision‑making through advanced SLA, performance, and geospatial analysis.

This project demonstrates strong capabilities in:
- Data engineering (cleaning, transformation, time metrics)
- Operational analytics (SLA, MTTR, MTBF, Root Cause)
- Geospatial visualization (cluster maps, heatmaps)
- UI/UX for analytical dashboards
- Python development and Streamlit application design

## Features

### KPI & SLA Analytics
- SLA Met %
- MTTR (Mean Time to Resolve)
- MTBF (Mean Time Between Failures)
- Deadline % utilization

### Technician & Root Cause Performance
- Avg Total RT (hours)
- Avg Elapsed RT (SLA hours)
- Avg Work Time
- Overdue % (Service Performance Overdued)
- Technician ranking tables
- Root Cause impact analysis

### Geospatial Analysis
- Cluster map of incidents
- Heatmap of incident density
- Aggregation by municipality (gmina), county (powiat), and voivodeship (województwo)

### Advanced Filtering
- Date range
- SLA breach only
- Category, Client, Technician
- Root Cause
- Resolution time sliders
- Deadline % threshold

### Data Processing
- Automatic conversion of HH:MM:SS → hours
- Auto‑refresh with TTL caching
- Manual **“Refresh Data”** button
- Cleaning of Root Cause values

---

## Project Structure
itsm-dashboard/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── data/
    ├── tickets.xlsx
    ├── tickets_by_gmina.xlsx

