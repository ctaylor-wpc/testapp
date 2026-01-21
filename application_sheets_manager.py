# application_sheets_manager.py
# Google Sheets integration for job fair applications

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_ID = "1QZ5gO5farg4E03dhaSINJljvn6qfocUgvHH4tjOSkIc"
WORKSHEET_NAME = "2026"
PDF_FOLDER_ID = "1X5crtAwvuIgmgrGOSUR9M1gq21e0oUwh"  # Shared Drive folder

def get_service_account_info_from_secrets():
    """Get service account info from Streamlit secrets"""
    sa = st.secrets.get("gcp", {}).get("service_account_json")
    if not sa:
        raise KeyError("Service account JSON not found: check st.secrets['gcp']['service_account_json']")
    if isinstance(sa, str):
        return json.loads(sa)
    return sa

def get_gspread_client():
    """Create and return authenticated gspread client"""
    sa_info = get_service_account_info_from_secrets()
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)

def get_drive_service():
    """Create and return Google Drive service"""
    sa_info = get_service_account_info_from_secrets()
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
    
    IMPORTANT: Your Google Sheet needs these 65 columns (A-BM):
    1. First Name
    2. Last Name
    3. Email
    4. Phone
    5. Alternate Phone
    6. Date of Birth
    7. Street Address
    8. City
    9. State
    10. Zip
    11. Interview Location
    12. Interview Date
    13. Interview Time
    14. Positions Applied For
    15. Hours Preferred
    16. Expected Payrate
    17. Availability Restrictions
    18. Available to Start
    19. Why Applying
    20. Special Training/Skills
    21. Legally Entitled to Work
    22. Can Perform Physical Duties
    23. Drug Test Willing
    24. Background Check Willing
    25. Valid Drivers License
    26. Reliable Transportation
    27. Submission Timestamp
    28. Employer 1 Name
    29. Employer 1 Location
    30. Employer 1 Hire Date
    31. Employer 1 End Date
    32. Employer 1 Position
    33. Employer 1 Pay Rate
    34. Employer 1 Reason for Leaving
    35. Employer 2 Name
    36. Employer 2 Location
    37. Employer 2 Hire Date
    38. Employer 2 End Date
    39. Employer 2 Position
    40. Employer 2 Pay Rate
    41. Employer 2 Reason for Leaving
    42. Employer 3 Name
    43. Employer 3 Location
    44. Employer 3 Hire Date
    45. Employer 3 End Date
    46. Employer 3 Position
    47. Employer 3 Pay Rate
    48. Employer 3 Reason for Leaving
    49. College Name & City
    50. College Area of Study
    51. College Graduated
    52. College Completion Date
    53. High School Name & City
    54. High School Area of Study
    55. High School Graduated
    56. High School Completion Date
    57. Reference 1 Name
    58. Reference 1 Contact
    59. Reference 1 Relationship
    60. Reference 2 Name
    61. Reference 2 Contact
    62. Reference 2 Relationship
    63. Reference 3 Name
    64. Reference 3 Contact
    65. Reference 3 Relationship
    66. PDF Link
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
