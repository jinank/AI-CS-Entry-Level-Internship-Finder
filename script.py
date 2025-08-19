import requests
import pandas as pd
from pyairtable import Api
import streamlit as st
from datetime import datetime
import os

# ----------------- Airtable Config -------------------
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY") or "your_airtable_api_key"
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID") or "your_base_id"
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME") or "your_table_name"
api = Api(AIRTABLE_API_KEY)
airtable = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

# ----------------- JSearch API Config ----------------
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY") or "your_jsearch_api_key"
headers = {
    "X-RapidAPI-Key": JSEARCH_API_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
}

# ----------------- Fetch Jobs Function ----------------
def fetch_jobs():
    query = "machine learning intern"
    url = "https://jsearch.p.rapidapi.com/search"
    params = {
        "query": query,
        "page": "1",
        "num_pages": "1",
        "date_posted": "last_3_days"  # Previously: 'today'
    }

    # Print API request for debugging
    st.write("🔗 API Request URL:")
    st.code(f"{url}?query={params['query']}&page={params['page']}&num_pages={params['num_pages']}&date_posted={params['date_posted']}")

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    jobs = data.get("data", [])[:10]  # Hard limit: 10 results
    filtered_jobs = []

    for job in jobs:
        title = job.get("job_title", "")
        description = job.get("job_description", "")
        if "2026" not in title and "2026" not in description:
            continue

        # Check for duplicates in Airtable
        existing = airtable.all(formula=f"{{Title}} = '{title}'")
        if existing:
            continue

        record = {
            "Title": title,
            "Company": job.get("employer_name", ""),
            "Location": job.get("job_city", ""),
            "Industry": job.get("job_employment_type", ""),
            "Source": job.get("job_apply_link") or job.get("job_google_link"),
            "Posting Date": job.get("job_posted_at_datetime_utc", "")[:10],
            "Internship Type": job.get("job_employment_type", ""),
            "Salary Range": job.get("job_salary_currency", "") + " " + str(job.get("job_min_salary", "")) if job.get("job_min_salary") else "",
            "Job Description": job.get("job_description", ""),
            "Link": job.get("job_apply_link") or job.get("job_google_link"),
            "Status": "PENDING"
        }
        filtered_jobs.append(record)

    st.write(f"📦 Filtered {len(filtered_jobs)} job(s) with '2026' in title/description and no duplicates.")
    return pd.DataFrame(filtered_jobs)

# ----------------- Upload to Airtable ----------------
def upload_to_airtable(df):
    for _, row in df.iterrows():
        airtable.create(row.to_dict())
    st.success(f"✅ Uploaded {len(df)} new job(s) to Airtable.")

# ----------------- Streamlit Interface ----------------
st.title("AI/CS Internship Finder 🚀")

if st.button("Fetch Latest Jobs"):
    st.info("🚀 Running job fetch + upload workflow...")
    df = fetch_jobs()
    if not df.empty:
        upload_to_airtable(df)
        st.dataframe(df)
    else:
        st.warning("⚠️ No matching jobs found.")
