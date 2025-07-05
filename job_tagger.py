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
    ],
    "Software Engineering": [
        "software engineer", "software developer", "backend", "frontend",
        "full stack", "microservices", "api design", "rest", "graphql",
        "design patterns", "oop", "typescript", "react", "java", "c++", "go"
    ],
    "Data Engineering & ETL": [
        "data engineer", "etl", "data pipeline", "airflow", "spark", "dask",
        "bigquery", "databricks", "warehousing", "redshift", "snowflake",
        "kinesis", "kafka", "streaming", "batch processing"
    ],
    "MLOps & LLMOps": [
        "mlops", "llmops", "model serving", "model deployment", "model monitoring",
        "kubeflow", "sagemaker", "vertex ai", "mlflow", "feature store",
        "inference", "ab testing", "drift detection", "vector database"
    ],
    "Speech & Audio": [
        "speech", "asr", "speech recognition", "tts", "voice assistant",
        "audio processing", "music information retrieval", "speaker diarization",
        "audio classification", "sound event detection"
    ],
    "Cybersecurity & Privacy": [
        "cybersecurity", "security engineer", "infosec", "penetration testing",
        "vulnerability", "threat detection", "siem", "incident response",
        "privacy", "gdpr", "pki", "zero trust", "iam"
    ],
    "Augmented / Virtual Reality": [
        "ar", "vr", "mixed reality", "xr", "oculus",
        "hololens", "3d graphics", "rendering", "spatial computing"
    ],
    "Autonomous Vehicles": [
        "autonomous vehicle", "self driving", "ad as", "lidar", "sensor fusion",
        "slam", "path planning", "drive sim", "perception stack", "automotive safety"
    ],
    "Edge & Embedded AI": [
        "edge ai", "embedded ai", "tinyml", "micropython", "tflite", "rtos",
        "arm cortex", "nvidia jetson", "raspberry pi", "low-power inference"
    ],
    "Quantum Computing": [
        "quantum computing", "quantum algorithms", "qiskit", "cirq", "quantum error correction",
        "superconducting qubits", "quantum annealing", "quantum machine learning"
    ],
    "EdTech & Learning Analytics": [
        "edtech", "education technology", "learning analytics", "adaptive learning",
        "lms", "moodle", "canvas", "mooc", "student success", "assessment analytics"
    ],
    "Climate Tech & Sustainability": [
        "climate tech", "sustainability", "carbon accounting", "energy modeling",
        "renewables", "climate risk", "emissions", "smart grid", "agritech", "environmental"
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