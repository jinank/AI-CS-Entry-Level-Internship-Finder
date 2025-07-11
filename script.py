import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pyairtable import Table

# Load secrets
load_dotenv()
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Jobs")

# Airtable client
airtable = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_jobs(keyword="data science intern", location=""):
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": keyword,
        "page": "1",
        "num_pages": "1",
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
            "Title": job.get("job_title"),
            "Company": job.get("employer_name"),
            "Location": job.get("job_city") or job.get("job_country", "N/A"),
            "Industry": job.get("job_title"),
            "Source": "JSearch API",
            "Posting Date": job.get("job_posted_at_datetime_utc", "").split("T")[0],
            "Internship Type": job.get("job_employment_type") if job.get("job_employment_type") in ["Internship", "Full-time", "Part-time"] else "Other",
            "Salary Range": f"${int(job['job_min_salary']):,}" if job.get("job_min_salary") else "N/A",
            "Job Description": job.get("job_description", "")[:250],
            "Link": job.get("job_apply_link"),
            "Status": "PENDING"
        })


    return pd.DataFrame(job_list)

def upload_to_airtable(df):
    for i, row in df.iterrows():
        record = {col: row[col] for col in df.columns if pd.notnull(row[col])}
        try:
            airtable.create(record)
        except Exception as e:
            print(f"❌ Failed to upload row {i}: {record}")
            print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Fetching Data Science Intern jobs...")
    df = fetch_jobs()
    print(f"✅ Retrieved {len(df)} job(s).")
    print("📤 Uploading to Airtable...")
    upload_to_airtable(df)
    print("🎉 Done.")
