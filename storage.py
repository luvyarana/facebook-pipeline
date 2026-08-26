import os
import json
import sqlite3
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


def init_sqlite_db(db_path: str = "data/facebook_pipeline.db"):
    """
    Initializes the SQLite database and creates the 'posts' table if it does not exist.
    Safe to call multiple times.
    """
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id TEXT PRIMARY KEY,
                page_id TEXT NOT NULL,
                message TEXT,
                created_time TEXT,
                media_type TEXT,
                media_url TEXT,
                likes_count INTEGER DEFAULT 0,
                comments_count INTEGER DEFAULT 0,
                shares_count INTEGER DEFAULT 0,
                reactions_like INTEGER DEFAULT 0,
                reactions_love INTEGER DEFAULT 0,
                reactions_haha INTEGER DEFAULT 0,
                reactions_wow INTEGER DEFAULT 0,
                reactions_sad INTEGER DEFAULT 0,
                reactions_angry INTEGER DEFAULT 0,
                fetched_at TEXT
            );
        """)
        conn.commit()


def save_processed_posts(posts: list, db_path: str = "data/facebook_pipeline.db") -> int:
    """
    Upserts normalized post dictionaries into the SQLite database.
    Uses 'ON CONFLICT(post_id) DO UPDATE' to prevent duplicate rows and update metrics.

    Returns:
        int: Number of rows inserted/updated.
    """
    if not posts:
        return 0

    init_sqlite_db(db_path)

    upsert_sql = """
        INSERT INTO posts (
            post_id, page_id, message, created_time, media_type, media_url,
            likes_count, comments_count, shares_count,
            reactions_like, reactions_love, reactions_haha, reactions_wow, reactions_sad, reactions_angry,
            fetched_at
        ) VALUES (
            :post_id, :page_id, :message, :created_time, :media_type, :media_url,
            :likes_count, :comments_count, :shares_count,
            :reactions_like, :reactions_love, :reactions_haha, :reactions_wow, :reactions_sad, :reactions_angry,
            :fetched_at
        )
        ON CONFLICT(post_id) DO UPDATE SET
            page_id = excluded.page_id,
            message = excluded.message,
            created_time = excluded.created_time,
            media_type = excluded.media_type,
            media_url = excluded.media_url,
            likes_count = excluded.likes_count,
            comments_count = excluded.comments_count,
            shares_count = excluded.shares_count,
            reactions_like = excluded.reactions_like,
            reactions_love = excluded.reactions_love,
            reactions_haha = excluded.reactions_haha,
            reactions_wow = excluded.reactions_wow,
            reactions_sad = excluded.reactions_sad,
            reactions_angry = excluded.reactions_angry,
            fetched_at = excluded.fetched_at;
    """

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.executemany(upsert_sql, posts)
        conn.commit()
        return cursor.rowcount

