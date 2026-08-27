import time
import logging
import requests
from datetime import datetime, timezone

GRAPH_API_VERSION = "v26.0"

logger = logging.getLogger(__name__)

# Custom Exception Hierarchy for Step 5
class FacebookAPIError(Exception):
    """Base exception for Facebook Graph API errors."""
    def __init__(self, message: str, code: int = None, http_status: int = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status


class FacebookTokenExpiredError(FacebookAPIError):
    """Code 190: Access token expired or invalid."""
    pass


class FacebookRateLimitError(FacebookAPIError):
    """Codes 4, 17: User or App rate limit hit."""
    pass


class FacebookPermissionError(FacebookAPIError):
    """Codes 10, 200, 294: Missing permission for target Page/fields."""
    pass


class FacebookInvalidParamError(FacebookAPIError):
    """Code 100: Invalid parameter or malformed query."""
    pass


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


def _sanitize_text(text: str, access_token: str) -> str:
    """Helper function to prevent exposing access token in log messages or exception text."""
    if access_token and access_token in text:
        return text.replace(access_token, "[REDACTED]")
    return text


def map_facebook_error(err_code: int, msg: str, http_status: int = None, access_token: str = "") -> FacebookAPIError:
    """Maps Facebook numerical error codes to custom exception classes."""
    msg = _sanitize_text(msg, access_token)
    if err_code == 190:
        return FacebookTokenExpiredError(f"Authentication Failure (Code 190): {msg}", code=190, http_status=http_status)
    elif err_code in (4, 17):
        return FacebookRateLimitError(f"Rate Limit Exceeded (Code {err_code}): {msg}", code=err_code, http_status=http_status)
    elif err_code in (10, 200, 294):
        return FacebookPermissionError(f"Permission Error (Code {err_code}): {msg}", code=err_code, http_status=http_status)
    elif err_code == 100:
        return FacebookInvalidParamError(f"Invalid Parameter Error (Code 100): {msg}", code=100, http_status=http_status)
    else:
        return FacebookAPIError(f"Facebook Graph API Error (Code {err_code}): {msg}", code=err_code, http_status=http_status)


def fetch_all_page_posts(page_id: str, access_token: str, raw_storage_callback=None, max_retries: int = 3):
    """
    Fetches all posts from a Facebook Page using Meta Graph API with pagination and rate limit retry support.

    Args:
        page_id (str): The Facebook Page ID.
        access_token (str): The Facebook Page Access Token.
        raw_storage_callback (callable, optional): Callback function (page_id, page_number, raw_data)
                                                   to save raw untouched API response.
        max_retries (int): Maximum retry attempts for rate limit errors.

    Yields:
        dict: Raw response JSON for each page fetched.

    Raises:
        FacebookTokenExpiredError: On token expiration (code 190).
        FacebookPermissionError: On permission errors (codes 10, 200, 294).
        FacebookInvalidParamError: On invalid parameters (code 100).
        FacebookRateLimitError: If rate limit retries are exhausted.
        FacebookAPIError: For other Facebook API errors.
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
        data = None
        attempt = 1

        while attempt <= max_retries + 1:
            try:
                if page_number == 1:
                    logger.info(f"Fetching initial page of posts for Page ID: {page_id} using Graph API {GRAPH_API_VERSION}...")
                    response = requests.get(url, params=params, timeout=15)
                else:
                    logger.info(f"Fetching page {page_number} using next URL...")
                    response = requests.get(next_url, timeout=15)

                response.raise_for_status()
                data = response.json()
                break  # Successful request, exit retry loop

            except requests.exceptions.HTTPError as err:
                status_code = response.status_code
                err_code = None
                msg = ""
                try:
                    err_json = response.json()
                    if "error" in err_json:
                        err_detail = err_json["error"]
                        err_code = err_detail.get("code")
                        msg = err_detail.get("message", "")
                except Exception:
                    msg = str(err)

                fb_exc = map_facebook_error(err_code, msg, http_status=status_code, access_token=access_token)

                # Check if it's a retryable rate limit error
                if isinstance(fb_exc, FacebookRateLimitError):
                    if attempt <= max_retries:
                        wait_seconds = 5 * (2 ** (attempt - 1))
                        logger.warning(
                            f"Rate limit hit for Page {page_id} (Attempt {attempt}/{max_retries}). "
                            f"Retrying in {wait_seconds}s..."
                        )
                        time.sleep(wait_seconds)
                        attempt += 1
                        continue
                    else:
                        logger.error(f"Rate limit retries exhausted for Page {page_id}.")
                        raise fb_exc from None
                else:
                    # Non-retryable Facebook API error (TokenExpired, Permission, InvalidParam, etc.)
                    logger.error(f"Request failed for Page ID {page_id}: {_sanitize_text(str(fb_exc), access_token)}")
                    raise fb_exc from None

            except requests.exceptions.Timeout:
                err_msg = "Request to Facebook Graph API timed out."
                logger.error(err_msg)
                raise FacebookAPIError(err_msg) from None

            except requests.exceptions.RequestException as e:
                sanitized_err = _sanitize_text(str(e), access_token)
                err_msg = f"Failed to connect to Facebook Graph API: {sanitized_err}"
                logger.error(err_msg)
                raise FacebookAPIError(err_msg) from None

        # STEP 4: Invoke raw storage callback BEFORE any parsing or filtering
        if raw_storage_callback and data is not None:
            try:
                saved_path = raw_storage_callback(page_id, page_number, data)
                logger.info(f"Saved raw response page {page_number} to {saved_path}")
            except Exception as storage_err:
                err_msg = f"Failed to save raw response for page {page_number}: {storage_err}"
                logger.error(err_msg)
                raise RuntimeError(err_msg) from storage_err

        yield data

        # STEP 3: Handle pagination logic
        paging = data.get("paging", {}) if data else {}
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


def normalize_post(raw_post: dict, page_id: str) -> dict:
    """
    Step 7: Normalizes a raw Facebook post dictionary into a consistent structure for SQLite storage.
    Defensive against missing optional fields with safe defaults.
    """
    post_id = raw_post.get("id")
    message = raw_post.get("message", "")
    created_time = raw_post.get("created_time", "")

    # Extract top attachment media_type and media_url
    media_type = None
    media_url = None
    attachments_data = raw_post.get("attachments", {}).get("data", [])
    if attachments_data:
        first_att = attachments_data[0]
        media_type = first_att.get("type")
        media_url = first_att.get("media", {}).get("image", {}).get("src") or first_att.get("url")

    # Counts with defaults
    likes_count = raw_post.get("likes", {}).get("summary", {}).get("total_count", 0)
    comments_count = raw_post.get("comments", {}).get("summary", {}).get("total_count", 0)
    shares_count = raw_post.get("shares", {}).get("count", 0)

    # Reactions breakdown with defaults
    reactions_like = raw_post.get("reactions_like", {}).get("summary", {}).get("total_count", 0)
    reactions_love = raw_post.get("reactions_love", {}).get("summary", {}).get("total_count", 0)
    reactions_haha = raw_post.get("reactions_haha", {}).get("summary", {}).get("total_count", 0)
    reactions_wow = raw_post.get("reactions_wow", {}).get("summary", {}).get("total_count", 0)
    reactions_sad = raw_post.get("reactions_sad", {}).get("summary", {}).get("total_count", 0)
    reactions_angry = raw_post.get("reactions_angry", {}).get("summary", {}).get("total_count", 0)

    fetched_at = datetime.now(timezone.utc).isoformat()

    return {
        "post_id": post_id,
        "page_id": page_id,
        "message": message,
        "created_time": created_time,
        "media_type": media_type,
        "media_url": media_url,
        "likes_count": likes_count,
        "comments_count": comments_count,
        "shares_count": shares_count,
        "reactions_like": reactions_like,
        "reactions_love": reactions_love,
        "reactions_haha": reactions_haha,
        "reactions_wow": reactions_wow,
        "reactions_sad": reactions_sad,
        "reactions_angry": reactions_angry,
        "fetched_at": fetched_at
    }


def parse_post_metrics(post: dict) -> dict:
    """
    Defensive parser that extracts post attributes and engagement metrics safely for stdout printing.
    """
    post_id = post.get("id", "N/A")
    message = post.get("message", "[No text content]")
    created_time = post.get("created_time", "N/A")

    shares_count = post.get("shares", {}).get("count", 0)
    likes_count = post.get("likes", {}).get("summary", {}).get("total_count", 0)
    comments_count = post.get("comments", {}).get("summary", {}).get("total_count", 0)

    reactions = {
        "LIKE": post.get("reactions_like", {}).get("summary", {}).get("total_count", 0),
        "LOVE": post.get("reactions_love", {}).get("summary", {}).get("total_count", 0),
        "HAHA": post.get("reactions_haha", {}).get("summary", {}).get("total_count", 0),
        "WOW": post.get("reactions_wow", {}).get("summary", {}).get("total_count", 0),
        "SAD": post.get("reactions_sad", {}).get("summary", {}).get("total_count", 0),
        "ANGRY": post.get("reactions_angry", {}).get("summary", {}).get("total_count", 0)
    }

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

