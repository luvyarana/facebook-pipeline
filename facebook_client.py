import requests

def fetch_page_posts(page_id, access_token):
    """
    Fetches posts from a Facebook Page using Meta Graph API v26.0.
    
    Args:
        page_id (str): The Facebook Page ID.
        access_token (str): The Facebook Page Access Token.
        
    Returns:
        dict: Parsed JSON response containing post data from Facebook Graph API.
        
    Raises:
        RuntimeError: If the API request fails or times out (without exposing token).
    """
    url = f"https://graph.facebook.com/v26.0/{page_id}/posts"
    params = {
        "fields": "id,message,created_time",
        "access_token": access_token
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        # Extract clean error message from Facebook JSON response if present
        error_msg = "HTTP Error encountered while calling Facebook Graph API."
        try:
            err_json = response.json()
            if "error" in err_json and "message" in err_json["error"]:
                error_msg = f"Facebook Graph API Error: {err_json['error']['message']}"
        except Exception:
            pass
        raise RuntimeError(error_msg) from None
    except requests.exceptions.Timeout:
        raise RuntimeError("Request to Facebook Graph API timed out. Please check your network connection.") from None
    except requests.exceptions.RequestException:
        raise RuntimeError("Failed to connect to Facebook Graph API.") from None
