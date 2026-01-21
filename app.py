# app.py
# Main application file for Job Fair Registration

import streamlit as st
import datetime
from application import render_application_form
from application_scheduling import render_scheduling_section, get_schedule_data
from application_sheets_manager import send_application_to_sheet
from application_pdf_generator import generate_application_pdf
from application_notifications import send_application_notification, send_confirmation_email

st.set_page_config(page_title="Wilson Plant Co. + Sage Garden Cafe Job Fair", layout="centered")

# Custom CSS for mobile-friendly layout
st.markdown("""
<style>
    /* Force single column layout */
    .stTextInput, .stTextArea, .stSelectbox, .stRadio, .stCheckbox {
        margin-bottom: 1rem;
    }
    
    /* Improve form field styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-size: 16px !important;
    }
    
    /* Make headers more consistent */
    h1, h2, h3 {
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_app():
    """Initialize the Streamlit app with session state variables"""
    if 'phase' not in st.session_state:
        st.session_state.phase = 1
    if 'basic_info' not in st.session_state:
        st.session_state.basic_info = {}
    if 'schedule_data' not in st.session_state:
        st.session_state.schedule_data = {}
    if 'application_data' not in st.session_state:
        st.session_state.application_data = {}

def reset_app():
    """Reset all session state"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_app()

def main():
    initialize_app()
    
    # Header
    st.title("Wilson Plant Co. + Sage Garden Cafe Job Fair")
    
    st.markdown("""
    Apply to begin a challenging and rewarding career path in the horticulture, retail, and hospitality industries. 
    Interview for a full or part-time, seasonal or year-round position with Wilson Plant Co, Sage Garden Café, 
    or our landscaping & production teams.
    """)
    
    st.markdown("---")
    
    # Phase 1: Basic Info and Scheduling
    if st.session_state.phase == 1:
        st.header("Register for the Job Fair")
        
        # Basic contact information - mobile-friendly single column
        first_name = st.text_input("First Name *", value=st.session_state.basic_info.get('first_name', ''))
        last_name = st.text_input("Last Name *", value=st.session_state.basic_info.get('last_name', ''))
        email = st.text_input("Email Address *", value=st.session_state.basic_info.get('email', ''))
        
        st.markdown("---")
        
        # Scheduling section
        st.header("Schedule Your Job Fair Interview")
        st.markdown("""
        The job fair is an opportunity for you to meet with several members of our team all on one day in one trip. 
        We provide multiple days and interview at both locations so please choose whatever day & location is most 
        convenient for you. Please note, while we do our best to stick to the schedule, some of our best candidates 
        have found themselves here for around two hours.
        """)
        
        schedule_data = render_scheduling_section()
        
        if st.button("Continue to Application", type="primary", use_container_width=True):
            if not all([first_name, last_name, email]):
                st.error("Please fill in all required fields (First Name, Last Name, Email)")
            elif not schedule_data:
                st.error("Please select a time slot for your interview")
            else:
                st.session_state.basic_info = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email
                }
                st.session_state.schedule_data = schedule_data
                st.session_state.phase = 2
                st.rerun()
    
    # Phase 2: Application for Employment
    elif st.session_state.phase == 2:
        st.header("Application for Employment")
        
        if st.button("← Back to Registration"):
            st.session_state.phase = 1
            st.rerun()
        
        st.markdown("---")
        
        # Render the application form with pre-filled basic info
        application_data = render_application_form(
            st.session_state.basic_info.get('first_name', ''),
            st.session_state.basic_info.get('last_name', ''),
            st.session_state.basic_info.get('email', '')
        )
        
        if application_data:
            st.session_state.application_data = application_data
            st.session_state.phase = 3
            st.rerun()
    
    # Phase 3: Confirmation and Submission
    elif st.session_state.phase == 3:
        st.header("Application Submitted Successfully!")
        st.success("Thank you for applying to our job fair!")
        
        # Process the application
        try:
            # Combine all data
            full_data = {
                **st.session_state.basic_info,
                **st.session_state.schedule_data,
                **st.session_state.application_data
            }
            
            # Generate PDF
            pdf_buffer = generate_application_pdf(full_data)
            
            # Upload PDF to Google Drive and get link
            from application_sheets_manager import upload_pdf_to_drive
            pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
            pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename) if pdf_buffer else ""
            
            # Add PDF link to data
            full_data['pdf_link'] = pdf_link
            
            # Send to Google Sheets
            sheet_success = send_application_to_sheet(full_data)
            
            # Send email notification to company
            if pdf_buffer and sheet_success:
                pdf_buffer.seek(0)  # Reset buffer
                email_success = send_application_notification(full_data, pdf_buffer)
                
                # Send confirmation email to applicant
                pdf_buffer.seek(0)  # Reset buffer again
                confirmation_success = send_confirmation_email(full_data)
                
                if email_success and confirmation_success:
                    st.success("Your application has been submitted and you will receive a confirmation email shortly.")
                else:
                    st.warning("Application saved, but confirmation email could not be sent.")
            
            # Offer PDF download
            if pdf_buffer:
                pdf_buffer.seek(0)
                st.download_button(
                    label="📥 Download Your Application",
                    data=pdf_buffer,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            
            # Show confirmation details
            st.markdown("### Your Interview Details:")
            st.write(f"**Location:** {full_data.get('location', 'N/A')}")
            st.write(f"**Date:** {full_data.get('date', 'N/A')}")
            st.write(f"**Time:** {full_data.get('time_slot', 'N/A')}")
            
            st.markdown("---")
            
            if st.button("Submit Another Application", use_container_width=True):
                reset_app()
                st.rerun()
                
        except Exception as e:
            st.error(f"An error occurred while processing your application: {e}")
            st.write("Please contact us directly at info@wilsonnurseriesky.com")

if __name__ == "__main__":
    main()
