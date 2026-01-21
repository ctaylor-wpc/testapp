# application_notifications.py
# Email notification system for job fair applications

import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Email configuration from secrets
def get_email_config():
    """Get email configuration from Streamlit secrets"""
    return {
        'smtp_server': st.secrets["email"]["smtp_server"],
        'smtp_port': st.secrets["email"]["smtp_port"],
        'sender_email': st.secrets["email"]["sender_email"],
        'sender_password': st.secrets["email"]["sender_password"],
        'company_email': 'info@wilsonnurseriesky.com'  # Company notification email
    }

def format_positions_email(positions):
    """Format positions for email display"""
    position_list = []
    
    # Wilson Plant Co
    wpc = []
    if positions.get('wpc_cashier'): wpc.append("Cashier")
    if positions.get('wpc_greenhouse'): wpc.append("Greenhouse")
    if positions.get('wpc_nursery'): wpc.append("Nursery")
    if positions.get('wpc_waterer'): wpc.append("Waterer/Production")
    if positions.get('wpc_admin'): wpc.append("Administration")
    if wpc:
        position_list.append("Wilson Plant Co: " + ", ".join(wpc))
    
    # Landscaping
    land = []
    if positions.get('land_designer'): land.append("Designer")
    if positions.get('land_foreman'): land.append("Foreman")
    if positions.get('land_installer'): land.append("Installer")
    if land:
        position_list.append("Landscaping: " + ", ".join(land))
    
    # Cafe
    cafe = []
    if positions.get('cafe_foh'): cafe.append("Front-of-house")
    if positions.get('cafe_boh'): cafe.append("Back-of-house")
    if positions.get('cafe_admin'): cafe.append("Administration")
    if cafe:
        position_list.append("Sage Garden Cafe: " + ", ".join(cafe))
    
    # Other
    if positions.get('other'):
        other_desc = positions.get('other_description', 'Not specified')
        position_list.append(f"Other: {other_desc}")
    
    return "\n".join(position_list) if position_list else "Not specified"

def format_hours_email(data):
    """Format hours preference for email"""
    hours = []
    if data.get('hours_15_25'): hours.append("15-25")
    if data.get('hours_30_40'): hours.append("30-40")
    if data.get('hours_40_plus'): hours.append("40+")
    return ", ".join(hours) if hours else "Not specified"

def format_employers_email(employers):
    """Format employment history for email"""
    if not employers or not any(emp.get('employer') for emp in employers):
        return "Not provided"
    
    emp_text = []
    for i, emp in enumerate(employers):
        if emp.get('employer'):
            emp_text.append(f"""
Employer {i+1}:
  Name: {emp.get('employer', 'N/A')}
  Location: {emp.get('location', 'N/A')}
  Dates: {emp.get('hire_date', 'N/A')} to {emp.get('end_date', 'N/A')}
  Position: {emp.get('position', 'N/A')}
  Pay Rate: {emp.get('pay_rate', 'N/A')}
  Reason for Leaving: {emp.get('reason', 'N/A')}
""")
    return "\n".join(emp_text)

def format_references_email(references):
    """Format references for email"""
    if not references or not any(ref.get('name') for ref in references):
        return "Not provided"
    
    ref_text = []
    for i, ref in enumerate(references):
        if ref.get('name'):
            ref_text.append(f"""
Reference {i+1}:
  Name: {ref.get('name', 'N/A')}
  Contact: {ref.get('contact', 'N/A')}
  Relationship: {ref.get('relationship', 'N/A')}
""")
    return "\n".join(ref_text)

def create_company_email_body(data):
    """Create the email body text for company notification"""
    email_body = f"""
NEW JOB FAIR APPLICATION RECEIVED
=====================================

APPLICANT INFORMATION:
Name: {data.get('first_name', '')} {data.get('last_name', '')}
Email: {data.get('email', '')}
Phone: {data.get('phone', '')}
Alternate Phone: {data.get('alternate_phone', 'Not provided')}
Date of Birth: {data.get('dob', 'Not provided')}
Address: {data.get('street_address', '')}, {data.get('city', '')}, {data.get('state', '')} {data.get('zip', '')}

INTERVIEW SCHEDULE:
Location: {data.get('location', 'N/A')}
Date: {data.get('date', 'N/A')}
Time: {data.get('time_slot', 'N/A')}

POSITION INFORMATION:
Positions Applied For:
{format_positions_email(data.get('positions', {}))}

Hours Preferred: {format_hours_email(data)}
Expected Payrate: {data.get('expected_payrate', 'Not specified')}

AVAILABILITY:
Restrictions: {data.get('availability_restrictions', 'None')}
Available to Start: {data.get('start_date', 'Not specified')}

WHY APPLYING:
{data.get('why_applying', 'Not provided')}

SPECIAL TRAINING/SKILLS:
{data.get('special_training', 'Not provided')}

LEGAL INFORMATION:
Legally entitled to work in U.S.: {data.get('legally_entitled', 'N/A')}
Can perform physical duties: {data.get('perform_duties', 'N/A')}
Willing to submit to drug test: {data.get('drug_test', 'N/A')}
Willing to submit to background check: {data.get('background_check', 'N/A')}
Valid driver's license: {data.get('drivers_license', 'N/A')}
Reliable transportation: {data.get('reliable_transport', 'N/A')}

EMPLOYMENT HISTORY:
{format_employers_email(data.get('employers', []))}

EDUCATION:
College: {data.get('college_name', 'N/A')}
  Area of Study: {data.get('college_study', 'N/A')}
  Graduated: {data.get('college_graduated', 'N/A')}
  Completion Date: {data.get('college_completion', 'N/A')}

High School: {data.get('hs_name', 'N/A')}
  Area of Study: {data.get('hs_study', 'N/A')}
  Graduated: {data.get('hs_graduated', 'N/A')}
  Completion Date: {data.get('hs_completion', 'N/A')}

REFERENCES:
{format_references_email(data.get('references', []))}

SUBMISSION DETAILS:
Submitted: {data.get('submission_timestamp', 'N/A')}

=====================================
Application PDF is attached.
"""
    return email_body

def create_confirmation_email_body(data):
    """Create the confirmation email body for the applicant"""
    first_name = data.get('first_name', '')
    date = data.get('date', '')
    time = data.get('time_slot', '')
    location = data.get('location', '')
    address = data.get('address', '')
    
    email_body = f"""{first_name}, thanks for applying & signing up for our job fair. We look forward to meeting you at {date}, {time}. 

As a reminder, your interview will be at our {location} store which is at {address}. When you arrive, head straight in and sign in at the register.

Thanks again for your interest & time,

-Chris Taylor
Wilson Plant Co. + Sage Garden Cafe
"""
    return email_body

def send_application_notification(data, pdf_buffer):
    """
    Send email notification to company with application data and PDF attachment
    
    Args:
        data: Dictionary containing all application data
        pdf_buffer: BytesIO buffer containing the generated PDF
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        config = get_email_config()
        
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = config['sender_email']
        msg["To"] = config['company_email']  # Send to company
        msg["Subject"] = f"Job Fair Application: {data.get('first_name', '')} {data.get('last_name', '')}"
        
        # Add email body
        email_body = create_company_email_body(data)
        msg.attach(MIMEText(email_body, "plain"))
        
        # Add PDF attachment
        if pdf_buffer:
            pdf_buffer.seek(0)
            pdf_filename = f"Application_{data.get('last_name', '')}_{data.get('first_name', '')}.pdf"
            part = MIMEApplication(pdf_buffer.read(), Name=pdf_filename)
            part['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            msg.attach(part)
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.sendmail(config['sender_email'], config['company_email'], msg.as_string())
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send notification email to company: {e}")
        return False

def send_confirmation_email(data):
    """
    Send confirmation email to the applicant
    
    Args:
        data: Dictionary containing all application data
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        config = get_email_config()
        
        # Create email message
        msg = MIMEMultipart()
        msg["From"] = config['sender_email']
        msg["To"] = data.get('email', '')  # Send to applicant
        msg["Subject"] = "Job Fair Interview Confirmation - Wilson Plant Co. + Sage Garden Cafe"
        
        # Add email body
        email_body = create_confirmation_email_body(data)
        msg.attach(MIMEText(email_body, "plain"))
        
        # Send email
        with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
            server.starttls()
            server.login(config['sender_email'], config['sender_password'])
            server.sendmail(config['sender_email'], data.get('email', ''), msg.as_string())
        
        return True
        
    except Exception as e:
        st.error(f"Failed to send confirmation email to applicant: {e}")
        return False
