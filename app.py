# app.py
# Main application file for Job Fair Registration

import os
import streamlit as st
import datetime
import traceback

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
    print("=== INITIALIZING APP ===")
    if 'phase' not in st.session_state:
        st.session_state.phase = 1
    if 'basic_info' not in st.session_state:
        st.session_state.basic_info = {}
    if 'schedule_data' not in st.session_state:
        st.session_state.schedule_data = {}
    if 'application_data' not in st.session_state:
        st.session_state.application_data = {}
    if 'submission_complete' not in st.session_state:
        st.session_state.submission_complete = False
    if 'pdf_buffer' not in st.session_state:
        st.session_state.pdf_buffer = None
    if 'pdf_filename' not in st.session_state:
        st.session_state.pdf_filename = None
    if 'full_data' not in st.session_state:
        st.session_state.full_data = None
    if 'submission_status' not in st.session_state:
        st.session_state.submission_status = {}
    print(f"Phase: {st.session_state.phase}")

def reset_app():
    """Reset all session state"""
    print("=== RESETTING APP ===")
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
        print("=== RENDERING PHASE 1: REGISTRATION ===")
        # Lazy import - only load when needed
        from application_scheduling import render_scheduling_section
        
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
            print(f"=== CONTINUE BUTTON CLICKED ===")
            print(f"First: {first_name}, Last: {last_name}, Email: {email}")
            print(f"Schedule: {schedule_data}")
            
            if not all([first_name, last_name, email]):
                print("ERROR: Missing required fields")
                st.error("Please fill in all required fields (First Name, Last Name, Email)")
            elif not schedule_data:
                print("ERROR: No schedule selected")
                st.error("Please select a time slot for your interview")
            else:
                st.session_state.basic_info = {
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email
                }
                st.session_state.schedule_data = schedule_data
                st.session_state.phase = 2
                print("=== ADVANCING TO PHASE 2 ===")
                st.rerun()
    
    # Phase 2: Application for Employment
    elif st.session_state.phase == 2:
        print("=== RENDERING PHASE 2: APPLICATION FORM ===")
        # Lazy import - only load when needed
        from application import render_application_form
        
        st.header("Application for Employment")
        
        if st.button("← Back to Registration"):
            print("=== BACK BUTTON CLICKED - RETURNING TO PHASE 1 ===")
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
            print("=== APPLICATION FORM SUBMITTED ===")
            print(f"Application data keys: {application_data.keys()}")
            st.session_state.application_data = application_data
            st.session_state.phase = 3
            st.rerun()
    
    # Phase 3: Confirmation and Submission
    elif st.session_state.phase == 3:
        print("=== RENDERING PHASE 3: SUBMISSION ===")
        st.header("Application Submitted Successfully!")
        st.success("Thank you for applying to our job fair!")
        
        # Only process if not already submitted
        if not st.session_state.submission_complete:
            print("=== STARTING SUBMISSION PROCESS ===")
            
            # Store data FIRST before attempting anything
            full_data = {
                **st.session_state.basic_info,
                **st.session_state.schedule_data,
                **st.session_state.application_data
            }
            st.session_state.full_data = full_data
            
            print(f"Applicant: {full_data.get('first_name')} {full_data.get('last_name')}")
            print(f"Email: {full_data.get('email')}")
            print(f"Interview: {full_data.get('date')} at {full_data.get('time_slot')}")
            
            # Lazy imports - only load heavy libraries when actually submitting
            from application_sheets_manager import send_application_to_sheet, upload_pdf_to_drive
            from application_pdf_generator import generate_application_pdf
            from application_notifications import send_application_notification, send_confirmation_email
            
            # Initialize status tracking
            status = {
                'sheets': False,
                'pdf': False,
                'drive': False,
                'company_email': False,
                'confirmation_email': False
            }
            
            # Show progress indicator
            with st.spinner("Processing your application..."):
                # STEP 1: Save to Google Sheets FIRST (most important)
                try:
                    print("STEP 1: Saving to Google Sheets...")
                    status['sheets'] = send_application_to_sheet(full_data)
                    if status['sheets']:
                        print("✓ Google Sheets: SUCCESS")
                    else:
                        print("✗ Google Sheets: FAILED")
                except Exception as e:
                    print(f"✗ Google Sheets: EXCEPTION - {e}")
                    print(traceback.format_exc())
                    status['sheets'] = False
                
                # STEP 2: Generate PDF (non-critical)
                pdf_buffer = None
                try:
                    print("STEP 2: Generating PDF...")
                    pdf_buffer = generate_application_pdf(full_data)
                    if pdf_buffer:
                        print("✓ PDF Generation: SUCCESS")
                        status['pdf'] = True
                    else:
                        print("✗ PDF Generation: FAILED (returned None)")
                        status['pdf'] = False
                except Exception as e:
                    print(f"✗ PDF Generation: EXCEPTION - {e}")
                    print(traceback.format_exc())
                    status['pdf'] = False
                    pdf_buffer = None
                
                # STEP 3: Upload PDF to Drive (if PDF exists)
                pdf_link = ""
                if pdf_buffer:
                    try:
                        print("STEP 3: Uploading PDF to Google Drive...")
                        pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
                        pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename)
                        if pdf_link:
                            print(f"✓ Drive Upload: SUCCESS - {pdf_link}")
                            status['drive'] = True
                        else:
                            print("✗ Drive Upload: FAILED (returned empty string)")
                            status['drive'] = False
                    except Exception as e:
                        print(f"✗ Drive Upload: EXCEPTION - {e}")
                        print(traceback.format_exc())
                        status['drive'] = False
                        pdf_link = ""
                else:
                    print("STEP 3: SKIPPED - No PDF to upload")
                
                # Update data with PDF link if available
                full_data['pdf_link'] = pdf_link
                
                # Update sheet with PDF link if we got one but it wasn't in original submission
                if pdf_link and status['sheets']:
                    try:
                        print("Updating Google Sheet with PDF link...")
                        # This is a nice-to-have, don't fail if it doesn't work
                        # You could implement an update function here if needed
                    except:
                        pass
                
                # STEP 4: Send company notification email (if we have PDF)
                if pdf_buffer:
                    try:
                        print("STEP 4: Sending company notification email...")
                        pdf_buffer.seek(0)
                        status['company_email'] = send_application_notification(full_data, pdf_buffer)
                        if status['company_email']:
                            print("✓ Company Email: SUCCESS")
                        else:
                            print("✗ Company Email: FAILED")
                    except Exception as e:
                        print(f"✗ Company Email: EXCEPTION - {e}")
                        print(traceback.format_exc())
                        status['company_email'] = False
                else:
                    print("STEP 4: SKIPPED - No PDF to attach")
                
                # STEP 5: Send confirmation email to applicant
                try:
                    print("STEP 5: Sending confirmation email to applicant...")
                    status['confirmation_email'] = send_confirmation_email(full_data)
                    if status['confirmation_email']:
                        print("✓ Confirmation Email: SUCCESS")
                    else:
                        print("✗ Confirmation Email: FAILED")
                except Exception as e:
                    print(f"✗ Confirmation Email: EXCEPTION - {e}")
                    print(traceback.format_exc())
                    status['confirmation_email'] = False
                
                # Store results
                st.session_state.pdf_buffer = pdf_buffer
                st.session_state.pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
                st.session_state.submission_status = status
                st.session_state.submission_complete = True
                
                print("=== SUBMISSION SUMMARY ===")
                print(f"Google Sheets: {'✓' if status['sheets'] else '✗'}")
                print(f"PDF Generated: {'✓' if status['pdf'] else '✗'}")
                print(f"PDF Uploaded: {'✓' if status['drive'] else '✗'}")
                print(f"Company Email: {'✓' if status['company_email'] else '✗'}")
                print(f"Confirmation Email: {'✓' if status['confirmation_email'] else '✗'}")
            
            # Show user-friendly status messages
            if status['sheets']:
                st.success("✓ Your application has been saved")
            else:
                st.error("✗ Failed to save application - please contact us directly")
            
            if status['pdf']:
                st.success("✓ PDF generated successfully")
            else:
                st.warning("⚠ PDF could not be generated, but your application was saved")
            
            if status['confirmation_email']:
                st.success("✓ Confirmation email sent")
            else:
                st.warning("⚠ Confirmation email could not be sent")
        
        # Show download button (outside the submission block so it persists)
        if st.session_state.pdf_buffer:
            st.session_state.pdf_buffer.seek(0)
            st.download_button(
                label="📄 Download Your Application",
                data=st.session_state.pdf_buffer,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )
        
        # Show confirmation details
        if st.session_state.full_data:
            st.markdown("### Your Interview Details:")
            st.write(f"**Location:** {st.session_state.full_data.get('location', 'N/A')}")
            st.write(f"**Date:** {st.session_state.full_data.get('date', 'N/A')}")
            st.write(f"**Time:** {st.session_state.full_data.get('time_slot', 'N/A')}")
        
        st.markdown("---")
        
        if st.button("Submit Another Application", use_container_width=True):
            print("=== SUBMIT ANOTHER APPLICATION CLICKED ===")
            reset_app()
            st.rerun()

if __name__ == "__main__":
    main()