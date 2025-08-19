import os
import base64
from email.utils import parsedate_to_datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DOWNLOAD_DIR = "attachments"

def main():
    """
    Searches for an email, prints its details, and downloads its attachments,
    prepending the email's ISO date to the attachment filename.
    """
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        next_page_token = None
        found_email = False

        print("🔎 Searching for an email with 'gasser' in the subject...")

        while not found_email:
            result = service.users().messages().list(userId="me", pageToken=next_page_token).execute()
            messages = result.get("messages", [])
            if not messages:
                print("No more messages found in your inbox.")
                break

            for msg in messages:
                txt = service.users().messages().get(userId="me", id=msg["id"]).execute()
                payload = txt.get("payload", {})
                headers = payload.get("headers", [])

                email_details = {}
                for header in headers:
                    name = header['name']
                    if name in ["From", "To", "Subject", "Date"]:
                        email_details[name] = header['value']

                subject = email_details.get("Subject", "")

                if 'gasser' in subject.lower():
                    found_email = True

                    print("\n✅ Found it! Here are the details:")
                    print(f"From: {email_details.get('From')}")
                    print(f"To: {email_details.get('To')}")
                    print(f"Date: {email_details.get('Date')}")
                    print(f"Subject: {email_details.get('Subject')}")
                    print("-" * 30)
                    
                    # 1. Convert date to a filename-safe ISO 8601 string
                    date_str = email_details.get('Date')
                    iso_date_prefix = ""
                    if date_str:
                        # Parse the standard email date string into a datetime object
                        dt_object = parsedate_to_datetime(date_str)
                        # Convert to ISO format and replace ':' to make it a valid filename
                        iso_date_prefix = dt_object.isoformat().replace(':', '-') + "_"

                    print("...Now checking for attachments...")
                    parts = payload.get("parts", [])
                    attachments_found = 0
                    if parts:
                        for part in parts:
                            if part.get("filename") and part.get("body") and part["body"].get("attachmentId"):
                                attachments_found += 1
                                original_filename = part["filename"]
                                attachment_id = part["body"]["attachmentId"]
                                
                                print(f"   - Found attachment: {original_filename}")
                                
                                attachment = service.users().messages().attachments().get(
                                    userId="me", messageId=msg["id"], id=attachment_id
                                ).execute()
                                
                                file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                                
                                if not os.path.exists(DOWNLOAD_DIR):
                                    os.makedirs(DOWNLOAD_DIR)
                                    print(f"   - Created directory: {DOWNLOAD_DIR}")
                                
                                # 2. Prepend the date prefix to the original filename
                                new_filename = f"{iso_date_prefix}{original_filename}"
                                path = os.path.join(DOWNLOAD_DIR, new_filename)
                                
                                with open(path, "wb") as f:
                                    f.write(file_data)
                                print(f"   - Successfully saved to '{path}'")
                    
                    if attachments_found == 0:
                        print("...This email has no attachments.")

                    break
            
            if found_email:
                break

            next_page_token = result.get("nextPageToken")
            if not next_page_token and not found_email:
                print("\nReached the end of your inbox, but did not find a matching email.")
                break

    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
