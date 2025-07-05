import requests
import pandas as pd
import os
from urllib.parse import quote_plus

def scrape_indeed(keyword: str, location: str = "") -> pd.DataFrame:
    """
    Search job listings using JSearch API from RapidAPI.
    
    Args:
        keyword (str): Job search keyword
        location (str): Location to search in (optional)
    
    Returns:
        pd.DataFrame: DataFrame containing job listings with columns:
                     ['Job Title', 'Company', 'Location', 'Description', 'Apply Link', 'Job Type', 'Posting Date']
    """
    
    # Create empty DataFrame with correct columns
    columns = ['Job Title', 'Company', 'Location', 'Description', 'Apply Link', 'Job Type', 'Posting Date', 'QueryFlag']
    jobs_df = pd.DataFrame(columns=columns)
    
    try:
        # Get API key from environment
        api_key = os.getenv('RAPIDAPI_KEY')
        if not api_key:
            raise Exception("RAPIDAPI_KEY not found in environment variables")
        
        # Construct search query - combine keyword and location if provided
        query = keyword
        if location:
            query = f"{keyword} {location}"
        
        # JSearch API endpoint
        url = "https://jsearch.p.rapidapi.com/search"
        
        # API parameters
        querystring = {
            "query": query,
            "page": "1",
            "num_pages": "1",
            "date_posted": "all"
        }
        
        # Required headers for RapidAPI
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        # Make the API request
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        
        # Extract job data from response
        if data.get('status') == 'OK' and data.get('data'):
            jobs_list = []
            
            for job in data['data']:
                try:
                    job_data = extract_job_data_from_api(job)
                    if job_data and job_data['Job Title']:
                        jobs_list.append(job_data)
                        
                except Exception as e:
                    # Continue processing other jobs if one fails
                    continue
            
            # Convert to DataFrame
            if jobs_list:
                jobs_df = pd.DataFrame(jobs_list)
                jobs_df = clean_job_data(jobs_df)
        
        return jobs_df
        
    except requests.RequestException as e:
        raise Exception(f"Network error while accessing JSearch API: {str(e)}")
    except Exception as e:
        raise Exception(f"Error fetching jobs from API: {str(e)}")

def extract_job_data_from_api(job_json):
    """
    Extract job data from JSearch API JSON response.
    
    Args:
        job_json (dict): Job data from API response
    
    Returns:
        dict: Formatted job data dictionary
    """
    try:
        job_data = {
            'Job Title': job_json.get('job_title', '').strip(),
            'Company': job_json.get('employer_name', '').strip(),
            'Location': format_location(job_json),
            'Description': format_description(job_json.get('job_description', '')),
            'Apply Link': job_json.get('job_apply_link', ''),
            'Job Type': format_job_type(job_json),
            'Posting Date': format_posting_date(job_json)
        }
        
        return job_data
        
    except Exception as e:
        return None

def format_location(job_json):
    """Format location information from job data."""
    location_parts = []
    
    if job_json.get('job_city'):
        location_parts.append(job_json['job_city'])
    
    if job_json.get('job_state'):
        location_parts.append(job_json['job_state'])
    
    if job_json.get('job_country'):
        location_parts.append(job_json['job_country'])
    
    # Check if it's a remote job
    if job_json.get('job_is_remote'):
        location_parts.append('Remote')
    
    return ', '.join(location_parts) if location_parts else 'Not specified'

def format_description(description):
    """Format and truncate job description."""
    if not description:
        return 'No description available'
    
    # Clean up HTML tags and extra whitespace
    import re
    clean_desc = re.sub(r'<[^>]+>', '', description)
    clean_desc = re.sub(r'\s+', ' ', clean_desc).strip()
    
    # Truncate if too long
    if len(clean_desc) > 300:
        clean_desc = clean_desc[:300] + "..."
    
    return clean_desc

def format_job_type(job_json):
    """Format job type information."""
    job_type_parts = []
    
    if job_json.get('job_employment_type'):
        job_type_parts.append(job_json['job_employment_type'].title())
    
    if job_json.get('job_is_remote'):
        job_type_parts.append('Remote')
    
    return ', '.join(job_type_parts) if job_type_parts else 'Not specified'

def format_posting_date(job_json):
    """Format posting date from job data."""
    import datetime
    
    # Try different date fields that might be available
    date_fields = ['job_posted_at_datetime_utc', 'job_posted_at_timestamp', 'job_posted_at']
    
    for field in date_fields:
        if job_json.get(field):
            try:
                # Handle different date formats
                date_value = job_json[field]
                if isinstance(date_value, str):
                    # Try parsing common date formats
                    try:
                        parsed_date = datetime.datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                        return parsed_date.strftime('%Y-%m-%d')
                    except:
                        return date_value
                elif isinstance(date_value, (int, float)):
                    # Assume timestamp
                    parsed_date = datetime.datetime.fromtimestamp(date_value)
                    return parsed_date.strftime('%Y-%m-%d')
            except:
                continue
    
    return 'Not available'

def clean_job_data(df):
    """
    Clean and validate the job data from API.
    
    Args:
        df (pd.DataFrame): Raw job data
    
    Returns:
        pd.DataFrame: Cleaned job data
    """
    if df.empty:
        return df
    
    # Remove rows where job title is empty
    df = df[df['Job Title'].str.strip() != '']
    
    # Clean and standardize data
    df['Company'] = df['Company'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df['Location'] = df['Location'].str.replace(r'\s+', ' ', regex=True).str.strip()
    df['Description'] = df['Description'].str.replace(r'\s+', ' ', regex=True).str.strip()
    
    # Remove duplicates based on job title and company
    df = df.drop_duplicates(subset=['Job Title', 'Company'], keep='first')
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df
