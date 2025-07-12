import os
import requests
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv
from pyairtable import Api

# Load environment variables
load_dotenv()

# API Keys and config
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Jobs")

# Airtable setup
api = Api(AIRTABLE_API_KEY)
airtable = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

def fetch_jobs(keyword="data science intern"):
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

    # Print constructed API request URL
    full_url = f"{url}?query={querystring['query']}&page=1&num_pages=1&date_posted=today"
    print("🔗 API Request URL:")
    print(full_url)

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    jobs = data.get("data", [])[:10]

    if not jobs:
        print("⚠️ No jobs returned from API.")
        return pd.DataFrame()

    job_list = []
    for job in jobs:
        title = job.get("job_title", "")
        if "2026" not in title:
            continue  # ✅ Filter by title keyword

        salary = job.get("job_min_salary")
        salary_range = f"${int(salary):,}" if salary else "N/A"
        internship_type = job.get("job_employment_type", "Other")
        if internship_type not in ["Internship", "Full-time", "Part-time"]:
            internship_type = "Other"

        link = job.get("job_apply_link")
        parsed_url = urlparse(link) if link else None
        source = parsed_url.netloc.replace("www.", "") if parsed_url and parsed_url.netloc else "Unknown"

        posting_date_raw = job.get("job_posted_at_datetime_utc")
        posting_date = pd.to_datetime(posting_date_raw).date().isoformat() if posting_date_raw else "N/A"

        dedup_key = f"{title}-{job.get('employer_name', '')}-{job.get('job_city') or job.get('job_country', '')}".lower().strip()

        job_list.append({
            "Title": title,
            "Company": job.get("employer_name"),
            "Location": job.get("job_city") or job.get("job_country", "N/A"),
            "Industry": title,
            "Source": source,
            "Posting Date": posting_date,  # ✅ Added Posting Date
            "Internship Type": internship_type,
            "Salary Range": salary_range,
            "Job Description": job.get("job_description", "")[:250],
            "Link": link,
            "Status": "PENDING",
            "Dedup Key": dedup_key  # ✅ Used for deduplication
        })

    df = pd.DataFrame(job_list)
    df.drop_duplicates(subset=["Dedup Key"], inplace=True)

    print(f"\n📦 Fetched {len(df)} job(s) with '2026' in the title.")
    return df

def upload_to_airtable(df):
    print("\n🔄 Checking existing records in Airtable by Dedup Key...")
    existing_keys = set()
    for record in airtable.all():
        key = record.get("fields", {}).get("Dedup Key", "").strip().lower()
        if key:
            existing_keys.add(key)

    uploaded = 0
    for i, row in df.iterrows():
        dedup_key = str(row.get("Dedup Key", "")).strip().lower()
        if dedup_key in existing_keys:
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
    print("🚀 Running job fetch + upload workflow...")
    df = fetch_jobs()
    if df.empty:
        print("⚠️ No matching jobs found.")
    else:
        upload_to_airtable(df)
        print("✅ Done!")
