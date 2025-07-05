import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import pandas as pd
from datetime import datetime

def send_job_digest_email(user_email, jobs_df, preferences):
    """Send daily job digest email to user."""
    try:
        # Debug: Retrieve and validate credentials
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        # Validate credentials exist
        
        if not gmail_email:
            raise Exception("GMAIL_EMAIL environment variable not found or empty")
        if not gmail_password:
            raise Exception("GMAIL_APP_PASSWORD environment variable not found or empty")
        
        # Create email content
        subject = f"Daily Job Digest - {len(jobs_df)} New Opportunities"
        html_content = generate_email_html(jobs_df, preferences)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = gmail_email
        message["To"] = user_email
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email using TLS (port 587)
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()  # Enable TLS security
            server.login(gmail_email, gmail_password)
            server.send_message(message)
            server.quit()
            
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as auth_error:
            return False, f"SMTP Authentication failed: {str(auth_error)}. Check if 2-Step Verification is enabled and App Password is correct."
        except smtplib.SMTPException as smtp_error:
            return False, f"SMTP error: {str(smtp_error)}"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def send_test_email(user_email):
    """Send a test email to verify SMTP configuration."""
    try:
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_email or not gmail_password:
            return False, "Gmail credentials not configured"
        
        # Create simple test message
        message = MIMEText("This is a test email from your AI/CS Job Finder application. Email configuration is working correctly!")
        message["Subject"] = "Test Email - Job Finder App"
        message["From"] = gmail_email
        message["To"] = user_email
        
        # Send using TLS
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_email, gmail_password)
        server.send_message(message)
        server.quit()
        
        return True, "Test email sent successfully"
        
    except Exception as e:
        return False, f"Test email failed: {str(e)}"

def generate_email_html(jobs_df, preferences):
    """Generate HTML content for job digest email."""
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #FF4B4B; color: white; padding: 20px; text-align: center; }}
            .job-card {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
            .job-title {{ font-weight: bold; font-size: 18px; color: #333; }}
            .company {{ color: #666; margin: 5px 0; }}
            .location {{ color: #888; font-style: italic; }}
            .apply-btn {{ 
                background-color: #FF4B4B; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 5px; 
                display: inline-block; 
                margin-top: 10px; 
            }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Your Daily Job Digest</h1>
            <p>Found {len(jobs_df)} new opportunities matching your preferences</p>
            <p>{datetime.now().strftime('%B %d, %Y')}</p>
        </div>
    """
    
    # Add job cards
    for _, job in jobs_df.head(10).iterrows():  # Limit to 10 jobs per email
        html += f"""
        <div class="job-card">
            <div class="job-title">{job['Job Title']}</div>
            <div class="company">🏢 {job['Company']}</div>
            <div class="location">📍 {job['Location']}</div>
            {f'<div style="color: #28a745;">🏠 Remote Position</div>' if 'Remote' in job.get('Location', '') else ''}
            {f'<div style="color: #666; margin: 10px 0;">{job["Description"][:200]}...</div>' if job.get('Description') else ''}
            <a href="{job['Apply Link']}" class="apply-btn">Apply Now</a>
        </div>
        """
    
    html += f"""
        <div class="footer">
            <p>This digest was generated by AI/CS Entry-Level & Internship Finder</p>
            <p>To modify your preferences or unsubscribe, visit the application.</p>
        </div>
    </body>
    </html>
    """
    
    return html

def validate_email(email):
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None