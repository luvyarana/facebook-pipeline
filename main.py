import sys
import time
import logging
import argparse
from datetime import datetime
from config import load_config
from facebook_client import (
    fetch_all_page_posts,
    parse_post_metrics,
    normalize_post,
    GRAPH_API_VERSION,
    FacebookTokenExpiredError,
    FacebookPermissionError,
    FacebookAPIError
)
from storage import save_raw_response, init_sqlite_db, save_processed_posts

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")


def run_pipeline_batch(config: dict) -> bool:
    """
    Runs a single execution batch of the pipeline across all configured Page IDs.
    Returns True if batch succeeded, False if stopped due to token expiry.
    """
    page_ids = config["PAGE_IDS"]
    access_token = config["FACEBOOK_PAGE_ACCESS_TOKEN"]
    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    db_path = "data/facebook_pipeline.db"

    # Ensure SQLite DB & schema exist
    init_sqlite_db(db_path)

    logger.info(f"Starting pipeline run ID: {run_timestamp}")
    logger.info(f"Target Pages count: {len(page_ids)}")

    total_posts_batch = 0

    for page_id in page_ids:
        logger.info(f"--- Processing Page ID: {page_id} ---")
        page_posts_count = 0
        normalized_posts = []

        try:
            for response_json in fetch_all_page_posts(
                page_id=page_id,
                access_token=access_token,
                raw_storage_callback=lambda p_id, p_num, d: save_raw_response(
                    p_id, p_num, d, run_timestamp=run_timestamp
                )
            ):
                raw_posts = response_json.get("data", [])
                for raw_post in raw_posts:
                    page_posts_count += 1
                    # Normalize for SQLite database (Step 7)
                    normalized = normalize_post(raw_post, page_id)
                    normalized_posts.append(normalized)

                    # Metrics for stdout print
                    metrics = parse_post_metrics(raw_post)
                    logger.debug(f"Fetched post ID: {metrics['id']}")

            # Save normalized posts to SQLite (Step 7)
            if normalized_posts:
                rows_saved = save_processed_posts(normalized_posts, db_path=db_path)
                logger.info(f"Successfully upserted {rows_saved} normalized post(s) to SQLite for Page ID {page_id}")

            total_posts_batch += page_posts_count

        except RuntimeError as e:
            # Fatal storage or critical runtime error stops the entire pipeline run immediately
            logger.error(f"CRITICAL STORAGE FAILURE: {e}")
            return False

        except FacebookPermissionError as e:
            # Step 6 Rule: Permission failure skips only the affected Page
            logger.warning(
                f"Skipping Page ID {page_id} due to FacebookPermissionError: {e.message}"
            )
            continue

        except FacebookTokenExpiredError as e:
            # Step 6 Rule: Token expiration stops the ENTIRE batch run immediately
            logger.error(
                f"CRITICAL: Facebook Access Token expired or invalid! Stopping entire pipeline run. Details: {e.message}"
            )
            return False

        except FacebookAPIError as e:
            logger.error(f"Facebook API Error processing Page ID {page_id}: {e.message}")
            continue

        except Exception as e:
            logger.error(f"Unexpected error processing Page ID {page_id}: {e}")
            continue

    logger.info(f"Batch run complete. Total posts processed across all pages: {total_posts_batch}")
    return True


def run_dry_run():
    """
    Executes a dry-run test without making any Facebook API calls.
    Verifies: config loading, pages.txt loading, SQLite DB init, and exception mapping.
    """
    print("========================================")
    print("DRY-RUN / TEST MODE (NO API REQUESTS)")
    print("========================================")

    # 1. Config loading
    print("1. Testing configuration & pages.txt loading...")
    config = load_config()
    print(f"   -> Loaded {len(config['PAGE_IDS'])} Page ID(s): {config['PAGE_IDS']}")
    print(f"   -> Access token present: {'Yes' if config.get('FACEBOOK_PAGE_ACCESS_TOKEN') else 'No'}")

    # 2. SQLite Database initialization
    print("2. Testing SQLite database initialization...")
    test_db = "data/test_dry_run.db"
    init_sqlite_db(test_db)
    print(f"   -> Successfully initialized database schema at: {test_db}")

    # 3. Exception hierarchy verification
    print("3. Testing Exception hierarchy mapping...")
    from facebook_client import map_facebook_error, FacebookTokenExpiredError, FacebookRateLimitError, FacebookPermissionError, FacebookInvalidParamError
    err190 = map_facebook_error(190, "Session expired", 400)
    err4 = map_facebook_error(4, "Application level rate limit", 400)
    err200 = map_facebook_error(200, "Permission error", 403)
    err100 = map_facebook_error(100, "Invalid parameter", 400)

    assert isinstance(err190, FacebookTokenExpiredError), "Code 190 mapping failed"
    assert isinstance(err4, FacebookRateLimitError), "Code 4 mapping failed"
    assert isinstance(err200, FacebookPermissionError), "Code 200 mapping failed"
    assert isinstance(err100, FacebookInvalidParamError), "Code 100 mapping failed"
    print("   -> All exception mappings (190, 4, 200, 100) verified successfully.")

    print("\nDRY-RUN VERIFICATION SUCCESSFUL! All offline components operate correctly.")


def main():
    parser = argparse.ArgumentParser(description="Facebook Page Data Pipeline")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--single-run", action="store_true", help="Run pipeline once and exit")
    group.add_argument("--interval", type=int, help="Run pipeline repeatedly at specified interval in seconds")
    parser.add_argument("--dry-run", action="store_true", help="Run offline verification test without calling Facebook API")

    args = parser.parse_args()

    if args.dry_run:
        run_dry_run()
        sys.exit(0)

    # 1. Load configuration
    try:
        config = load_config()
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)

    # Determine execution mode precedence:
    # 1. --single-run CLI flag
    # 2. --interval <seconds> CLI flag
    # 3. RUN_INTERVAL_SECONDS from .env
    # 4. Default to single-run
    interval_seconds = None

    if args.single_run:
        interval_seconds = None
    elif args.interval is not None:
        interval_seconds = args.interval
    elif config.get("RUN_INTERVAL_SECONDS") is not None:
        interval_seconds = config["RUN_INTERVAL_SECONDS"]

    print("========================================")
    print("Facebook Page Data Pipeline")
    print(f"Graph API Version: {GRAPH_API_VERSION}")
    print(f"Mode: {'Interval (' + str(interval_seconds) + 's)' if interval_seconds else 'Single Run'}")
    print("========================================")

    if interval_seconds:
        logger.info(f"Starting pipeline in interval mode ({interval_seconds} seconds between runs)...")
        while True:
            success = run_pipeline_batch(config)
            if not success:
                logger.error("Pipeline stopped due to critical token failure.")
                sys.exit(1)
            logger.info(f"Sleeping for {interval_seconds} seconds until next interval run...")
            time.sleep(interval_seconds)
    else:
        logger.info("Starting pipeline in single-run mode...")
        success = run_pipeline_batch(config)
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()

