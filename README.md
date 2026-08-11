# Facebook Pipeline

A beginner-friendly data acquisition pipeline to fetch posts from a Facebook Page using the Graph API.

## Setup Instructions

Follow these steps to run the project on your machine.

### 1. Create a Virtual Environment

It's best practice to use a virtual environment to keep your project's dependencies separate.

Run this command in your terminal to create one:
```bash
python3 -m venv venv
```

Activate the virtual environment:
- On Mac/Linux:
  ```bash
  source venv/bin/activate
  ```
- On Windows:
  ```bash
  venv\Scripts\activate
  ```

### 2. Install Requirements

Install the necessary Python packages (`requests` and `python-dotenv`) by running:
```bash
pip install -r requirements.txt
```

### 3. Create the `.env` File

This project uses a `.env` file to securely store your API keys.

1. Open the `.env` file in the project folder.
2. Fill in your Facebook Graph API credentials:

```env
FACEBOOK_APP_ID=your_app_id_here
FACEBOOK_APP_SECRET=your_app_secret_here
FACEBOOK_PAGE_ID=your_page_id_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_access_token_here
```

*Note: Never commit your actual `.env` file to a public repository. The `.gitignore` file is already set up to ignore it.*

### 4. Run the Script

To fetch your page posts and print them to the console, run:
```bash
python main.py
```
