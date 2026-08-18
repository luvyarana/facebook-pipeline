# Facebook Pipeline

A lightweight Python pipeline to fetch Facebook Page posts using the Meta Graph API and display them cleanly in the terminal.

---

## 📌 Overview

This project connects to the **Meta Graph API** to retrieve post details (Post ID, Message content, and Creation Timestamp) from a designated Facebook Page. It is designed with a clean, simple architecture focusing purely on data acquisition and console output.

---

## 🏗️ Architecture Flow

```text
Facebook Page
      ↓
Meta Graph API
      ↓
Page Access Token
      ↓
facebook_client.py
      ↓
main.py
      ↓
Terminal output
```

---

## 📁 Project Structure

```text
facebook-pipeline/
│
├── .env                  # Environment variables (credentials) - DO NOT COMMIT
├── .gitignore            # Specifies intentionally untracked files to ignore
├── README.md             # Project documentation and guide
├── config.py             # Configuration loader and validator using python-dotenv
├── facebook_client.py    # Client module to interact with Meta Graph API
├── main.py               # Application entry point & terminal formatter
└── requirements.txt      # Project Python dependencies
```

---

## 🔒 Security Notice

> [!CAUTION]
> **NEVER commit the `.env` file or hardcode credentials!**
> Real values for `FACEBOOK_APP_SECRET` and `FACEBOOK_PAGE_ACCESS_TOKEN` must strictly reside inside your local `.env` file and must **NEVER** be pushed to GitHub or printed in terminal logs/tracebacks.

---

## ⚙️ Setup & Installation

### 1. Create a Virtual Environment

It's best practice to use a virtual environment to keep your project's dependencies separate. Navigate to the project directory and create a Python virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  venv\Scripts\activate
  ```
- **Windows (PowerShell):**
  ```powershell
  .\venv\Scripts\activate
  ```

### 2. Install Dependencies

Install the required Python packages (`requests` and `python-dotenv`):

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Create a `.env` file in the root directory. Fill in your Facebook Graph API credentials:

```env
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
```

### Environment Variables Explained

| Variable | Description |
|---|---|
| `FACEBOOK_APP_ID` | Meta Developer App ID created in Meta for Developers dashboard |
| `FACEBOOK_APP_SECRET` | Meta Developer App Secret |
| `FACEBOOK_PAGE_ID` | Numeric ID of the target Facebook Page |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | Generated Page Access Token with `pages_read_engagement` permission |

*Note: The `.gitignore` file is already set up to ignore your `.env` file.*

---

## 🚀 Usage

Run the main script from your terminal:

```bash
python main.py
```

---

## 💻 Example Output

```text
========================================
Facebook Page Data
========================================

Page ID: 1208396852359744

Fetching posts...

----------------------------------------
Post ID:
1208396852359744_123456789

Message:
Question of the Day...

Created Time:
2026-07-31T13:57:14+0000
----------------------------------------

Successfully fetched 1 posts.
```
