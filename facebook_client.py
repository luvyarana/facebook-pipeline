import logging
import requests

GRAPH_API_VERSION = "v26.0"

logger = logging.getLogger(__name__)

# Expanded Graph API fields string for Step 2
EXPANDED_FIELDS = (
    "id,message,created_time,"
    "attachments{media,type,url,title,description,subattachments},"
    "shares,"
    "likes.summary(true),"
    "comments.summary(true),"
    "reactions.type(LIKE).summary(true).as(reactions_like),"
    "reactions.type(LOVE).summary(true).as(reactions_love),"
    "reactions.type(HAHA).summary(true).as(reactions_haha),"
    "reactions.type(WOW).summary(true).as(reactions_wow),"
    "reactions.type(SAD).summary(true).as(reactions_sad),"
    "reactions.type(ANGRY).summary(true).as(reactions_angry)"
)


def fetch_all_page_posts(page_id: str, access_token: str, raw_storage_callback=None):
    """
    Fetches all posts from a Facebook Page using Meta Graph API with pagination support.

    Args:
        page_id (str): The Facebook Page ID.
        access_token (str): The Facebook Page Access Token.
        raw_storage_callback (callable, optional): Callback function (page_id, page_number, raw_data)
                                                   to save raw untouched API response.

    Yields:
        dict: Raw response JSON for each page fetched.

    Raises:
        RuntimeError: If authentication fails, API times out, or network fails.
    """
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{page_id}/posts"
    params = {
        "fields": EXPANDED_FIELDS,
        "limit": 100,
        "access_token": access_token
    }

    page_number = 1
    next_url = None
    seen_urls = set()

    while True:
        try:
            if page_number == 1:
                logger.info(f"Fetching initial page of posts for Page ID: {page_id} using Graph API {GRAPH_API_VERSION}...")
                response = requests.get(url, params=params, timeout=15)
            else:
                logger.info(f"Fetching page {page_number} using next URL...")
                # STEP 3 CRITICAL: Request next_url directly without re-passing params dictionary
                response = requests.get(next_url, timeout=15)

            response.raise_for_status()
            data = response.json()

        except requests.exceptions.HTTPError as err:
            error_msg = f"HTTP Error encountered calling Graph API ({response.status_code})."
            try:
                err_json = response.json()
                if "error" in err_json:
                    err_detail = err_json["error"]
                    err_code = err_detail.get("code")
                    err_subcode = err_detail.get("error_subcode")
                    msg = err_detail.get("message", "")
                    
                    # Detect authentication/token errors specifically (e.g. OAuthException, code 190)
                    if err_detail.get("type") == "OAuthException" or err_code in (100, 190):
                        error_msg = (
                            f"Authentication Failure (Code {err_code}, Subcode {err_subcode}): "
                            f"{msg}. Please check your FACEBOOK_PAGE_ACCESS_TOKEN in .env."
                        )
                    else:
                        error_msg = f"Facebook Graph API Error (Code {err_code}): {msg}"
            except Exception:
                pass
            
            logger.error(f"Request failed for Page ID {page_id}: {error_msg}")
            raise RuntimeError(error_msg) from None

        except requests.exceptions.Timeout:
            err_msg = "Request to Facebook Graph API timed out. Please check network connection."
            logger.error(err_msg)
            raise RuntimeError(err_msg) from None

        except requests.exceptions.RequestException as e:
            err_msg = f"Failed to connect to Facebook Graph API: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg) from None

        # STEP 4: Invoke raw storage callback BEFORE any parsing or filtering
        if raw_storage_callback:
            try:
                saved_path = raw_storage_callback(page_id, page_number, data)
                logger.info(f"Saved raw response page {page_number} to {saved_path}")
            except Exception as storage_err:
                logger.warning(f"Failed to save raw response for page {page_number}: {storage_err}")

        yield data

        # STEP 3: Handle pagination logic
        paging = data.get("paging", {})
        next_url = paging.get("next")

        if not next_url:
            logger.info("Pagination complete: no further 'paging.next' URL provided.")
            break

        # Infinite loop prevention
        if next_url in seen_urls:
            logger.error(f"Infinite pagination loop detected! Next URL already requested: {next_url}")
            break

        seen_urls.add(next_url)
        page_number += 1


def parse_post_metrics(post: dict) -> dict:
    """
    Defensive parser that extracts post attributes and engagement metrics safely.
    Missing optional fields return default values (0, 'N/A', empty lists) without crashing.
    """
    post_id = post.get("id", "N/A")
    message = post.get("message", "[No text content]")
    created_time = post.get("created_time", "N/A")

    # Shares count
    shares_count = post.get("shares", {}).get("count", 0)

    # Likes summary count
    likes_count = post.get("likes", {}).get("summary", {}).get("total_count", 0)

    # Comments summary count
    comments_count = post.get("comments", {}).get("summary", {}).get("total_count", 0)

    # Reactions breakdown for 6 types
    reactions = {
        "LIKE": post.get("reactions_like", {}).get("summary", {}).get("total_count", 0),
        "LOVE": post.get("reactions_love", {}).get("summary", {}).get("total_count", 0),
        "HAHA": post.get("reactions_haha", {}).get("summary", {}).get("total_count", 0),
        "WOW": post.get("reactions_wow", {}).get("summary", {}).get("total_count", 0),
        "SAD": post.get("reactions_sad", {}).get("summary", {}).get("total_count", 0),
        "ANGRY": post.get("reactions_angry", {}).get("summary", {}).get("total_count", 0)
    }

    # Attachments parsing
    attachments_raw = post.get("attachments", {}).get("data", [])
    attachments = []
    for att in attachments_raw:
        att_type = att.get("type", "unknown")
        media_url = att.get("media", {}).get("image", {}).get("src") or att.get("url", "")
        title = att.get("title", "")
        attachments.append({
            "type": att_type,
            "url": media_url,
            "title": title
        })

    return {
        "id": post_id,
        "message": message,
        "created_time": created_time,
        "shares_count": shares_count,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "reactions": reactions,
        "attachments": attachments
    }
