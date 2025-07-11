import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pyairtable import Table

# Load environment variables
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Jobs")

# Airtable setup
airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_jobs(keyword="data science intern", location=""):
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": keyword,
        "page": "1",
        "num_pages": "1",  # Increase this if you want more results
        "date_posted": "month"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    jobs = data.get("data", [])
    
    job_list = []
    for job in jobs:
        job_list.append({
            "Job Title": job.get("job_title"),
            "Company": job.get("employer_name"),
            "Location": job.get("job_city") or job.get("job_country"),
            "Description": job.get("job_description", "")[:300],  # Short description
            "Apply Link": job.get("job_apply_link"),
            "Job Type": job.get("job_employment_type"),
            "Posting Date": job.get("job_posted_at_datetime_utc", "").split("T")[0]
        })

    return pd.DataFrame(job_list)

def upload_to_airtable(df):
    for _, row in df.iterrows():
        record = {col: row[col] for col in df.columns}
        airtable.create(record)

if __name__ == "__main__":
    print("Fetching jobs...")
    df = fetch_jobs()
    print(f"Found {len(df)} jobs.")
    print("Uploading to Airtable...")
    upload_to_airtable(df)
    print("✅ Done.")
