import os
from dotenv import load_dotenv

def load_config():
    """
    Loads and validates environment variables from the .env file.
    
    Returns:
        dict: A dictionary containing validated configuration variables.
    
    Raises:
        ValueError: If any required configuration variable is missing.
    """
    load_dotenv()

    required_vars = [
        "FACEBOOK_APP_ID",
        "FACEBOOK_APP_SECRET",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_PAGE_ACCESS_TOKEN"
    ]

    config = {}
    for var in required_vars:
        val = os.getenv(var)
        if not val or val.strip() == "":
            raise ValueError(f"{var} is missing from .env")
        config[var] = val.strip()

    return config
