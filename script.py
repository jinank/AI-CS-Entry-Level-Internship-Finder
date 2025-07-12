import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pyairtable import Table

# Load environment variables from .env
load_dotenv()

# Airtable credentials
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
        "date_posted": "today"  # ✅ Only today's jobs
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
        salary = job.get("job_min_salary")
        salary_range = f"${int(salary):,}" if salary else "N/A"
        internship_type = job.get("job_employment_type")
        if internship_type not in ["Internship", "Full-time", "Part-time"]:
            internship_type = "Other"

        job_list.append({
            "Title": job.get("job_title"),
            "Company": job.get("employer_name"),
            "Location": job.get("job_city") or job.get("job_country", "N/A"),
            "Industry": job.get("job_title"),
            "Source": "JSearch API",
            "Posting Date": job.get("job_posted_at_datetime_utc", "").split("T")[0],
            "Internship Type": internship_type,
            "Salary Range": salary_range,
            "Job Description": job.get("job_description", "")[:250],
            "Link": job.get("job_apply_link"),
            "Status": "PENDING"
        })

    df = pd.DataFrame(job_list)

    # ✅ Filter only today's date (extra safeguard)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    df = df[df["Posting Date"] == today]

    # ✅ Remove duplicate jobs
    df.drop_duplicates(subset=["Title", "Company", "Location"], inplace=True)

    return df

def upload_to_airtable(df):
    for i, row in df.iterrows():
        record = {col: row[col] for col in df.columns if pd.notnull(row[col])}
        try:
            airtable.create(record)
            print(f"✅ Uploaded: {record['Title']} @ {record['Company']}")
        except Exception as e:
            print(f"❌ Failed to upload row {i}: {record}")
            print(f"Error: {e}")

if __name__ == "__main__":
    print("🔍 Fetching today's Data Science Intern jobs...")
    df = fetch_jobs()
    print(f"📦 {len(df)} unique job(s) found for today.")

    if df.empty:
        print("⚠️ No new jobs found today.")
    else:
        print("📤 Uploading to Airtable...")
        upload_to_airtable(df)
        print("✅ All done!")
