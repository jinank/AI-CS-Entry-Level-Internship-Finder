# AI/CS Entry-Level & Internship Finder

## Overview

This is a Python Streamlit application that helps users search for AI, ML, Data Science, and Software Engineering internships and entry-level roles using the JSearch API. It's built for students and recent graduates seeking roles in Fall 2025, Spring 2026, and Summer 2026.

## System Architecture

### Frontend
- **Framework**: Streamlit
- **Port**: Runs on port 5000 with headless configuration
- **Layout**: Wide layout with form-based input and responsive columns
- **Interface**: Minimal UI with tooltips and clean design

### Backend
- **API**: JSearch API (via RapidAPI)
- **Processing**: Pandas for DataFrame handling
- **Session State**: Uses Streamlit session state for storing search results
- **Query Logic**: Dynamically constructed based on user input

### Design Highlights
- Modular design (app.py, utils.py)
- API-driven architecture (not scraping)
- Smart filters for job type and remote jobs
- Custom job cards with save/apply functionality

## Core Modules

### app.py
- Streamlit UI and form logic
- Displays results and handles state

### utils.py
- Helper functions for formatting and flagging remote jobs

## Data Schema
Each job entry is stored as a row in a pandas DataFrame with:
- Job Title
- Company
- Location
- Description
- Apply Link
- Remote Job Indicator

## Workflow

1. User submits job title/location
2. JSearch API is queried with enhanced filters
3. Results formatted and stored in session
4. Displayed interactively with save/export options

## Dependencies

### Python Packages
- streamlit (>=1.46.0)
- pandas (>=2.3.0)
- requests (>=2.32.4)

### Services
- JSearch API via RapidAPI

## Deployment

### Replit
- **Python**: 3.11
- **Run**: `streamlit run app.py --server.port 5000`
- Configured for autoscaling with global IP binding

## Enhancements (June 24, 2025)
- Replaced scraping with JSearch API
- Added job type filter (Internship, Entry-Level, Both)
- Remote-only job toggle
- Smart keyword expansion for seasonal searches
- Save and export results
- UI improvements

## Changelog
```
- June 24, 2025: Major update with JSearch API and student-centric features
```

## Technical Notes

### Bot Detection Handling
- Uses browser-mimicking headers and retry logic

### Performance
- Efficient use of Pandas
- Session-aware caching to reduce redundant queries