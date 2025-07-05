import pandas as pd
import re

def tag_jobs_by_theme(jobs_df):
    """Auto-tag jobs with AI/CS theme categories."""
    if jobs_df.empty:
        return jobs_df
    
    # Define theme categories and their keywords
    theme_categories = {
        "Computer Vision": [
            "computer vision", "cv", "image processing", "opencv", "image recognition",
            "object detection", "facial recognition", "medical imaging", "autonomous",
            "lidar", "camera", "visual", "perception"
        ],
        "Natural Language Processing": [
            "nlp", "natural language", "language model", "text processing", "chatbot",
            "sentiment analysis", "speech recognition", "translation", "linguistics",
            "transformer", "bert", "gpt", "llm"
        ],
        "Generative AI": [
            "generative ai", "genai", "gpt", "llm", "large language model", "diffusion",
            "stable diffusion", "dall-e", "midjourney", "text generation", "ai art",
            "prompt engineering", "fine-tuning", "rag", "retrieval augmented"
        ],
        "Machine Learning": [
            "machine learning", "ml", "deep learning", "neural network", "tensorflow",
            "pytorch", "scikit-learn", "keras", "model training", "feature engineering",
            "regression", "classification", "clustering", "supervised", "unsupervised"
        ],
        "Data Science": [
            "data science", "data scientist", "data analysis", "statistics", "pandas",
            "numpy", "jupyter", "visualization", "tableau", "power bi", "sql",
            "database", "etl", "data pipeline", "analytics"
        ],
        "Robotics": [
            "robotics", "robot", "ros", "autonomous", "drone", "manipulation",
            "control systems", "embedded", "sensors", "actuators", "path planning"
        ],
        "Healthcare AI": [
            "healthcare", "medical", "biotech", "pharmaceutical", "clinical",
            "health tech", "telemedicine", "medical device", "fda", "hipaa",
            "radiology", "pathology", "genomics"
        ],
        "FinTech": [
            "fintech", "financial", "banking", "trading", "cryptocurrency", "blockchain",
            "payments", "fraud detection", "risk management", "algorithmic trading",
            "quantitative", "portfolio"
        ],
        "Cloud & DevOps": [
            "cloud", "aws", "azure", "gcp", "kubernetes", "docker", "devops",
            "ci/cd", "infrastructure", "terraform", "microservices", "serverless"
        ],
        "Research": [
            "research", "phd", "academic", "publication", "conference", "arxiv",
            "experimental", "theoretical", "university", "lab", "postdoc"
        ]
    }
    
    # Add tags column
    jobs_df = jobs_df.copy()
    jobs_df['Tags'] = jobs_df.apply(lambda row: categorize_job(row, theme_categories), axis=1)
    
    return jobs_df

def categorize_job(job_row, theme_categories):
    """Categorize a single job based on keywords."""
    # Combine job title, description, and company for analysis
    text_to_analyze = " ".join([
        str(job_row.get('Job Title', '')),
        str(job_row.get('Description', '')),
        str(job_row.get('Company', ''))
    ]).lower()
    
    # Find matching categories
    matching_tags = []
    
    for category, keywords in theme_categories.items():
        for keyword in keywords:
            if keyword.lower() in text_to_analyze:
                if category not in matching_tags:
                    matching_tags.append(category)
                break  # Found match for this category, move to next
    
    # Return top 3 most relevant tags
    return ", ".join(matching_tags[:3]) if matching_tags else "General Tech"

def get_tag_statistics(jobs_df):
    """Get statistics about job tags."""
    if 'Tags' not in jobs_df.columns or jobs_df.empty:
        return {}
    
    tag_counts = {}
    for tags_str in jobs_df['Tags']:
        if pd.notna(tags_str):
            tags = [tag.strip() for tag in tags_str.split(',')]
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    return dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True))

def filter_jobs_by_tag(jobs_df, selected_tag):
    """Filter jobs by a specific tag."""
    if 'Tags' not in jobs_df.columns or jobs_df.empty:
        return jobs_df
    
    if selected_tag == "All":
        return jobs_df
    
    filtered_df = jobs_df[
        jobs_df['Tags'].str.contains(selected_tag, case=False, na=False)
    ]
    
    return filtered_df.reset_index(drop=True)