import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables from .env
load_dotenv()

# Airtable credentials
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Jobs")

# ✅ New recommended Airtable client
api = Api(AIRTABLE_API_KEY)
airtable = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_jobs(keyword="data science intern", location=""):
    url = "https://jsearch.p.rapidapi.com/search"
    querystring = {
        "query": keyword,
        "page": "1",
        "num_pages": "1",
        "date_posted": "today"
    }

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }

    # 🖨️ Print request URL
    full_url = f"{url}?query={querystring['query']}&page={querystring['page']}&num_pages={querystring['num_pages']}&date_posted={querystring['date_posted']}"
    print("🔗 API Request URL:")
    print(full_url)

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    jobs = data.get("data", [])[:10]  # ✅ Hard limit to 10 jobs

    if not jobs:
        print("⚠️ No jobs returned from API.")
        return pd.DataFrame()

    print("\n📥 API Response Preview:")
    for i, job in enumerate(jobs, 1):
        print(f"{i}. {job.get('job_title')} @ {job.get('employer_name')} ({job.get('job_city') or job.get('job_country')})")

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
            "Internship Type": internship_type,
            "Salary Range": salary_range,
            "Job Description": job.get("job_description", "")[:250],
            "Link": job.get("job_apply_link"),
            "Status": "PENDING"
        })

    df = pd.DataFrame(job_list)

    # ✅ Remove local duplicates
    df.drop_duplicates(subset=["Title", "Company", "Location"], inplace=True)

    print(f"\n📦 API returned {len(df)} unique job(s).")
    return df

def upload_to_airtable(df):
    print("\n🔄 Checking for existing records in Airtable...")

    existing_keys = set()
    for record in airtable.all():
        fields = record.get("fields", {})
        key = (
            fields.get("Title", "").strip().lower(),
            fields.get("Company", "").strip().lower(),
            fields.get("Location", "").strip().lower()
        )
        existing_keys.add(key)

    uploaded = 0
    for i, row in df.iterrows():
        key = (
            str(row["Title"]).strip().lower(),
            str(row["Company"]).strip().lower(),
            str(row["Location"]).strip().lower()
        )
        if key in existing_keys:
            print(f"🛑 Skipped duplicate: {row['Title']} @ {row['Company']}")
            continue

        record = {col: row[col] for col in df.columns if pd.notnull(row[col])}
        try:
            airtable.create(record)
            uploaded += 1
            print(f"✅ Uploaded: {record['Title']} @ {record['Company']}")
        except Exception as e:
            print(f"❌ Failed to upload row {i}: {record}")
            print(f"Error: {e}")

    print(f"\n📊 Upload complete: {uploaded} new job(s) added.")

if __name__ == "__main__":
    print("🔍 Fetching Data Science Intern jobs posted in the last 24 hours...")
    df = fetch_jobs()
    if df.empty:
        print("⚠️ No new jobs to upload.")
    else:
        print("📤 Uploading to Airtable...")
        upload_to_airtable(df)
        print("✅ Done!")
