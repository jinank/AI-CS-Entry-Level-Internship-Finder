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
print(RAPIDAPI_KEY)
print(AIRTABLE_API_KEY)
print(AIRTABLE_BASE_ID)
print(AIRTABLE_TABLE_NAME)
# Airtable setup
api = Api(AIRTABLE_API_KEY)
airtable = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

