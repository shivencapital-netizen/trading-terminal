import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from a local .env file if present.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Do not hardcode Alpaca keys in source. Use environment variables.
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")

# Optional: override the backend API base URL in frontend using REACT_APP_API_BASE.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def get_alpaca_credentials():
    """Return Alpaca credentials from the current environment or .env file."""
    load_dotenv(BASE_DIR / ".env")
    return os.getenv("ALPACA_API_KEY", ""), os.getenv("ALPACA_SECRET_KEY", "")
