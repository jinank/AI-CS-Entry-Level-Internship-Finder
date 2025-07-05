import pandas as pd
import re
from datetime import datetime

def highlight_remote_jobs(df):
    """
    Add a column to highlight remote jobs in the DataFrame.
    
    Args:
        df (pd.DataFrame): Jobs DataFrame
    
    Returns:
        pd.DataFrame: DataFrame with remote job indicator
    """
    if df.empty:
        return df
    
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Check for remote indicators in location and job title
    remote_keywords = [
        'remote', 'Remote', 'REMOTE',
        'work from home', 'Work from Home', 'WFH',
        'telecommute', 'Telecommute',
        'virtual', 'Virtual',
        'anywhere', 'Anywhere'
    ]
    
    # Create pattern for remote detection
    pattern = '|'.join(remote_keywords)
    
    # Check location and job title for remote indicators
    df_copy['Remote Job'] = (
        df_copy['Location'].str.contains(pattern, na=False, case=False) |
        df_copy['Job Title'].str.contains(pattern, na=False, case=False) |
        df_copy['Description'].str.contains(pattern, na=False, case=False)
    )
    
    # Convert boolean to readable text
    df_copy['Remote Job'] = df_copy['Remote Job'].map({True: '🏠 Remote', False: '🏢 On-site'})
    
    return df_copy

def format_dataframe_display(df):
    """
    Format the DataFrame for better display in Streamlit.
    
    Args:
        df (pd.DataFrame): Jobs DataFrame
    
    Returns:
        pd.DataFrame: Formatted DataFrame
    """
    if df.empty:
        return df
    
    # Create a copy
    formatted_df = df.copy()
    
    # Truncate long job titles
    formatted_df['Job Title'] = formatted_df['Job Title'].apply(
        lambda x: x[:60] + "..." if len(str(x)) > 60 else x
    )
    
    # Truncate long company names
    formatted_df['Company'] = formatted_df['Company'].apply(
        lambda x: x[:40] + "..." if len(str(x)) > 40 else x
    )
    
    # Truncate long descriptions
    formatted_df['Description'] = formatted_df['Description'].apply(
        lambda x: x[:100] + "..." if len(str(x)) > 100 else x
    )
    
    # Format apply links for display
    formatted_df['Apply Link'] = formatted_df['Apply Link'].apply(
        lambda x: "Apply" if x else "N/A"
    )
    
    # Format job type for display
    if 'Job Type' in formatted_df.columns:
        formatted_df['Job Type'] = formatted_df['Job Type'].apply(
            lambda x: x[:30] + "..." if len(str(x)) > 30 else x
        )
    
    return formatted_df

def validate_search_inputs(keyword, location):
    """
    Validate user inputs for job search.
    
    Args:
        keyword (str): Job search keyword
        location (str): Location input
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not keyword or not keyword.strip():
        return False, "Please enter a job keyword to search."
    
    # Check for potentially problematic characters
    if re.search(r'[<>"\']', keyword):
        return False, "Keyword contains invalid characters."
    
    if location and re.search(r'[<>"\']', location):
        return False, "Location contains invalid characters."
    
    # Check keyword length
    if len(keyword.strip()) < 2:
        return False, "Keyword must be at least 2 characters long."
    
    if len(keyword.strip()) > 100:
        return False, "Keyword is too long (max 100 characters)."
    
    return True, ""

def format_timestamp(timestamp):
    """
    Format timestamp for display.
    
    Args:
        timestamp (datetime): Timestamp to format
    
    Returns:
        str: Formatted timestamp string
    """
    if not timestamp:
        return "Unknown"
    
    return timestamp.strftime("%Y-%m-%d at %H:%M:%S")

def get_job_statistics(df):
    """
    Calculate statistics from the jobs DataFrame.
    
    Args:
        df (pd.DataFrame): Jobs DataFrame
    
    Returns:
        dict: Statistics dictionary
    """
    if df.empty:
        return {
            'total_jobs': 0,
            'unique_companies': 0,
            'remote_jobs': 0,
            'unique_locations': 0
        }
    
    # Count remote jobs
    remote_count = len(df[
        df['Location'].str.contains('remote|Remote|REMOTE|work from home|WFH', na=False, case=False) |
        df['Job Title'].str.contains('remote|Remote|REMOTE|work from home|WFH', na=False, case=False)
    ])
    
    return {
        'total_jobs': len(df),
        'unique_companies': df['Company'].nunique(),
        'remote_jobs': remote_count,
        'unique_locations': df['Location'].nunique()
    }

def create_search_summary(keyword, location, job_count, timestamp):
    """
    Create a summary of the search performed.
    
    Args:
        keyword (str): Search keyword
        location (str): Search location
        job_count (int): Number of jobs found
        timestamp (datetime): When search was performed
    
    Returns:
        str: Search summary text
    """
    location_text = f" in {location}" if location else " globally"
    time_text = format_timestamp(timestamp)
    
    return f"Found {job_count} jobs for '{keyword}'{location_text} on {time_text}"

def sanitize_filename(filename):
    """
    Sanitize filename for safe file downloads.
    
    Args:
        filename (str): Original filename
    
    Returns:
        str: Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'_+', '_', sanitized)  # Replace multiple underscores with single
    sanitized = sanitized.strip('_')  # Remove leading/trailing underscores
    
    return sanitized if sanitized else "jobs"
