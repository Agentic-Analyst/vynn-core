import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load .env file from the consuming application's directory
# This will search for .env starting from current directory and going up the directory tree
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # Fallback: try common locations
    possible_paths = [
        Path.cwd() / '.env',
        Path.cwd().parent / '.env', 
        Path(__file__).parent.parent.parent / '.env'  # For development
    ]
    
    for path in possible_paths:
        if path.exists():
            load_dotenv(path)
            break

# Database configuration - loaded from .env file
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB = os.getenv("MONGO_DB")

# Optional: Add validation function for debugging
def validate_config():
    """
    Validate that required environment variables are loaded.
    Call this function to debug configuration issues.
    """
    missing = []
    if not MONGO_URI:
        missing.append("MONGO_URI")
    if not MONGO_DB:
        missing.append("MONGO_DB")
    
    if missing:
        dotenv_path = find_dotenv()
        if dotenv_path:
            print(f"Found .env file at: {dotenv_path}")
        else:
            print("No .env file found in current directory or parent directories")
        
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return {
        "MONGO_URI": MONGO_URI,
        "MONGO_DB": MONGO_DB,
        "dotenv_path": find_dotenv()
    }
