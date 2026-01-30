# app.py
# Main application file for Job Fair Registration
# NON-BLOCKING VERSION - Steps process with visible progress

import os
import streamlit as st
import datetime
import traceback
import uuid
import time

# Check maintenance mode FIRST
try:
    from maintenance import MAINTENANCE_MODE, MAINTENANCE_MESSAGE
    if MAINTENANCE_MODE:
        st.set_page_config(page_title="Under Maintenance", layout="centered")
        st.title("Wilson Plant Co. + Sage Garden Cafe")
        st.warning(MAINTENANCE_MESSAGE)
        st.info("💡 **Tip:** Refresh this page in a few minutes to try again.")
        st.stop()
except ImportError:
    pass

st.set_page_config(page_title="Wilson Plant Co. + Sage Garden Cafe Job Fair", layout="centered")

# Custom CSS
st.markdown("""
<style>
.stTextInput, .stTextArea, .stSelectbox, .stRadio, .stCheckbox {
    margin-bottom: 1rem;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    font-size: 16px !important;
}
h1, h2, h3 {
    margin-top: 1.5rem;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

def check_render_loop():
    """Detect and break infinite render loops"""
    if 'render_count' not in st.session_state:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()
    
    st.session_state.render_count += 1
    
    if st.session_state.render_count > 30 and (time.time() - st.session_state.render_start) < 5:
        print(f"INFINITE LOOP DETECTED: {st.session_state.render_count} renders")
        st.error("App error detected. Please refresh the page.")
        st.stop()
    
    if time.time() - st.session_state.render_start > 5:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()

def initialize_app():
    """Initialize session state"""
    if 'initialized' not in st.session_state:
        print("INITIALIZING NEW SESSION")
        st.session_state.initialized = True
        st.session_state.phase = 1
        st.session_state.basic_info = {}
        st.session_state.schedule_data = {}
        st.session_state.application_data = {}
        st.session_state.submission_id = None
        st.session_state.submitted = False
        st.session_state.processing_step = 0
        st.session_state.pdf_buffer = None
        st.session_state.pdf_filename = None
        st.session_state.full_data = None
        st.session_state.status = {}

def reset_app():
    """Complete reset"""
    print("RESETTING APP")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_app()

def generate_submission_id():
    """Generate unique ID"""
    sub_id = str(uuid.uuid4())[:8].upper()
    print(f"NEW SUBMISSION ID: {sub_id}")
    return sub_id

def main():
    check_render_loop()
    initialize_app()
    
    # TERMINAL STATE - Show completion page
    if st.session_state.get('submitted'):
        sub_id = st.session_state.submission_id
        print(f"TERMINAL STATE: ID {sub_id}")
        
        st.title("✅ Application Submitted!")
        st.success("Your application has been received.")
        
        if sub_id:
            st.info(f"**Reference ID:** {sub_id}")
        
        if st.session_state.full_data:
            data = st.session_state.full_data
            st.markdown("### Your Interview Details:")
            st.write(f"**Name:** {data.get('first_name')} {data.get('last_name')}")
            st.write(f"**Location:** {data.get('location', 'N/A')}")
            st.write(f"**Date:** {data.get('date', 'N/A')}")
            st.write(f"**Time:** {data.get('time_slot', 'N/A')}")
        
        status = st.session_state.status
        if status:
            st.markdown("### Submission Status:")
            if status.get('sheets'):
                st.write("✅ Application saved to database")
            if status.get('pdf'):
                st.write("✅ PDF generated")
            if status.get('confirmation_email'):
                st.write("✅ Confirmation email sent")
        
        if st.session_state.pdf_buffer:
            st.session_state.pdf_buffer.seek(0)
            st.download_button(
                label="📄 Download Your Application PDF",
                data=st.session_state.pdf_buffer,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )
        
        st.markdown("---")
        st.info("You may close this page. Check your email for confirmation.")
        
        if st.button("Submit Another Application", use_container_width=True):
            reset_app()
            st.rerun()
        
        st.stop()
    
    # PHASE 1: Registration
    if st.session_state.phase == 1:
        print(f"PHASE 1: Registration")
        from application_scheduling import render_scheduling_section
        
        st.title("Wilson Plant Co. + Sage Garden Cafe Job Fair")
        st.markdown("""
        Apply to begin a challenging and rewarding career path in the horticulture, retail, and hospitality industries.
        Interview for a full or part-time, seasonal or year-round position with Wilson Plant Co, Sage Garden Café,
        or our landscaping & production teams.
        """)
        st.markdown("---")
        
        st.header("Register for the Job Fair")
        
        first_name = st.text_input("First Name *", value=st.session_state.basic_info.get('first_name', ''))
        last_name = st.text_input("Last Name *", value=st.session_state.basic_info.get('last_name', ''))
        email = st.text_input("Email Address *", value=st.session_state.basic_info.get('email', ''))
        
        st.markdown("---")
        st.header("Schedule Your Job Fair Interview")
        st.markdown("""
        The job fair is an opportunity for you to meet with several members of our team all on one day in one trip.
        We provide multiple days and interview at both locations so please choose whatever day & location is most
        convenient for you. Please note, while we do our best to stick to the schedule, some of our best candidates
        have found themselves here for around two hours.
        """)
        
        schedule_data = render_scheduling_section()
        
        if st.button("Continue to Application", type="primary", use_container_width=True, key="phase1_continue"):
            print(f"Continue clicked: {first_name} {last_name} {email}")
            
            if not all([first_name.strip(), last_name.strip(), email.strip()]):
                print("Missing required fields")
                st.error("Please fill in all required fields (First Name, Last Name, Email)")
            elif not schedule_data:
                print("No schedule selected")
                st.error("Please select a time slot for your interview")
            else:
                st.session_state.basic_info = {
                    'first_name': first_name.strip(),
                    'last_name': last_name.strip(),
                    'email': email.strip()
                }
                st.session_state.schedule_data = schedule_data
                st.session_state.phase = 2
                print(f"PHASE 1 COMPLETE - {first_name} {last_name}")
                st.rerun()
    
    # PHASE 2: Application Form
    elif st.session_state.phase == 2:
        print(f"PHASE 2: Application - {st.session_state.basic_info.get('first_name')} {st.session_state.basic_info.get('last_name')}")
        from application import render_application_form
        
        st.title("Wilson Plant Co. + Sage Garden Cafe Job Fair")
        st.header("Application for Employment")
        
        if st.button("← Back to Registration", key="phase2_back"):
            print("Back to registration")
            st.session_state.phase = 1
            st.rerun()
        
        st.markdown("---")
        
        application_data = render_application_form(
            st.session_state.basic_info.get('first_name', ''),
            st.session_state.basic_info.get('last_name', ''),
            st.session_state.basic_info.get('email', '')
        )
        
        if application_data:
            print(f"Form submitted - {st.session_state.basic_info.get('first_name')} {st.session_state.basic_info.get('last_name')}")
            st.session_state.application_data = application_data
            st.session_state.phase = 3
            st.session_state.processing_step = 0
            st.rerun()
    
    # PHASE 3: Multi-step processing (NON-BLOCKING)
    elif st.session_state.phase == 3:
        # Generate submission ID once
        if not st.session_state.submission_id:
            st.session_state.submission_id = generate_submission_id()
            st.session_state.full_data = {
                **st.session_state.basic_info,
                **st.session_state.schedule_data,
                **st.session_state.application_data,
                'submission_id': st.session_state.submission_id
            }
            st.session_state.status = {
                'pdf': False,
                'drive': False,
                'sheets': False,
                'company_email': False,
                'confirmation_email': False
            }
        
        sub_id = st.session_state.submission_id
        full_data = st.session_state.full_data
        status = st.session_state.status
        step = st.session_state.processing_step
        
        applicant_name = f"{full_data.get('first_name')} {full_data.get('last_name')}"
        
        st.title("Submitting Your Application")
        st.info(f"**Reference ID:** {sub_id}")
        st.write(f"**Applicant:** {applicant_name}")
        
        # Progress indicators
        step1_txt = "⏳ Preparing your application..." if step == 0 else ("✅ Application prepared" if status.get('pdf') else "⚠️ Application prepared (PDF unavailable)")
        step2_txt = "⏳ Sending to our HR team..." if step == 1 else ("✅ Sent to our HR team" if step > 1 and status.get('sheets') else ("❌ Failed to send" if step > 1 else "⚪ Sending to our HR team"))
        step3_txt = "⏳ Registering for job fair..." if step == 2 else ("✅ Registered for job fair" if step > 2 else "⚪ Registering for job fair")
        step4_txt = "⏳ Finalizing..." if step == 3 else ("✅ Complete!" if step > 3 else "⚪ Finalizing")
        
        st.markdown(step1_txt)
        st.markdown(step2_txt)
        st.markdown(step3_txt)
        st.markdown(step4_txt)
        
        # STEP 0: Generate PDF (with immediate rerun after)
        if step == 0:
            print(f"SUBMISSION {sub_id}: STEP 0 - Generating PDF for {applicant_name}")
            
            from application_pdf_generator import generate_application_pdf
            
            try:
                pdf_buffer = generate_application_pdf(full_data)
                if pdf_buffer:
                    st.session_state.pdf_buffer = pdf_buffer
                    status['pdf'] = True
                    print(f"SUBMISSION {sub_id}: PDF generated for {applicant_name}")
                else:
                    print(f"SUBMISSION {sub_id}: PDF generation failed for {applicant_name}")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: PDF error for {applicant_name} - {e}")
                print(traceback.format_exc())
            
            st.session_state.processing_step = 1
            time.sleep(0.3)
            st.rerun()
        
        # STEP 1: Upload PDF & Save to Sheets
        elif step == 1:
            print(f"SUBMISSION {sub_id}: STEP 1 - Saving to sheets for {applicant_name}")
            
            from application_sheets_manager import upload_pdf_to_drive, send_application_to_sheet
            
            pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
            pdf_link = ""
            
            # Upload PDF if available
            if st.session_state.pdf_buffer:
                try:
                    print(f"SUBMISSION {sub_id}: Uploading PDF for {applicant_name}")
                    pdf_link = upload_pdf_to_drive(st.session_state.pdf_buffer, pdf_filename)
                    if pdf_link:
                        status['drive'] = True
                        print(f"SUBMISSION {sub_id}: PDF uploaded for {applicant_name}")
                except Exception as e:
                    print(f"SUBMISSION {sub_id}: Upload failed for {applicant_name} - {e}")
                    print(traceback.format_exc())
            
            full_data['pdf_link'] = pdf_link
            st.session_state.full_data = full_data
            st.session_state.pdf_filename = pdf_filename
            
            # Save to Sheets
            try:
                status['sheets'] = send_application_to_sheet(full_data)
                if status['sheets']:
                    print(f"SUBMISSION {sub_id}: Saved to sheets for {applicant_name}")
                else:
                    print(f"SUBMISSION {sub_id}: Sheets save failed for {applicant_name}")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: Sheets error for {applicant_name} - {e}")
                print(traceback.format_exc())
            
            st.session_state.processing_step = 2
            time.sleep(0.3)
            st.rerun()
        
        # STEP 2: Send Notifications
        elif step == 2:
            print(f"SUBMISSION {sub_id}: STEP 2 - Sending emails for {applicant_name}")
            
            from application_notifications import send_application_notification, send_confirmation_email
            
            # Company email
            if st.session_state.pdf_buffer and status.get('sheets'):
                try:
                    st.session_state.pdf_buffer.seek(0)
                    status['company_email'] = send_application_notification(full_data, st.session_state.pdf_buffer)
                    if status['company_email']:
                        print(f"SUBMISSION {sub_id}: Company email sent for {applicant_name}")
                except Exception as e:
                    print(f"SUBMISSION {sub_id}: Company email error for {applicant_name} - {e}")
                    print(traceback.format_exc())
            
            # Confirmation email
            try:
                status['confirmation_email'] = send_confirmation_email(full_data)
                if status['confirmation_email']:
                    print(f"SUBMISSION {sub_id}: Confirmation sent for {applicant_name}")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: Confirmation error for {applicant_name} - {e}")
                print(traceback.format_exc())
            
            st.session_state.processing_step = 3
            time.sleep(0.3)
            st.rerun()
        
        # STEP 3: Finalize
        elif step == 3:
            print(f"SUBMISSION {sub_id}: STEP 3 - Finalizing for {applicant_name}")
            
            st.session_state.status = status
            st.session_state.submitted = True
            
            print(f"SUBMISSION {sub_id}: COMPLETE for {applicant_name}")
            print(f"  PDF: {'YES' if status['pdf'] else 'NO'}")
            print(f"  Drive: {'YES' if status['drive'] else 'NO'}")
            print(f"  Sheets: {'YES' if status['sheets'] else 'NO'}")
            print(f"  Company Email: {'YES' if status['company_email'] else 'NO'}")
            print(f"  Confirmation: {'YES' if status['confirmation_email'] else 'NO'}")
            
            time.sleep(0.5)
            st.rerun()

if __name__ == "__main__":
    main()
