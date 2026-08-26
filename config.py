import os
from dotenv import load_dotenv #type: ignore

def load_pages(pages_file_path: str = "pages.txt") -> list:
    """
    Loads Page IDs from pages.txt if present and non-empty.
    Ignores empty lines, surrounding whitespace, and lines starting with '#'.
    """
    page_ids = []
    if os.path.exists(pages_file_path):
        with open(pages_file_path, "r", encoding="utf-8") as f:
            for line in f:
                line_str = line.strip()
                if line_str and not line_str.startswith("#"):
                    page_ids.append(line_str)
    return page_ids


def load_config(pages_file_path: str = "pages.txt"):
    """
    Loads and validates configuration from environment variables and optional pages.txt.

    Returns:
        dict: A dictionary containing validated configuration variables and PAGE_IDS list.

    Raises:
        ValueError: If required configuration is missing.
    """
    load_dotenv()

    required_vars = [
        "FACEBOOK_APP_ID",
        "FACEBOOK_APP_SECRET",
        "FACEBOOK_PAGE_ACCESS_TOKEN"
    ]

    config = {}
    for var in required_vars:
        val = os.getenv(var)
        if not val or val.strip() == "":
            raise ValueError(f"{var} is missing from .env")
        config[var] = val.strip()

    # Step 6: Load Page IDs from pages.txt if present and non-empty; otherwise fall back to FACEBOOK_PAGE_ID in .env
    page_ids = load_pages(pages_file_path)
    if not page_ids:
        env_page_id = os.getenv("FACEBOOK_PAGE_ID", "").strip()
        if env_page_id:
            page_ids = [pid.strip() for pid in env_page_id.split(",") if pid.strip()]
        else:
            raise ValueError("No Page IDs found in pages.txt and FACEBOOK_PAGE_ID is missing from .env")

    config["PAGE_IDS"] = page_ids
    # Keep FACEBOOK_PAGE_ID pointing to first Page ID for backward compatibility
    config["FACEBOOK_PAGE_ID"] = page_ids[0]

    # RUN_INTERVAL_SECONDS optional check from .env
    interval_env = os.getenv("RUN_INTERVAL_SECONDS")
    if interval_env and interval_env.strip().isdigit():
        config["RUN_INTERVAL_SECONDS"] = int(interval_env.strip())
    else:
        config["RUN_INTERVAL_SECONDS"] = None

    return config

