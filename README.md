# MCP Intelligent Email Agent

This [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server transforms Claude Desktop into an intelligent email assistant. Unlike basic email scripts, this server allows Claude to read your inbox, fetch a specific style guide from a live Google Doc, and generate context-aware draft replies that match your personal or brand voice.

## How it Works
1. **Read**: Claude uses the `read_emails` tool to fetch messages via IMAP.
2. **Consult**: The server fetches your latest writing preferences from a Google Doc Style Guide.
3. **Draft**: Claude generates a reply based on the email context and the style guide.
4. **Stage**: The server saves the reply directly into your **Gmail Drafts** folder for your final approval.

## Features
- **Dynamic Style Sync**: Pulls writing constraints from Google Docs using a Service Account.
- **MIME Parsing**: Automatically handles multipart emails, prioritizing plain text over HTML for cleaner LLM context.
- **Security-First**: Uses a "Read-and-Draft" workflow. The server cannot "Send" emails, ensuring a human always has the final review.

## Prerequisites
- **Python 3.10+**
- **Anthropic API Key**: To power the drafting logic.
- **Google Service Account**: With "Google Docs API" enabled and access to your style guide document.
- **Gmail App Password**: For secure IMAP access.

## Installation

### 1. Project Navigation

Navigate to your cloned project directory:

```bash
cd ~/mcp-servers/email
```

### 2. Virtual Environment Setup

Create and activate a virtual environment to keep dependencies isolated:

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt 
```

### 4. Environment Setup

```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
PASSWORD=your_16_char_app_password
```

### 5. Google Cloud & Style Guide Setup

#### A. Create the Service Account
1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Enable the Google Docs API**: Search for "Google Docs API" in the library and click **Enable**.
3.  **Navigate to Credentials**: Go to `APIs & Services` > `Credentials`.
4.  **Create Credentials**: Click `Create Credentials` > `Service Account`.
5.  **Generate JSON Key**:
    * Once the account is created, click on its email address to open the settings.
    * Go to the **Keys** tab.
    * Click **Add Key** > **Create New Key**.
    * Select **JSON** and click **Create**.
6.  **Rename & Move**: Rename the downloaded file to `google-service-account.json` and place it in your project root directory.

#### B. Setup the Style Guide
1.  **Create the Doc**: Open a new Google Doc and write out your specific email tone, formatting rules, or brand style preferences.
2.  **Copy the Document ID**: Look at the URL in your browser. The ID is the long string of characters between `/d/` and `/edit`.
    * *Example:* `https://docs.google.com/document/d/`**`1A2b3C4d5E6fG7h8I9j0_KLmNoP`**`/edit`
3.  **Grant Access**: 
    * Open your `google-service-account.json` and copy the `client_email` address.
    * In your Style Guide Google Doc, click **Share**.
    * Paste the `client_email` and grant it **Viewer** access.

### 6. Configuration for Claude Desktop

Add this configuration to your claude_desktop_config.json:

Path (Linux/WSL): ```bash 
~/.config/Claude/claude_desktop_config.json```

Path (Mac): ```bash
~/Library/Application Support/Anthropic/Claude/claude_desktop_config.json```

```json
{
  "mcpServers": {
    "email-agent": {
      "command": "/PATH/TO/YOUR/PROJECT/venv/bin/python",
      "args": [
        "/PATH/TO/YOUR/PROJECT/email_server.py"
      ],
      "env": {
        "EMAIL_USER": "your_gmail_address@gmail.com",
        "EMAIL_APP_PASSWORD": "your_16_char_app_password",
      }
    }
  }
}
```

### Usage Examples
Once configured and Claude Desktop is restarted, you can ask:

"Get my last unread email and create a draft reply using the style guide provided."
