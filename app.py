# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from scraper import scrape_indeed
from utils import highlight_remote_jobs, format_dataframe_display
from job_tagger import tag_jobs_by_theme, get_tag_statistics, filter_jobs_by_tag
from email_service import send_job_digest_email, validate_email, send_test_email

def build_enhanced_query(keyword, location, job_type, location_mode):
    """Build enhanced search query based on user selections."""
    query_parts = [keyword]
    
    # Add job type specific terms
    if job_type == "Internship":
        query_parts.extend(["internship", "intern", "fall 2025", "spring 2026", "summer 2026"])
    elif job_type == "Entry-Level":
        query_parts.extend(["entry level", "new grad", "junior", "early career", "graduate program"])
    elif job_type == "Both":
        query_parts.extend(["internship", "entry level", "new grad", "junior", "intern"])
    
    # Add remote if specified
    if location_mode == "Remote Only":
        query_parts.append("remote")
    
    return " ".join(query_parts)

def filter_remote_jobs(df):
    """Filter DataFrame for remote jobs only."""
    if df.empty:
        return df
    
    remote_mask = (
        df['Location'].str.contains('remote|Remote|REMOTE', na=False, case=False) |
        df['Job Type'].str.contains('remote|Remote|REMOTE', na=False, case=False) |
        df['Job Title'].str.contains('remote|Remote|REMOTE', na=False, case=False)
    )
    
    return df[remote_mask].reset_index(drop=True)

def display_jobs_by_season(jobs_df):
    """Display jobs separated by season/type with apply buttons."""
    if jobs_df.empty:
        return
    
    # Separate jobs by QueryFlag
    if 'QueryFlag' not in jobs_df.columns:
        st.warning("No job type information available")
        return
    
    # Define season order
    season_order = [
        "Fall 2025 Internship",
        "Spring 2026 Internship", 
        "Summer 2026 Internship",
        "Entry-Level / New-Grad Full-Time"
    ]
    
    for season in season_order:
        season_df = jobs_df[jobs_df['QueryFlag'] == season]
        if not season_df.empty:
            st.subheader(f"🎯 {season} ({len(season_df)} jobs)")
            display_job_cards(season_df, season)

def display_table_view(jobs_df):
    """Display jobs in compact table format with batch apply functionality."""
    if jobs_df.empty:
        return
    
    # Add remote job highlighting
    display_df = highlight_remote_jobs(jobs_df.copy())
    
    # Prepare table data
    table_data = []
    for idx, job in display_df.iterrows():
        table_data.append({
            'Select': False,
            'Job Title': job['Job Title'][:50] + "..." if len(job['Job Title']) > 50 else job['Job Title'],
            'Company': job['Company'][:30] + "..." if len(job['Company']) > 30 else job['Company'],
            'Location': job['Location'][:25] + "..." if len(job['Location']) > 25 else job['Location'],
            'Remote': '✓' if job.get('Remote Job') == '🏠 Remote' else '',
            'Tags': job.get('Tags', 'General Tech')[:40] + "..." if len(str(job.get('Tags', ''))) > 40 else job.get('Tags', 'General Tech'),
            'Apply Link': job['Apply Link'],
            'Index': idx
        })
    
    table_df = pd.DataFrame(table_data)
    
    # Display editable dataframe for selection
    edited_df = st.data_editor(
        table_df[['Select', 'Job Title', 'Company', 'Location', 'Remote', 'Tags']],
        column_config={
            "Select": st.column_config.CheckboxColumn("Select", width="small"),
            "Job Title": st.column_config.TextColumn("Job Title", width="large"),
            "Company": st.column_config.TextColumn("Company", width="medium"),
            "Location": st.column_config.TextColumn("Location", width="medium"),
            "Remote": st.column_config.TextColumn("Remote", width="small"),
            "Tags": st.column_config.TextColumn("Tags", width="medium")
        },
        use_container_width=True,
        hide_index=True
    )
    
    # Batch actions
    selected_indices = edited_df[edited_df['Select']].index.tolist()
    if selected_indices:
        st.markdown(f"**Selected {len(selected_indices)} jobs**")
        
        batch_col1, batch_col2, batch_col3 = st.columns(3)
        
        with batch_col1:
            if st.button("Open All Apply Links"):
                selected_jobs = [table_data[i] for i in selected_indices]
                links_html = "<br>".join([f'<a href="{job["Apply Link"]}" target="_blank">{job["Job Title"]}</a>' for job in selected_jobs if job["Apply Link"]])
                st.markdown(links_html, unsafe_allow_html=True)
        
        with batch_col2:
            if st.button("Save All Selected"):
                for idx in selected_indices:
                    job_data = display_df.iloc[table_data[idx]['Index']].to_dict()
                    already_saved = any(
                        saved['Job Title'] == job_data['Job Title'] and saved['Company'] == job_data['Company'] 
                        for saved in st.session_state.saved_jobs
                    )
                    if not already_saved:
                        st.session_state.saved_jobs.append(job_data)
                st.success(f"Saved {len(selected_indices)} jobs!")
                st.rerun()
        
        with batch_col3:
            if st.button("Export Selected to CSV"):
                selected_jobs_df = pd.DataFrame([display_df.iloc[table_data[i]['Index']] for i in selected_indices])
                csv_data = selected_jobs_df.to_csv(index=False)
                st.download_button(
                    label="Download Selected Jobs CSV",
                    data=csv_data,
                    file_name="selected_jobs.csv",
                    mime="text/csv"
                )

def display_job_cards(jobs_df, season_prefix):
    """Display individual job cards with apply buttons."""
    # Add remote job highlighting
    display_df = highlight_remote_jobs(jobs_df.copy())
    
    for idx, job in display_df.iterrows():
        with st.container():
            st.markdown("---")
            
            # Job header
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### {job['Job Title']}")
                st.markdown(f"**{job['Company']}** • {job['Location']}")
                if 'Job Type' in job and pd.notna(job['Job Type']):
                    st.markdown(f"*{job['Job Type']}*")
                if 'Posting Date' in job and pd.notna(job['Posting Date']):
                    st.markdown(f"*Posted: {job['Posting Date']}*")
            
            with col2:
                # Apply button that opens in new tab
                if job['Apply Link'] and pd.notna(job['Apply Link']):
                    st.markdown(f"""
                    <a href="{job['Apply Link']}" target="_blank" style="
                        display: inline-block;
                        padding: 0.5em 1em;
                        background-color: #FF4B4B;
                        color: white;
                        text-decoration: none;
                        border-radius: 0.5em;
                        text-align: center;
                        font-weight: bold;
                    ">Apply Now</a>
                    """, unsafe_allow_html=True)
                else:
                    st.write("No apply link")
            
            with col3:
                # Save job button
                unique_key = f"save_{season_prefix}_{idx}_{job['Job Title'][:20]}"
                already_saved = any(
                    saved['Job Title'] == job['Job Title'] and saved['Company'] == job['Company'] 
                    for saved in st.session_state.saved_jobs
                )
                
                if already_saved:
                    st.success("Saved")
                else:
                    if st.button("Save Job", key=unique_key):
                        job_dict = job.to_dict()
                        st.session_state.saved_jobs.append(job_dict)
                        st.rerun()
            
            # Job description
            if job['Description'] and pd.notna(job['Description']):
                with st.expander("View Description"):
                    st.write(job['Description'])
            
            # Job badges and tags
            badge_col1, badge_col2, badge_col3 = st.columns(3)
            with badge_col1:
                if job.get('Remote Job') == '🏠 Remote':
                    st.success("Remote")
            with badge_col2:
                if 'internship' in job['Job Title'].lower() or 'intern' in job['Job Title'].lower():
                    st.info("Internship")
            with badge_col3:
                if 'Posting Date' in job and pd.notna(job['Posting Date']) and job['Posting Date'] != 'Not available':
                    from datetime import datetime, timedelta
                    try:
                        post_date = datetime.strptime(job['Posting Date'], '%Y-%m-%d')
                        days_ago = (datetime.now() - post_date).days
                        if days_ago <= 7:
                            st.success(f"New ({days_ago}d ago)")
                        elif days_ago <= 14:
                            st.warning(f"{days_ago}d ago")
                    except:
                        pass
            
            # Job tags display
            if 'Tags' in job and pd.notna(job['Tags']) and job['Tags'] != 'General Tech':
                tags = [tag.strip() for tag in job['Tags'].split(',')]
                tag_html = " ".join([f'<span style="background-color: #e1f5fe; color: #0277bd; padding: 2px 8px; border-radius: 12px; font-size: 12px; margin: 2px;">{tag}</span>' for tag in tags])
                st.markdown(f"**Tags:** {tag_html}", unsafe_allow_html=True)

# Page configuration
st.set_page_config(
    page_title="AI/ML Job Finder",
    page_icon="🎯",
    layout="wide"
)

# Replace the quick search section in your code with this expandable version:

# Main title
st.title("🎯 AI/CS Entry-Level & Internship Finder")
st.markdown("Find internships, entry-level roles, and new grad positions in AI, ML, Data Science, and Software Engineering")

# Expandable Quick Search Section
with st.expander("🚀 Quick Search Options", expanded=False):
    st.markdown("**Click any button below to instantly search for popular job types:**")
    
    col1, col2, col3, col4, col5 = st.columns(5)

    # ── Column 1: Data Science ───────────────────────────────────────────────────
    with col1:
        st.markdown("**🍃 Data Science**")
        if st.button("DS Intern (Fall 2025)", use_container_width=True, key="ds_intern_fall"):
            st.session_state.quick_keyword = "data science"
            st.session_state.quick_type = "Fall 2025 Internship"
        if st.button("Junior Data Scientist", use_container_width=True, key="junior_ds"):
            st.session_state.quick_keyword = "data scientist"
            st.session_state.quick_type = "Entry-Level"
        if st.button("Data Analyst Intern", use_container_width=True, key="da_intern"):
            st.session_state.quick_keyword = "data analyst intern"
            st.session_state.quick_type = "Summer 2026 Internship"

    # ── Column 2: Machine Learning ───────────────────────────────────────────────
    with col2:
        st.markdown("**🤖 Machine Learning**")
        if st.button("ML Engineer Intern", use_container_width=True, key="ml_intern"):
            st.session_state.quick_keyword = "machine learning intern"
            st.session_state.quick_type = "Fall 2025 Internship"
        if st.button("ML Engineer Entry", use_container_width=True, key="ml_entry"):
            st.session_state.quick_keyword = "machine learning engineer"
            st.session_state.quick_type = "Entry-Level"
        if st.button("ML Research Intern", use_container_width=True, key="ml_research"):
            st.session_state.quick_keyword = "machine learning research intern"
            st.session_state.quick_type = "Spring 2026 Internship"

    # ── Column 3: Software Engineering ──────────────────────────────────────────
    with col3:
        st.markdown("**💻 Software Engineering**")
        if st.button("Entry Software Engineer", use_container_width=True, key="swe_entry"):
            st.session_state.quick_keyword = "software engineer"
            st.session_state.quick_type = "Entry-Level"
        if st.button("Frontend Intern", use_container_width=True, key="frontend_intern"):
            st.session_state.quick_keyword = "frontend developer intern"
            st.session_state.quick_type = "Summer 2026 Internship"
        if st.button("Backend Engineer", use_container_width=True, key="backend_engineer"):
            st.session_state.quick_keyword = "backend engineer"
            st.session_state.quick_type = "Entry-Level"

    # ── Column 4: AI & NLP ──────────────────────────────────────────────────────
    with col4:
        st.markdown("**🧠 AI & NLP**")
        if st.button("AI Research Intern", use_container_width=True, key="ai_research"):
            st.session_state.quick_keyword = "artificial intelligence intern"
            st.session_state.quick_type = "Fall 2025 Internship"
        if st.button("NLP Engineer Intern", use_container_width=True, key="nlp_intern"):
            st.session_state.quick_keyword = "natural language processing intern"
            st.session_state.quick_type = "Summer 2026 Internship"
        if st.button("AI Researcher", use_container_width=True, key="ai_researcher"):
            st.session_state.quick_keyword = "AI researcher"
            st.session_state.quick_type = "Entry-Level"

    # ── Column 5: Full-Stack & Business Intelligence ─────────────────────────────
    with col5:
        st.markdown("**🌐 Full-Stack & BI**")
        if st.button("Full-Stack Entry", use_container_width=True, key="fullstack_entry"):
            st.session_state.quick_keyword = "full stack developer"
            st.session_state.quick_type = "Entry-Level"
        if st.button("BI Intern", use_container_width=True, key="bi_intern"):
            st.session_state.quick_keyword = "business intelligence intern"
            st.session_state.quick_type = "Fall 2025 Internship"
        if st.button("Data Engineer Entry", use_container_width=True, key="de_entry"):
            st.session_state.quick_keyword = "data engineer"
            st.session_state.quick_type = "Entry-Level"
    
    # Additional row for remote and popular searches
    st.markdown("---")
    st.markdown("**🏠 Remote & Popular Searches:**")
    
    remote_col1, remote_col2, remote_col3, remote_col4, remote_col5 = st.columns(5)
    
    with remote_col1:
        if st.button("🏠 Remote SWE Intern", use_container_width=True, key="remote_swe"):
            st.session_state.quick_keyword = "software engineer"
            st.session_state.quick_type = "Spring 2026 Internship"
            st.session_state.quick_remote = True
    
    with remote_col2:
        if st.button("🏠 Remote Data Science", use_container_width=True, key="remote_ds"):
            st.session_state.quick_keyword = "data science"
            st.session_state.quick_type = "Entry-Level"
            st.session_state.quick_remote = True
    
    with remote_col3:
        if st.button("🏠 Remote ML Engineer", use_container_width=True, key="remote_ml"):
            st.session_state.quick_keyword = "machine learning"
            st.session_state.quick_type = "Entry-Level"
            st.session_state.quick_remote = True
    
    with remote_col4:
        if st.button("🏠 Remote Python Dev", use_container_width=True, key="remote_python"):
            st.session_state.quick_keyword = "python developer"
            st.session_state.quick_type = "Entry-Level"
            st.session_state.quick_remote = True
    
    with remote_col5:
        if st.button("🏠 Remote DevOps", use_container_width=True, key="remote_devops"):
            st.session_state.quick_keyword = "devops engineer"
            st.session_state.quick_type = "Entry-Level"
            st.session_state.quick_remote = True
    
    # Quick tip at the bottom
    st.info("💡 **Tip:** Click any button above to auto-fill the search form below, then click 'Search Jobs' to find opportunities!")

# Quick search button handling - add this right after the expandable section
if 'quick_keyword' in st.session_state:
    st.session_state.form_keyword = st.session_state.quick_keyword
    st.session_state.pop('quick_keyword', None)  # Clear after use

if 'quick_type' in st.session_state:
    st.session_state.form_job_type = st.session_state.quick_type
    st.session_state.pop('quick_type', None)  # Clear after use

if 'quick_remote' in st.session_state:
    st.session_state.form_remote = st.session_state.quick_remote
    st.session_state.pop('quick_remote', None)  # Clear after use

# Continue with the rest of your form code...

# Quick search button handling - add this right after the quick search buttons
if 'quick_keyword' in st.session_state:
    st.session_state.form_keyword = st.session_state.quick_keyword
    st.session_state.pop('quick_keyword', None)  # Clear after use

if 'quick_type' in st.session_state:
    st.session_state.form_job_type = st.session_state.quick_type
    st.session_state.pop('quick_type', None)  # Clear after use

if 'quick_remote' in st.session_state:
    st.session_state.form_remote = st.session_state.quick_remote
    st.session_state.pop('quick_remote', None)  # Clear after use

# Create input form
# Complete fixed form section - replace the entire form section in your app.py with this:

# Create input form
with st.form("job_search_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Pre-fill from quick search if available
        default_keyword = st.session_state.get('form_keyword', '')
        keyword = st.text_input(
            "Job Keywords", 
            value=default_keyword,
            placeholder="e.g., data science, machine learning, software engineer",
            help="Enter keywords to search for in job titles and descriptions"
        )
    
    with col2:
        location = st.text_input(
            "Location (Optional)", 
            placeholder="e.g., San Francisco, New York, Austin",
            help="Leave blank for global results"
        )
    
    with col3:
        st.write("")  # Spacing for alignment
    
    # Advanced filters in expandable section
    with st.expander("🔧 Advanced Filters", expanded=True):
        st.markdown("**Select job types to search for:**")
        
        # Determine default values based on quick search
        default_job_type = st.session_state.get('form_job_type', '')
        default_remote = st.session_state.get('form_remote', False)
        
        col4, col5 = st.columns(2)
        
        with col4:
            fall_2025 = st.checkbox(
                "Fall 2025 Internship", 
                value=(default_job_type == "Fall 2025 Internship")
            )
            spring_2026 = st.checkbox(
                "Spring 2026 Internship", 
                value=(default_job_type == "Spring 2026 Internship")
            )
        
        with col5:
            summer_2026 = st.checkbox(
                "Summer 2026 Internship", 
                value=(default_job_type == "Summer 2026 Internship")
            )
            entry_level = st.checkbox(
                "Entry-Level / New-Grad Full-Time", 
                value=(default_job_type == "Entry-Level")
            )
        
        # Additional filters row
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        
        with filter_col1:
            # Enhanced location filter
            location_mode = st.radio(
                "Location Filter",
                ["On-site Only", "Remote Only", "Include Remote"],
                index=2 if not default_remote else 1,  # default to Include Remote, unless quick remote was selected
                help="Filter jobs based on work location preferences"
            )
        
        with filter_col2:
            num_results = st.selectbox("Max Results", [10, 25, 50, 100], index=1)
        
        with filter_col3:
            sort_by = st.selectbox("Sort By", ["Relevance", "Date Posted", "Company"])
        
        # UI Mode and Email Digest
        # Replace the email digest section in your form with this fixed version:

        # UI Mode and Email Digest
        ui_col1, ui_col2 = st.columns(2)
        with ui_col1:
            view_mode = st.selectbox("View Mode", ["Card View", "Table View"])
        with ui_col2:
            enable_digest = st.checkbox("Enable Email Digest")
        
        # Email digest fields (but no buttons inside form)
        digest_email = None
        digest_frequency = None
        if enable_digest:
            digest_col1, digest_col2 = st.columns(2)
            with digest_col1:
                digest_email = st.text_input("Email for Digest", placeholder="your@email.com")
            with digest_col2:
                digest_frequency = st.selectbox("Frequency", ["Daily", "Weekly"])
    
    # Form submit button (this must be inside the form)
    submitted = st.form_submit_button("🔍 Search Jobs", use_container_width=True)

# Test email button OUTSIDE the form
if enable_digest and digest_email:
    test_col1, test_col2, test_col3 = st.columns([1, 1, 1])
    with test_col2:
        if st.button("Send Test Email", key="test_email_btn"):
            if validate_email(digest_email):
                success, message = send_test_email(digest_email)
                if success:
                    st.success("Test email sent!")
                else:
                    st.error(f"Test failed: {message}")
            else:
                st.warning("Please enter a valid email address")

# Update the filtering logic after form submission
if submitted:
    if not keyword.strip():
        st.error("Please enter a job keyword to search.")
    else:
        # Check if at least one job type is selected
        selected_types = []
        if fall_2025:
            selected_types.append("Fall 2025 Internship")
        if spring_2026:
            selected_types.append("Spring 2026 Internship")
        if summer_2026:
            selected_types.append("Summer 2026 Internship")
        if entry_level:
            selected_types.append("Entry-Level / New-Grad Full-Time")
        
        if not selected_types:
            st.error("Please select at least one job type to search for.")
        else:
            # Clear the form session state after successful submission
            st.session_state.pop('form_keyword', None)
            st.session_state.pop('form_job_type', None)
            st.session_state.pop('form_remote', None)
            
            with st.spinner("🔍 Searching for jobs using JSearch API..."):
                try:
                    # Perform searches for each selected type
                    all_jobs = []
                    
                    term_map = {
                        "Fall 2025 Internship": "fall 2025 internship",
                        "Spring 2026 Internship": "spring 2026 internship", 
                        "Summer 2026 Internship": "summer 2026 internship",
                        "Entry-Level / New-Grad Full-Time": "entry level new grad"
                    }
                    
                    for job_type in selected_types:
                        search_terms = term_map[job_type]
                    
                    # Apply location mode to search terms
                    if location_mode == "Remote Only":
                        search_terms += " remote"
                    
                    full_query = f"{keyword.strip()} {search_terms}"
                    jobs_df = scrape_indeed(full_query, location.strip())
                    
                    # Add query flag to identify job type
                    if not jobs_df.empty:
                        jobs_df['QueryFlag'] = job_type
                        all_jobs.append(jobs_df)
                        
                        # Add query flag to identify job type
                        if not jobs_df.empty:
                            jobs_df['QueryFlag'] = job_type
                            all_jobs.append(jobs_df)
                    
                    # Combine all results
                    if all_jobs:
                        combined_df = pd.concat(all_jobs, ignore_index=True)
                        
                        # Apply location mode filtering
                        if location_mode == "Remote Only":
                            combined_df = filter_remote_jobs(combined_df)
                        elif location_mode == "On-site Only":
                            # Filter OUT remote jobs
                            remote_mask = (
                                combined_df['Location'].str.contains('remote|Remote|REMOTE', na=False, case=False) |
                                combined_df['Job Type'].str.contains('remote|Remote|REMOTE', na=False, case=False) |
                                combined_df['Job Title'].str.contains('remote|Remote|REMOTE', na=False, case=False)
                            )
                            combined_df = combined_df[~remote_mask].reset_index(drop=True)
                        # For "Include Remote", we don't filter anything
                        
                        # Apply sorting if specified
                        if sort_by == "Date Posted" and 'Posting Date' in combined_df.columns:
                            combined_df = combined_df.sort_values('Posting Date', ascending=False)
                        elif sort_by == "Company":
                            combined_df = combined_df.sort_values('Company')
                        
                        # Add job tags
                        combined_df = tag_jobs_by_theme(combined_df)
                        
                        # Limit results
                        combined_df = combined_df.head(num_results)
                            
                        st.session_state.jobs_df = combined_df
                        st.session_state.search_timestamp = datetime.now()
                        
                        # Send email digest if enabled
                        if enable_digest and digest_email and validate_email(digest_email):
                            preferences = {
                                'job_types': selected_types,
                                'keywords': keyword,
                                'location': location,
                                'location_mode': location_mode
                            }
                            success, message = send_job_digest_email(digest_email, combined_df, preferences)
                            if success:
                                st.success(f"Found {len(combined_df)} jobs! Email digest sent to {digest_email}")
                            else:
                                st.success(f"Found {len(combined_df)} jobs!")
                                st.warning(f"Email sending failed: {message}")
                        elif not combined_df.empty:
                            st.success(f"Found {len(combined_df)} jobs!")
                        else:
                            st.warning("No jobs found for your search criteria. Try different keywords or location.")
                    else:
                        st.session_state.jobs_df = pd.DataFrame()
                        st.warning("No jobs found for your search criteria. Try different keywords or location.")
                        
                except Exception as e:
                    st.error(f"❌ Error occurred while searching: {str(e)}")
                    st.info("Please try again with different search terms or check your internet connection.")

# Search tips section
with st.expander("💡 Search Tips & Suggestions"):
    st.markdown("""
    **Popular Search Terms:**
    - **Internships**: "Fall 2025 internship", "Spring 2026 internship", "Summer 2026 internship"
    - **Entry-Level**: "entry-level data analyst", "new grad software engineer", "junior ML engineer"
    - **Specific Roles**: "AI intern", "data science intern", "software engineering new grad"
    
    **Job Type Selection:**
    - **Internship**: Focuses on intern positions for students
    - **Entry-Level**: Targets new graduate and early career roles
    - **Both**: Searches for all entry-level opportunities
    
    **Location Tips:**
    - Use "remote" for work-from-home positions
    - Try specific cities like "San Francisco", "New York", "Seattle"
    - Leave blank to see opportunities from all locations
    """)

# Initialize session state for storing results
if 'jobs_df' not in st.session_state:
    st.session_state.jobs_df = pd.DataFrame()
if 'search_timestamp' not in st.session_state:
    st.session_state.search_timestamp = None
if 'saved_jobs' not in st.session_state:
    st.session_state.saved_jobs = []
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Card View"

# Display results
if not st.session_state.jobs_df.empty:
    st.markdown("---")
    
    # Display search info
    search_info_col1, search_info_col2 = st.columns(2)
    with search_info_col1:
        st.markdown(f"**📊 {len(st.session_state.jobs_df)} jobs found**")
    with search_info_col2:
        if st.session_state.search_timestamp:
            st.markdown(f"**🕐 Last updated:** {st.session_state.search_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Tag filter section
    if 'Tags' in st.session_state.jobs_df.columns:
        st.markdown("**Filter by Theme:**")
        tag_stats = get_tag_statistics(st.session_state.jobs_df)
        available_tags = ["All"] + list(tag_stats.keys())
        
        tag_col1, tag_col2 = st.columns([3, 1])
        with tag_col1:
            selected_tag = st.selectbox("Theme Category", available_tags, key="tag_filter")
        with tag_col2:
            if selected_tag != "All":
                filtered_count = len(filter_jobs_by_tag(st.session_state.jobs_df, selected_tag))
                st.metric("Tagged Jobs", filtered_count)
        
        # Apply tag filter
        display_df = filter_jobs_by_tag(st.session_state.jobs_df, selected_tag)
    else:
        display_df = st.session_state.jobs_df
    
    # Display jobs based on view mode
    try:
        current_view_mode = view_mode if 'view_mode' in locals() else "Card View"
        st.session_state.view_mode = current_view_mode
    except:
        current_view_mode = "Card View"
    
    if current_view_mode == "Table View":
        display_table_view(display_df)
    else:
        display_jobs_by_season(display_df)
    
    # Download button
    st.markdown("---")
    
    # Convert dataframe to CSV
    csv_data = st.session_state.jobs_df.to_csv(index=False)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_data,
            file_name="jobs.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    # Enhanced statistics with tag breakdown
    st.markdown("---")
    st.markdown("### 📈 Job Search Analytics")
    
    stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
    
    with stats_col1:
        st.metric("Total Jobs", len(st.session_state.jobs_df))
    
    with stats_col2:
        unique_companies = st.session_state.jobs_df['Company'].nunique()
        st.metric("Unique Companies", unique_companies)
    
    with stats_col3:
        remote_jobs = st.session_state.jobs_df[
            st.session_state.jobs_df['Location'].str.contains('remote|Remote|REMOTE', na=False, case=False) |
            st.session_state.jobs_df['Job Type'].str.contains('remote|Remote|REMOTE', na=False, case=False)
        ]
        st.metric("Remote Jobs", len(remote_jobs))
    
    with stats_col4:
        unique_locations = st.session_state.jobs_df['Location'].nunique()
        st.metric("Unique Locations", unique_locations)
    
    # Tag statistics
    if 'Tags' in st.session_state.jobs_df.columns:
        st.markdown("### 🏷️ Popular Job Categories")
        tag_stats = get_tag_statistics(st.session_state.jobs_df)
        if tag_stats:
            tag_chart_col1, tag_chart_col2 = st.columns(2)
            with tag_chart_col1:
                # Display top tags as metrics
                top_tags = list(tag_stats.items())[:6]
                for i in range(0, len(top_tags), 2):
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        if i < len(top_tags):
                            st.metric(top_tags[i][0], top_tags[i][1])
                    with metric_col2:
                        if i + 1 < len(top_tags):
                            st.metric(top_tags[i + 1][0], top_tags[i + 1][1])
            
            with tag_chart_col2:
                # Create a simple bar chart using markdown
                st.markdown("**Tag Distribution:**")
                for tag, count in list(tag_stats.items())[:5]:
                    percentage = (count / len(st.session_state.jobs_df)) * 100
                    bar_length = int(percentage / 2)  # Scale down for display
                    bar = "█" * bar_length + "░" * (50 - bar_length)
                    st.markdown(f"`{tag:<20} │{bar}│ {count} ({percentage:.1f}%)`")
    
    # Saved jobs section
    if st.session_state.saved_jobs:
        st.markdown("---")
        st.markdown("### 📚 Saved Jobs")
        
        for i, saved_job in enumerate(st.session_state.saved_jobs):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{saved_job['Job Title']}** at {saved_job['Company']}")
            with col2:
                if st.button("View", key=f"view_{i}"):
                    st.write(f"**Location:** {saved_job['Location']}")
                    st.write(f"**Apply Link:** {saved_job['Apply Link']}")
            with col3:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.saved_jobs.pop(i)
                    st.rerun()
        
        # Export saved jobs
        if st.button("📥 Export Saved Jobs to CSV"):
            saved_df = pd.DataFrame(st.session_state.saved_jobs)
            csv_saved = saved_df.to_csv(index=False)
            st.download_button(
                label="Download Saved Jobs CSV",
                data=csv_saved,
                file_name="saved_jobs.csv",
                mime="text/csv"
            )

else:
    # Show helpful information when no search has been performed
    st.markdown("---")
    st.info("👆 Enter your job search criteria above and click 'Search Jobs' to get started!")
    
    st.markdown("### 💡 Search Tips:")
    st.markdown("""
    - **Keywords**: Try specific terms like "machine learning engineer", "data scientist", "python developer"
    - **Location**: Use "remote" for remote jobs, city names like "San Francisco", or leave blank for all locations
    - **Results**: Jobs are scraped in real-time from Indeed, so results may vary
    """)
    
    st.markdown("### 🔥 Popular Search Terms:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **AI/ML:**
        - machine learning
        - artificial intelligence
        - deep learning
        - computer vision
        - NLP
        """)
    
    with col2:
        st.markdown("""
        **Data Science:**
        - data scientist
        - data analyst
        - data engineer
        - business intelligence
        - analytics
        """)
    
    with col3:
        st.markdown("""
        **Software Engineering:**
        - software engineer
        - python developer
        - full stack developer
        - backend engineer
        - DevOps engineer
        """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
    Built with Streamlit | Data sourced from JSearch API
    </div>
    """, 
    unsafe_allow_html=True
)
