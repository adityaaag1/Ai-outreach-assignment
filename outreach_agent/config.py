import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Model Configuration
GROQ_MODEL_NAME = "llama-3.3-70b-versatile"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Our Product Configuration
# This is a generic description of our product to be used when drafting outreach.
OUR_PRODUCT_DESCRIPTION = """
We provide an AI-powered B2B outreach research platform that automates the discovery of 
company pain points and drafts highly personalized outreach messages based on real evidence.
Our platform saves sales teams hours of manual research and increases reply rates by 
ensuring every message is highly relevant and tailored to the prospect's specific challenges.
"""

# Search Configuration
MAX_SEARCH_RESULTS = 3
SEARCH_TIMEOUT_SECONDS = 10
