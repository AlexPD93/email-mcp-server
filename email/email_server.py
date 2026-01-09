#!/usr/bin/env python3
# 1. Standard Library Imports
import asyncio
import os
import time
import email
import email.utils
import imaplib
from email.header import decode_header
from email.mime.text import MIMEText

# 2. Third-Party Imports (MCP SDK)
from mcp.server import Server
import mcp.server.stdio
import mcp.types as types

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from anthropic import AsyncAnthropic

from dotenv import load_dotenv

load_dotenv()

anthropic_client = AsyncAnthropic()

server = Server("email-server")

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

SERVICE_ACCOUNT_FILE = os.path.join(
    os.path.dirname(__file__), "google-service-account.json"
)
DOCUMENT_ID = "12LSYG255PdWUUX6XfYFK9kHFjduu08abmDmjkdVv-5U"
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_emails",
            description="Read your emails",
            inputSchema={
                "type": "object",
                "properties": {
                    "mailbox": {
                        "type": "string",
                        "description": "The mailbox to read from (e.g., 'INBOX').",
                    },
                    "search_criteria": {
                        "type": "string",
                        "description": "The status of the email e.g SEEN or UNSEEN.",
                    },
                    "limit": {
                        "type": "number",
                        "description": "The limit amount of emails to fetch.",
                    },
                },
                "required": ["mailbox"],
            },
        ),
        types.Tool(
            name="create_draft_reply",
            description="Generates a draft reply using Claude and saves it to a specific email thread.",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {
                        "type": "string",
                        "description": "The unique ID of the message to reply to (e.g., the IMAP UID).",
                    },
                    "email_content": {
                        "type": "string",
                        "description": "The full text of the original email to provide context to Claude.",
                    },
                },
                "required": ["email_id", "email_content"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    email_user = os.environ["EMAIL_USER"]
    email_password = os.environ["EMAIL_APP_PASSWORD"]

    if name == "read_emails":
        mailbox = arguments.get("mailbox", "INBOX")
        limit = arguments.get("limit", 5)
        search_criteria = arguments.get("search_criteria", "UNSEEN")

        try:
            imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
            imap.login(email_user, email_password)
            imap.select(mailbox, readonly=True)
            status, data = imap.search(None, search_criteria)
            email_ids = data[0].split()
            latest_email_ids = email_ids[-limit:][::-1]

            results = []
            for email_id in latest_email_ids:
                status, msg_data = imap.fetch(email_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject, encoding = decode_header(msg["Subject"])[0]
                if encoding:
                    subject = subject.decode(encoding)

                email_body = extract_body(msg)

                results.append(
                    {
                        "id": email_id.decode(),
                        "from": msg.get("From"),
                        "subject": subject,
                        "date": msg.get("Date"),
                        "body": email_body,
                    }
                )

            imap.close()
            imap.logout()

            output_text = "Retrieved emails:\n"
            for res in results:
                output_text += f"ID: {res['id']}\n"
                output_text += f"From: {res['from']}\n"
                output_text += f"Subject: {res['subject']}\n"
                output_text += f"Date: {res['date']}\n\n"
                output_text += f"Body:\n{res['body']}\n\n"

            return [types.TextContent(type="text", text=output_text)]

        except imaplib.IMAP4.error as e:
            return [types.TextContent(type="text", text=f"Error reading emails: {e}")]
        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"An unexpected error occurred: {e}"
                )
            ]

    elif name == "create_draft_reply":
        email_id = arguments.get("email_id")
        email_content = arguments.get("email_content")
        style_guide_text = await fetch_style_guide()

        try:
            draft_reply_text = await request_claude_reply(
                email_content, style_guide_text
            )

            draft_confirmation = save_draft_via_imap(
                email_user, email_password, email_id, draft_reply_text
            )

            return [
                types.TextContent(
                    type="text",
                    text=f"✓ Draft reply generated by Claude and saved for message ID {email_id}. {draft_confirmation}",
                )
            ]

        except Exception as e:
            return [
                types.TextContent(
                    type="text", text=f"Error generating or saving draft: {e}"
                )
            ]


async def request_claude_reply(original_content: str, style_guide: str) -> str:
    """
    Sends the original email content to Claude and returns the generated reply text.
    """

    system_prompt = (
        "You are an assistant dedicated to generating concise, professional, "
        "and helpful email replies. Do not include salutations or subject lines. "
        "Follow the style guide strictly."
    )

    user_prompt = (
        f"Style guide:\n{style_guide}\n\n"
        f"Original email:\n---\n{original_content}\n---\n"
        f"Write a draft reply according to the style guide."
    )

    completion = await anthropic_client.messages.create(
        model="claude-sonnet-4-5-20250929",
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        max_tokens=500,
    )

    return completion.content[0].text


async def fetch_style_guide() -> str:
    """
    Fetches the Google Docs style guide text using a service account.
    """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service: Resource = build("docs", "v1", credentials=credentials)
    doc = service.documents().get(documentId=DOCUMENT_ID).execute()

    # Extract all text from the document
    style_guide_text = ""
    for element in doc.get("body", {}).get("content", []):
        paragraph = element.get("paragraph")
        if paragraph:
            for run in paragraph.get("elements", []):
                text_run = run.get("textRun")
                if text_run:
                    style_guide_text += text_run.get("content", "")
    return style_guide_text


def extract_body(msg):

    body_content = ""
    html_content = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            if (
                content_disposition is not None
                and content_disposition.lower().startswith("attachment")
            ):
                continue

            if content_type == "text/plain":
                try:
                    charset = part.get_content_charset()
                    body_content = part.get_payload(decode=True).decode(
                        charset or "utf-8", errors="ignore"
                    )
                except Exception:
                    continue
            elif content_type == "text/html":
                try:
                    charset = part.get_content_charset()
                    html_content = part.get_payload(decode=True).decode(
                        charset or "utf-8", errors="ignore"
                    )
                except Exception:
                    continue
        return body_content or html_content
    else:
        content_type = msg.get_content_type()
        if content_type.startswith("text/"):
            try:
                charset = msg.get_content_charset()
                body_content = msg.get_payload(decode=True).decode(
                    charset or "utf-8", errors="ignore"
                )
            except Exception:
                return "Could not decode message body."
    return "No readable body found."


def save_draft_via_imap(
    email_user: str, email_password: str, original_id: str, reply_body: str
):
    """Saves the generated reply as a draft in Gmail using IMAP APPEND."""

    imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    imap.login(email_user, email_password)

    # Fetch original headers
    imap.select("INBOX", readonly=True)
    status, msg_data = imap.fetch(
        original_id, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT MESSAGE-ID REFERENCES)])"
    )
    if status != "OK":
        imap.logout()
        raise imaplib.IMAP4.error(
            f"Failed to fetch original headers for ID {original_id}: {msg_data}"
        )

    header_data = msg_data[0][1]
    original_message = email.message_from_bytes(header_data)

    original_from = original_message.get("From")
    original_subject = original_message.get("Subject")
    original_message_id = original_message.get("Message-ID")
    original_references = original_message.get("References", "")

    _, reply_to_address = email.utils.parseaddr(original_from)

    msg = MIMEText(reply_body, "plain")
    msg["From"] = email_user
    msg["To"] = reply_to_address
    msg["Subject"] = (
        f"Re: {original_subject}"
        if not original_subject.lower().startswith("re:")
        else original_subject
    )
    msg["In-Reply-To"] = original_message_id
    msg["References"] = f"{original_references} {original_message_id}".strip()

    full_message = msg.as_bytes()

    # Append to Gmail Drafts
    imap.select("[Gmail]/Drafts", readonly=False)
    status, data = imap.append(
        "[Gmail]/Drafts",
        "(\\Draft)",
        imaplib.Time2Internaldate(time.time()),
        full_message,
    )

    imap.close()
    imap.logout()

    if status != "OK":
        raise imaplib.IMAP4.error(f"Failed to save draft: {data}")

    return f"Draft saved successfully for thread ID {original_id}. Recipient: {reply_to_address}"


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
