import sys
import logging
from config import load_config
from facebook_client import fetch_all_page_posts, parse_post_metrics, GRAPH_API_VERSION
from storage import save_raw_response

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("main")

def main():
    # 1. Load configuration
    try:
        config = load_config()
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)

    page_id = config["FACEBOOK_PAGE_ID"]
    access_token = config["FACEBOOK_PAGE_ACCESS_TOKEN"]

    print("========================================")
    print("Facebook Page Data Pipeline")
    print(f"Graph API Version: {GRAPH_API_VERSION}")
    print("========================================")
    print(f"Page ID: {page_id}")
    print("\nFetching posts with pagination and saving raw responses...\n")

    total_pages = 0
    total_posts = 0

    # 2. Fetch posts iteratively across all pagination pages
    try:
        for response_json in fetch_all_page_posts(
            page_id=page_id,
            access_token=access_token,
            raw_storage_callback=save_raw_response
        ):
            total_pages += 1
            posts = response_json.get("data", [])

            for raw_post in posts:
                total_posts += 1
                # Safely parse metrics with defensive fallbacks
                metrics = parse_post_metrics(raw_post)

                print("----------------------------------------")
                print(f"Post ID: {metrics['id']}")
                print(f"Created Time: {metrics['created_time']}")
                print(f"Message: {metrics['message']}")
                print(f"Shares: {metrics['shares_count']} | Likes: {metrics['likes_count']} | Comments: {metrics['comments_count']}")
                r = metrics['reactions']
                print(f"Reactions -> LIKE: {r['LIKE']}, LOVE: {r['LOVE']}, HAHA: {r['HAHA']}, WOW: {r['WOW']}, SAD: {r['SAD']}, ANGRY: {r['ANGRY']}")
                if metrics['attachments']:
                    att_types = ", ".join([a['type'] for a in metrics['attachments']])
                    print(f"Attachments ({len(metrics['attachments'])}): {att_types}")
                print("----------------------------------------\n")

    except RuntimeError as e:
        logger.error(f"Execution Error: {e}")
        sys.exit(1)

    print("========================================")
    print(f"Pipeline Complete: Processed {total_pages} page(s) and {total_posts} post(s).")
    print("========================================")

if __name__ == "__main__":
    main()
