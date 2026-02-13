#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from email_server import save_draft_via_imap

# Load environment variables from .env file
load_dotenv()


def debug_save_draft():
    """
    This script helps debug the save_draft_via_imap function.

    It retrieves the necessary credentials from environment variables
    and calls the function with a sample email to isolate and identify
    any errors that may be occurring.

    The script will print the result of the function call or any
    error messages that are caught.
    """

    # --- CONFIGURATION ---
    # Credentials for the email account
    email_user = os.environ["EMAIL_USER"]
    email_password = os.environ["EMAIL_APP_PASSWORD"]

    # Ensure that the required environment variables are set
    if not all([email_user, email_password]):
        print(
            "Error: Make sure EMAIL_USER and EMAIL_APP_PASSWORD are set in your .env file."
        )
        return

    # --- FUNCTION CALL ---
    # The ID of the email to which the reply is being drafted
    # This should be a valid email ID from the INBOX
    original_id = "3"  # Replace with a valid email ID

    # The content of the draft reply
    reply_body = "This is a test draft reply."

    print("Attempting to save a draft...")

    try:
        # Call the function to save the draft
        result = save_draft_via_imap(
            email_user, email_password, original_id, reply_body
        )
        print("\n--- Success ---")
        print(result)

    except Exception as e:  # pylint: disable=broad-exception-caught
        # Catch and print any exceptions that occur
        print("\n--- Error ---")
        print(f"An error occurred: {e}")
        print("\n--- Troubleshooting ---")
        print(
            "1. Verify that the EMAIL_USER and EMAIL_APP_PASSWORD in your .env file are correct."
        )
        print(
            "2. Make sure that the 'original_id' is a valid and existing email ID in your INBOX."
        )
        print(
            "3. Check that the IMAP server settings in 'email_server.py' are correct for your email provider."
        )
        print(
            "4. Ensure that your email account has IMAP enabled and that app passwords are set up correctly if you are using 2FA."
        )


if __name__ == "__main__":
    debug_save_draft()
