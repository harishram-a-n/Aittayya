# main.py (Corrected Version)

import functions_framework
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from googleapiclient.discovery import build
import google.auth # <-- THIS IMPORT WAS MISSING

# --- CONFIGURATION ---
PARKING_SHEET_ID = '1zZhqre5G80my5tQLwLkJL3mjlBe8PEGrbbfM34XQDcQ'
PARKING_SHEET_RANGE = 'kulasai 2025!A:I'
PARKING_FIRESTORE_COLLECTION = 'parking_lots'

CONTENT_SHEET_ID = '1Dhr9siyS-lKZMEr3iUzsWKtPXsgtykM0ZfA5FiyA1uM'
CONTENT_SHEET_RANGE = 'WebsiteContent!A:C'
CONTENT_FIRESTORE_COLLECTION = 'website_content'
CONTENT_FIRESTORE_DOCUMENT = 'landing_page'

logging.basicConfig(level=logging.INFO)

# --- INITIALIZE FIRESTORE ---
try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    db = firestore.client()
    print("Firestore initialized successfully.")
except Exception as e:
    logging.error(f"FATAL: Failed to initialize Firestore: {e}", exc_info=True)
    db = None

def _sanitize_header(h): return h.strip().lower().replace(' ', '_').replace('/', '_').replace('.', '').replace('%', '')

@functions_framework.http
def sync_data_http(request):
    """HTTP Cloud Function to sync data from Google Sheets to Firestore."""
    if not db:
        return ("Firestore not initialized", 500)

    try:
        # Use Application Default Credentials to build the Sheets service
        sheets_creds, project = google.auth.default(scopes=['https://www.googleapis.com/auth/spreadsheets.readonly'])
        sheets_service = build('sheets', 'v4', credentials=sheets_creds)
        print("Google Sheets API service built successfully.")
    except Exception as e:
        logging.error(f"Failed to build Sheets service: {e}", exc_info=True)
        return ("Failed to build Sheets service", 500)

    errors = []

    # Sync Website Content
    try:
        print("Syncing Website Content...")
        result = sheets_service.spreadsheets().values().get(spreadsheetId=CONTENT_SHEET_ID, range=CONTENT_SHEET_RANGE).execute()
        values = result.get('values', [])
        if values and len(values) >= 2:
            content_data = {row[0]: {'en': row[1], 'ta': row[2]} for row in values[1:] if row and len(row) > 2 and row[0]}
            db.collection(CONTENT_FIRESTORE_COLLECTION).document(CONTENT_FIRESTORE_DOCUMENT).set(content_data)
            print(f"✅ Synced {len(content_data)} content keys.")
        else:
            print("⚠️ No data found for website content sync.")
    except Exception as e:
        logging.error(f"Error during content sync: {e}", exc_info=True)
        errors.append(f"Content sync failed: {str(e)}")

    # Sync Parking Data
    try:
        print("Syncing Parking Data...")
        result = sheets_service.spreadsheets().values().get(spreadsheetId=PARKING_SHEET_ID, range=PARKING_SHEET_RANGE).execute()
        values = result.get('values', [])
        if values and len(values) >= 2:
            headers = [_sanitize_header(h) for h in values[0]]
            batch = db.batch()
            count = 0
            for row in values[1:]:
                if not any(row): continue
                row_dict = dict(zip(headers, row + [''] * (len(headers) - len(row))))
                doc_id = row_dict.get('parking_lot')
                if not doc_id: continue
                row_dict['user_for_this_function'] = str(row_dict.get('user_for_this_function')).upper() == 'TRUE'
                doc_ref = db.collection(PARKING_FIRESTORE_COLLECTION).document(doc_id)
                batch.set(doc_ref, row_dict)
                count += 1
            batch.commit()
            print(f"✅ Synced {count} parking documents.")
        else:
             print("⚠️ No data found for parking sync.")
    except Exception as e:
        logging.error(f"Error during parking sync: {e}", exc_info=True)
        errors.append(f"Parking sync failed: {str(e)}")
    
    if errors:
        return (f"Sync completed with errors: {', '.join(errors)}", 500)
    
    return ("Sync completed successfully", 200)