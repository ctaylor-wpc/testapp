# application_sheets_manager.py
# Google Sheets integration for job fair applications

import streamlit as st
from config_secrets import get_gcp_service_account, get_sheet_config

# Get config from centralized secrets
_sheet_config = get_sheet_config()
SHEET_ID = _sheet_config['sheet_id']
WORKSHEET_NAME = _sheet_config['worksheet_name']
PDF_FOLDER_ID = _sheet_config['pdf_folder_id']

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


@st.cache_resource
def get_gspread_client():
    """Create and return authenticated gspread client. Cached for performance."""
    # Lazy import - only load when needed
    import gspread
    from google.oauth2.service_account import Credentials
    
    sa_info = get_gcp_service_account()
    if not sa_info:
        raise KeyError("Service account JSON not found in secrets")
    
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource
def get_drive_service():
    """Create and return Google Drive service. Cached for performance."""
    # Lazy import - only load when needed
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    
    sa_info = get_gcp_service_account()
    if not sa_info:
        raise KeyError("Service account JSON not found in secrets")
    
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    service = build("drive", "v3", credentials=creds)
    return service


def upload_pdf_to_drive(pdf_buffer, filename):
    """
    Upload PDF to Google Drive shared folder
    
    Args:
        pdf_buffer: BytesIO buffer containing the PDF
        filename: Name for the PDF file
    
    Returns:
        str: URL to the uploaded file, or empty string if failed
    """
    try:
        # Lazy import
        from googleapiclient.http import MediaIoBaseUpload
        
        service = get_drive_service()
        
        file_metadata = {
            "name": filename,
            "parents": [PDF_FOLDER_ID]
        }
        
        pdf_buffer.seek(0)
        media = MediaIoBaseUpload(pdf_buffer, mimetype="application/pdf", resumable=True)
        
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
            supportsAllDrives=True  # Important for Shared Drives
        ).execute()
        
        file_id = uploaded_file.get("id")
        return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
        
    except Exception as e:
        st.error(f"Failed to upload PDF to Google Drive: {e}")
        return ""


def format_positions_for_sheet(positions):
    """Format positions dictionary for sheet"""
    position_list = []
    
    if positions.get('wpc_cashier'): position_list.append("WPC-Cashier")
    if positions.get('wpc_greenhouse'): position_list.append("WPC-Greenhouse")
    if positions.get('wpc_nursery'): position_list.append("WPC-Nursery")
    if positions.get('wpc_waterer'): position_list.append("WPC-Waterer/Production")
    if positions.get('wpc_admin'): position_list.append("WPC-Administration")
    if positions.get('land_designer'): position_list.append("Landscaping-Designer")
    if positions.get('land_foreman'): position_list.append("Landscaping-Foreman")
    if positions.get('land_installer'): position_list.append("Landscaping-Installer")
    if positions.get('cafe_foh'): position_list.append("Cafe-FOH")
    if positions.get('cafe_boh'): position_list.append("Cafe-BOH")
    if positions.get('cafe_admin'): position_list.append("Cafe-Admin")
    if positions.get('other'):
        other_desc = positions.get('other_description', 'Not specified')
        position_list.append(f"Other: {other_desc}")
    
    return ", ".join(position_list)


def format_hours_for_sheet(data):
    """Format hours preference for sheet"""
    hours = []
    if data.get('hours_15_25'): hours.append("15-25")
    if data.get('hours_30_40'): hours.append("30-40")
    if data.get('hours_40_plus'): hours.append("40+")
    return ", ".join(hours)


def send_application_to_sheet(data):
    """
    Send application data to Google Sheet
    """
    try:
        client = get_gspread_client()
        workbook = client.open_by_key(SHEET_ID)
        worksheet = workbook.worksheet(WORKSHEET_NAME)
        
        # Prepare employer data (up to 3 employers)
        employers = data.get('employers', [])
        employer_data = []
        for i in range(3):
            if i < len(employers):
                emp = employers[i]
                employer_data.extend([
                    emp.get('employer', ''),
                    emp.get('location', ''),
                    emp.get('hire_date', ''),
                    emp.get('end_date', ''),
                    emp.get('position', ''),
                    emp.get('pay_rate', ''),
                    emp.get('reason', '')
                ])
            else:
                employer_data.extend(['', '', '', '', '', '', ''])
        
        # Prepare reference data (up to 3 references)
        references = data.get('references', [])
        reference_data = []
        for i in range(3):
            if i < len(references):
                ref = references[i]
                reference_data.extend([
                    ref.get('name', ''),
                    ref.get('contact', ''),
                    ref.get('relationship', '')
                ])
            else:
                reference_data.extend(['', '', ''])
        
        # Prepare row data (66 columns total)
        row_data = [
            # Columns 1-10: Basic info
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('alternate_phone', ''),
            data.get('dob', ''),
            data.get('street_address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('zip', ''),
            
            # Columns 11-13: Interview schedule
            data.get('location', ''),
            data.get('date', ''),
            data.get('time_slot', ''),
            
            # Columns 14-20: Position and availability info
            format_positions_for_sheet(data.get('positions', {})),
            format_hours_for_sheet(data),
            data.get('expected_payrate', ''),
            data.get('availability_restrictions', ''),
            data.get('start_date', ''),
            data.get('why_applying', ''),
            data.get('special_training', ''),
            
            # Columns 21-27: Legal info
            data.get('legally_entitled', ''),
            data.get('perform_duties', ''),
            data.get('drug_test', ''),
            data.get('background_check', ''),
            data.get('drivers_license', ''),
            data.get('reliable_transport', ''),
            data.get('submission_timestamp', ''),
        ]
        
        # Columns 28-48: Add employer data (3 employers x 7 fields)
        row_data.extend(employer_data)
        
        # Columns 49-56: Education
        row_data.extend([
            data.get('college_name', ''),
            data.get('college_study', ''),
            data.get('college_graduated', ''),
            data.get('college_completion', ''),
            data.get('hs_name', ''),
            data.get('hs_study', ''),
            data.get('hs_graduated', ''),
            data.get('hs_completion', '')
        ])
        
        # Columns 57-65: Add reference data (3 references x 3 fields)
        row_data.extend(reference_data)
        
        # Column 66: PDF Link
        row_data.append(data.get('pdf_link', ''))
        
        # Append row to sheet
        worksheet.append_row(row_data, value_input_option='USER_ENTERED')
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send to Google Sheet: {e}")
        return False