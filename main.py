import json
from facebook_client import get_page_posts

def main():
    print("Fetching page posts from Facebook...")
    
    try:
        # Call our function to get the data
        posts_data = get_page_posts()
        
        # Pretty-print the JSON response
        # indent=4 makes it easy to read for beginners
        print(json.dumps(posts_data, indent=4))
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
