import requests
import config

def get_page_posts():
    """
    Fetches the latest posts from the Facebook Page using the Graph API.
    Returns the JSON response containing the posts.
    """
    # The Facebook Graph API endpoint for page posts
    url = f"https://graph.facebook.com/v18.0/{config.FACEBOOK_PAGE_ID}/posts"
    
    # We need to pass the access token to authenticate the request
    params = {
        "access_token": config.FACEBOOK_PAGE_ACCESS_TOKEN
    }
    
    # Make a GET request to the Facebook Graph API
    response = requests.get(url, params=params)
    
    # Raise an exception if the request failed (e.g., bad token, invalid page ID)
    response.raise_for_status()
    
    # Return the JSON data
    return response.json()
