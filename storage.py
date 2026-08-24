import os
import json
from datetime import datetime

def save_raw_response(page_id: str, page_number: int, raw_data: dict, run_timestamp: str = None) -> str:
    """
    Saves the original untouched API JSON response to disk.

    Target path structure:
        data/raw/facebook/YYYY-MM-DD/<run_timestamp>/page_<PAGE_ID>_page_<PAGE_NUMBER:03d>.json

    Args:
        page_id (str): Facebook Page ID.
        page_number (int): 1-based page index of the pagination sequence.
        raw_data (dict): Exact JSON dictionary returned by Facebook Graph API.
        run_timestamp (str, optional): Run execution timestamp string (e.g. YYYYMMDD_HHMMSS).

    Returns:
        str: Relative filepath of the saved JSON file.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    if not run_timestamp:
        run_timestamp = now.strftime("%Y%m%d_%H%M%S")

    target_dir = os.path.join("data", "raw", "facebook", date_str, run_timestamp)
    os.makedirs(target_dir, exist_ok=True)

    filename = f"page_{page_id}_page_{page_number:03d}.json"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, indent=2, ensure_ascii=False)

    return filepath
