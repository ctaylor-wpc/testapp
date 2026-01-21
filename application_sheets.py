# application_sheets_manager.py
# Google Sheets integration for job fair applications

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# Configuration
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
SHEET_ID = "1QZ5gO5farg4E03dhaSINJljvn6qfocUgvHH4tjOSkIc"
WORKSHEET_NAME = "2026"

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
    
    IMPORTANT: Your Google Sheet needs these 50 columns (A-AX):
    1. First Name
    2. Last Name
    3. Email
    4. Phone
    5. Street Address
    6. City
    7. State
    8. Zip
    9. Interview Location
    10. Interview Date
    11. Interview Time
    12. Positions Applied For
    13. Hours Preferred
    14. Expected Payrate
    15. Why Applying
    16. Special Training/Skills
    17. Legally Entitled to Work
    18. Can Perform Physical Duties
    19. Drug Test Willing
    20. Background Check Willing
    21. Valid Drivers License
    22. Reliable Transportation
    23. Submission Timestamp
    24. Employer 1 Name
    25. Employer 1 Location
    26. Employer 1 Hire Date
    27. Employer 1 End Date
    28. Employer 1 Position
    29. Employer 1 Pay Rate
    30. Employer 1 Reason for Leaving
    31. Employer 2 Name
    32. Employer 2 Location
    33. Employer 2 Hire Date
    34. Employer 2 End Date
    35. Employer 2 Position
    36. Employer 2 Pay Rate
    37. Employer 2 Reason for Leaving
    38. Employer 3 Name
    39. Employer 3 Location
    40. Employer 3 Hire Date
    41. Employer 3 End Date
    42. Employer 3 Position
    43. Employer 3 Pay Rate
    44. Employer 3 Reason for Leaving
    45. College Name & City
    46. College Area of Study
    47. College Graduated
    48. College Completion Date
    49. High School Name & City
    50. High School Area of Study
    51. High School Graduated
    52. High School Completion Date
    53. Reference 1 Name
    54. Reference 1 Contact
    55. Reference 1 Relationship
    56. Reference 2 Name
    57. Reference 2 Contact
    58. Reference 2 Relationship
    59. Reference 3 Name
    60. Reference 3 Contact
    61. Reference 3 Relationship
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
        
        # Prepare row data (61 columns total)
        row_data = [
            # Columns 1-8: Basic info
            data.get('first_name', ''),
            data.get('last_name', ''),
            data.get('email', ''),
            data.get('phone', ''),
            data.get('street_address', ''),
            data.get('city', ''),
            data.get('state', ''),
            data.get('zip', ''),
            
            # Columns 9-11: Interview schedule
            data.get('location', ''),
            data.get('date', ''),
            data.get('time_slot', ''),
            
            # Columns 12-16: Position info
            format_positions_for_sheet(data.get('positions', {})),
            format_hours_for_sheet(data),
            data.get('expected_payrate', ''),
            data.get('why_applying', ''),
            data.get('special_training', ''),
            
            # Columns 17-23: Legal info
            data.get('legally_entitled', ''),
            data.get('perform_duties', ''),
            data.get('drug_test', ''),
            data.get('background_check', ''),
            data.get('drivers_license', ''),
            data.get('reliable_transport', ''),
            data.get('submission_timestamp', ''),
        ]
        
        # Columns 24-44: Add employer data (3 employers x 7 fields)
        row_data.extend(employer_data)
        
        # Columns 45-52: Education
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
        
        # Columns 53-61: Add reference data (3 references x 3 fields)
        row_data.extend(reference_data)
        
        # Append row to sheet
        worksheet.append_row(row_data, value_input_option='USER_ENTERED')
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send to Google Sheet: {e}")
        return False
