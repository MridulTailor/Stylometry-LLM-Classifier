import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Environment variables
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Database
    DB_PATH = "provenance.db"
    
    # API Rate Limits
    RATE_LIMIT = "10 per minute;100 per day"
    
    # Models
    GROQ_MODEL = "llama-3.3-70b-versatile"
