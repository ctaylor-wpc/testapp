# sheets_manager.py Version 4
# Google Sheets integration for dashboard and state management

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime
import json
from config import SCOPES, SHEET_ID


def get_service_account_info_from_secrets():
    """
    Reads service account JSON stored in st.secrets["gcp"]["service_account_json"].
    Handles either a dict or a JSON string (escaped newlines etc).
    """
    sa = st.secrets.get("gcp", {}).get("service_account_json")
    if not sa:
        raise KeyError("Service account JSON not found: check st.secrets['gcp']['service_account_json']")
    if isinstance(sa, str):
        return json.loads(sa)
    return sa


def get_gspread_client():
    """Get authenticated gspread client"""
    sa_info = get_service_account_info_from_secrets()
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


def send_to_dashboard(customer_data, installation_data, pricing_data, plants_data, pdf_link, install_id=None):
    """
    Send installation data to Google Sheet dashboard.
    If install_id is provided, update existing row. Otherwise, append new row.
    Returns the install_id (generated or existing).
    """
    try:
        client = get_gspread_client()
        sheet = client.open_by_key(SHEET_ID).sheet1
        
        # Prepare row data
        customer_name = customer_data.get("customer_name", "")
        address = f"{installation_data.get('customer_street_address','')}, {installation_data.get('customer_city','')}, KY {installation_data.get('customer_zip','')}".strip().strip(",")
        phone = customer_data.get("customer_phone", "")
        total_amount = pricing_data.get("final_total", 0.0)
        sold_on = datetime.date.today().strftime("%m/%d/%Y")
        customer_subdivision = customer_data.get("customer_subdivision", "")
        customer_cross_street = customer_data.get("customer_cross_street", "")
        install_location = customer_data.get("install_location", "")
        notes = customer_data.get("notes", "")
        employee_initials = customer_data.get("employee_initials", "")
        origin_location = installation_data.get("origin_location", "")
        
        # Generate install_id if not provided
        if not install_id:
            import random
            install_id = str(random.randint(100000, 999999))
        
        row_data = [
            customer_name,              # A Customer Name
            address,                    # B Address
            phone,                      # C Phone Number
            f"${total_amount:.2f}",     # D Total Amount
            "Sold",                     # E Current Status
            "",                         # F Notes
            sold_on,                    # G Sold On
            "",                         # H BUD Called On
            "",                         # I BUD Notes
            "",                         # J BUD Clear On
            "",                         # K Scheduled For
            "",                         # L Completed
            pdf_link,                   # M PDF File
            customer_subdivision,       # N Subdivision (hidden)
            customer_cross_street,      # O Cross Street (hidden)
            install_location,           # P Install Location (hidden)
            employee_initials,          # Q Employee Initials (hidden)
            origin_location,            # R Origin Location (hidden)
            install_id                  # S Install ID (hidden)
        ]
        
        # Check if install_id exists and update, otherwise append
        if install_id:
            # Try to find existing row with this install_id
            try:
                cell = sheet.find(install_id, in_column=19)  # Column S
                if cell:
                    # Update existing row
                    sheet.update(f'A{cell.row}:S{cell.row}', [row_data], value_input_option='USER_ENTERED')
                    return install_id
            except:
                pass  # Not found, will append
        
        # Append new row
        sheet.append_row(row_data, value_input_option='USER_ENTERED')
        
        return install_id
        
    except Exception as e:
        st.error(f"Failed to send to Google Sheet: {e}")
        return None


def save_install_state(install_id, plants_data, installation_data, customer_data, pricing_data):
    """
    Save complete install state to a separate tab in the Google Sheet.
    This allows loading and editing existing installs.
    If install_id already exists, it UPDATES that row instead of creating a new one.
    """
    try:
        client = get_gspread_client()
        workbook = client.open_by_key(SHEET_ID)
        
        # Try to get or create "Install States" tab
        try:
            state_sheet = workbook.worksheet("Install States")
        except:
            state_sheet = workbook.add_worksheet(title="Install States", rows=1000, cols=20)
            # Add headers
            headers = ["Install ID", "Customer Name", "Date Saved", "Plants Data", "Installation Data", "Customer Data", "Pricing Data"]
            state_sheet.append_row(headers)
        
        # Serialize data as JSON
        plants_json = json.dumps(plants_data)
        installation_json = json.dumps(installation_data)
        customer_json = json.dumps(customer_data)
        pricing_json = json.dumps(pricing_data)
        
        date_saved = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        customer_name = customer_data.get("customer_name", "")
        
        row_data = [
            install_id,
            customer_name,
            date_saved,
            plants_json,
            installation_json,
            customer_json,
            pricing_json
        ]
        
        # Get all values from column A (Install IDs) to find if this ID exists
        all_install_ids = state_sheet.col_values(1)
        
        # Check if install_id exists (skip header row)
        row_to_update = None
        for i, cell_value in enumerate(all_install_ids):
            if i == 0:  # Skip header
                continue
            if str(cell_value) == str(install_id):
                row_to_update = i + 1  # +1 because row numbers are 1-indexed
                break
        
        if row_to_update:
            # Update existing row by overwriting each cell
            state_sheet.update(f'A{row_to_update}:G{row_to_update}', [row_data], value_input_option='USER_ENTERED')
            return True
        else:
            # Append new row if install_id doesn't exist
            state_sheet.append_row(row_data, value_input_option='USER_ENTERED')
            return True
        
    except Exception as e:
        st.error(f"Failed to save install state: {e}")
        return False


def load_install_states():
    """
    Load all saved install states from Google Sheet.
    Returns a list of dictionaries with install data.
    """
    try:
        client = get_gspread_client()
        workbook = client.open_by_key(SHEET_ID)
        
        try:
            state_sheet = workbook.worksheet("Install States")
        except:
            return []  # Tab doesn't exist yet
        
        # Get all records (skip header row)
        records = state_sheet.get_all_records()
        
        installs = []
        for record in records:
            try:
                installs.append({
                    'install_id': record.get('Install ID', ''),
                    'customer_name': record.get('Customer Name', ''),
                    'date_saved': record.get('Date Saved', ''),
                    'plants_data': json.loads(record.get('Plants Data', '{}')),
                    'installation_data': json.loads(record.get('Installation Data', '{}')),
                    'customer_data': json.loads(record.get('Customer Data', '{}')),
                    'pricing_data': json.loads(record.get('Pricing Data', '{}'))
                })
            except json.JSONDecodeError:
                continue  # Skip invalid records
        
        return installs
        
    except Exception as e:
        st.error(f"Failed to load install states: {e}")
        return []


def get_install_by_id(install_id):
    """Load a specific install by ID"""
    installs = load_install_states()
    for install in installs:
        if install['install_id'] == install_id:
            return install
    return None
