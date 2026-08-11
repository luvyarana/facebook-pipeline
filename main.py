import sys
from config import load_config
from facebook_client import fetch_page_posts

def main():
    # 1. Load configuration
    try:
        config = load_config()
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)

    page_id = config["FACEBOOK_PAGE_ID"]
    access_token = config["FACEBOOK_PAGE_ACCESS_TOKEN"]

    # 2. Print initial header
    print("========================================")
    print("Facebook Page Data")
    print("========================================")
    print(f"\nPage ID: {page_id}")
    print("\nFetching posts...\n")

    # 3. Fetch Facebook Page posts
    try:
        response_json = fetch_page_posts(page_id, access_token)
    except RuntimeError as e:
        print(f"Error fetching posts: {e}", file=sys.stderr)
        sys.exit(1)

    posts = response_json.get("data", [])

    if not posts:
        print("No posts found for this Facebook Page.")
        return

    # 4. Process and print each post
    for post in posts:
        post_id = post.get("id", "N/A")
        message = post.get("message", "[No text content]")
        created_time = post.get("created_time", "N/A")

        print("----------------------------------------")
        print("Post ID:")
        print(post_id)
        print("\nMessage:")
        print(message)
        print("\nCreated Time:")
        print(created_time)
        print("----------------------------------------\n")

    # 5. Summary
    print(f"Successfully fetched {len(posts)} posts.")

if __name__ == "__main__":
    main()
