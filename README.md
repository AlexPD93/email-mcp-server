# MCP Intelligent Email Agent

This [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server transforms Claude Desktop into an intelligent email assistant. Unlike basic email scripts, this server allows Claude to read your inbox, fetch a specific style guide from a live Google Doc, and generate context-aware draft replies that match your personal or brand voice.

[Image of Model Context Protocol architecture diagram]

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

### 1. Set up Project Directory
```bash
mkdir -p ~/mcp-servers/email
cd ~/mcp-servers/email
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install mcp anthropic google-api-python-client google-auth python-dotenv
```

### 3. Environment Setup
```bash
ANTHROPIC_API_KEY=your_anthropic_key_here
EMAIL_USER=your_email@gmail.com
EMAIL_APP_PASSWORD=your_16_char_app_password
```

### 4. Google Docs Authentication
1. Place your google-service-account.json in the root folder.

2. Share your Google Doc with the email address found in the client_email field of that JSON.

3. Update DOCUMENT_ID in the script with the ID from your Doc's URL.

### 5. Configuration for Claude Desktop
Add this configuration to your claude_desktop_config.json:

Path (Linux/WSL): ```bash 
~/.config/Claude/claude_desktop_config.json```

Path (Mac): ```bash
~/Library/Application Support/Anthropic/Claude/claude_desktop_config.json```

```json
{
  "mcpServers": {
    "email-agent": {
      "command": "/home/alexpdhackney/mcp-servers/email/venv/bin/python",
      "args": ["/home/alexpdhackney/mcp-servers/email/email_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "your_key",
        "EMAIL_USER": "your_email@gmail.com",
        "EMAIL_APP_PASSWORD": "your_app_password"
      }
    }
  }
}
```

### Usage Examples
Once configured and Claude Desktop is restarted, you can ask:

"Check my inbox for any unread emails from the last 24 hours."

"Read email ID 12 and generate a draft reply using my style guide."
