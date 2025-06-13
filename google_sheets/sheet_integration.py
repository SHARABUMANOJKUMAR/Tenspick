# google_sheets/sheet_integration.py

import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2.service_account import Credentials  # For store_chat_to_sheet

# ------------------------------
# 📩 Contact Form Submission
# ------------------------------
def save_to_google_sheet(data):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('google_sheets/credentials.json', scope)
    client = gspread.authorize(creds)

    sheet = client.open("TensPick Contact Data").sheet1
    sheet.append_row([data["name"], data["email"], data["phone"], data["project"], data["message"]])

# ------------------------------
# 💬 Store Chatbot Interaction
# ------------------------------
def store_chat_to_sheet(user_msg, ai_reply):
    SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    SERVICE_ACCOUNT_FILE = "google_sheets/tenspick-key.json"  # Path to service account key
    SPREADSHEET_ID = "https://docs.google.com/spreadsheets/d/1lP2UXaST1MjqJZF6fs1xY2Ky4juSLMmvGYowerRhI_A/edit?gid=497673416#gid=497673416"  # 🔁 Replace with actual Google Sheet ID

    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1

    # Prepare and append row
    row = [str(datetime.datetime.now()), user_msg, ai_reply]
    sheet.append_row(row)
