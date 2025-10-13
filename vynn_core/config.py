import os
from pathlib import Path
from dotenv import load_dotenv
# Look for .env file in the project root of the consuming application
env_path = Path.cwd() / '.env'
load_dotenv(env_path)

# Database configuration - loaded from .env file
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")
