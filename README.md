# AI/CS Entry‑Level & Internship Finder

## Overview
A lightweight Streamlit app that lets students and new grads hunt for AI, ML, Data‑Science and Software‑Engineering **internships** and **entry‑level** roles.  
Powered by the **JSearch API** and tuned for Fall 2025, Spring 2026 and Summer 2026 recruiting cycles.

## System Architecture
### Front‑end
| Item | Detail |
|------|--------|
| **Framework** | Streamlit |
| **Port** | Runs on `5000` (headless enabled) |
| **Layout** | Wide, form‑based input with responsive columns |
| **Interface** | Minimal UI, tool‑tips, expandable _Quick Search_ panel |

### Back‑end
| Item | Detail |
|------|--------|
| **API** | JSearch (via RapidAPI) |
| **Processing** | Pandas DataFrames |
| **State** | Streamlit `st.session_state` |
| **Query Logic** | Dynamically built from user input & quick‑search buttons |

### Design Highlights
* Modular files (`app.py`, `utils.py`, etc.)
* **API‑driven** (no web‑scraping)
* Smart filters for **job type** and an **enhanced location filter**<br>  *(On‑site Only | Remote Only | Include Remote)*
* Custom job cards, table view, and save/apply workflow
* One‑click _Quick Search_ buttons for popular roles & seasons

## Core Modules
| File | Responsibility |
|------|----------------|
| **app.py** | Streamlit UI, form logic, results display |
| **utils.py** | Helper functions (remote‑job flag, formatting) |

## Data Schema
Every job is a single DataFrame row:

| Column | Description |
|--------|-------------|
| Job Title | Role name |
| Company | Employer |
| Location | City / Remote |
| Description | Short blurb |
| Apply Link | URL |
| Remote Job | 🏠 flag |
| Tags | Auto‑categorised theme |
| QueryFlag | Season / entry‑level label |

## Typical Workflow
1. User enters keywords or hits a **Quick Search** shortcut  
2. App constructs an enhanced query (keywords + season + location mode)  
3. JSearch API returns matching postings  
4. Jobs are tagged, cached & rendered (card or table)  

## Dependencies
### Python Packages
```
streamlit >=1.46  
pandas    >=2.3  
requests  >=2.32
```
### Services
* JSearch API (RapidAPI key required)

## Deployment
### Streamlit
* **Runtime**: Python 3.11  
* **Command**:
```bash
streamlit run app.py --server.port 5000
```
* Autoscale & open‑to‑web enabled

## Enhancements (July 6 2025)
* Added **location filter modes** (On‑site / Remote / Include)  
* Quick‑search panel with **remote‑only** shortcuts  
* Table view with batch‑apply & CSV export  
* Email‑digest option for sending results

## Changelog
```
2025‑06‑24  Major rewrite – switched to JSearch API  
2025‑07‑06  Remote filter modes, quick‑search revamp, table view
2025-07-10  Re-developed the user interface for public deployment
```

## Technical Notes
### Bot‑Detection
Retry logic with browser‑like headers keeps the API happy.

### Performance
* Pandas operations are vectorised  
* Results cached in session to avoid duplicate queries
