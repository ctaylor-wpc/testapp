# app.py
# Main application file for Job Fair Registration
# PRODUCTION VERSION with maintenance mode and terminal state

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
    pass  # No maintenance file, continue normally

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
    
    if st.session_state.render_count > 20 and (time.time() - st.session_state.render_start) < 5:
        print(f"⚠️ INFINITE LOOP DETECTED: {st.session_state.render_count} renders in {time.time() - st.session_state.render_start:.1f}s")
        st.error("⚠️ App error detected. Please refresh the page to start over.")
        st.stop()
    
    if time.time() - st.session_state.render_start > 5:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()

def initialize_app():
    """Initialize session state with safe defaults"""
    if 'initialized' not in st.session_state:
        print("🔧 INITIALIZING NEW SESSION")
        st.session_state.initialized = True
        st.session_state.phase = 1
        st.session_state.basic_info = {}
        st.session_state.schedule_data = {}
        st.session_state.application_data = {}
        st.session_state.submission_id = None
        st.session_state.submitted = False  # TERMINAL STATE
        st.session_state.submission_started = False
        st.session_state.pdf_generated = False
        st.session_state.pdf_buffer = None
        st.session_state.pdf_filename = None
        st.session_state.full_data = None
        st.session_state.submission_status = {}

def reset_app():
    """Complete reset - clears everything"""
    print("🔄 RESETTING APP - CLEARING ALL DATA")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_app()

def generate_submission_id():
    """Generate unique ID for tracking"""
    sub_id = str(uuid.uuid4())[:8].upper()
    print(f"🆔 NEW SUBMISSION ID: {sub_id}")
    return sub_id

def show_progress_step(step_num, total_steps, message, complete=False):
    """Show a progress step with checkmark when complete"""
    if complete:
        return f"✅ {message}"
    elif step_num == total_steps:
        return f"⏳ {message}..."
    else:
        return f"⚪ {message}"

def main():
    check_render_loop()
    initialize_app()
    
    # TERMINAL STATE CHECK - Show final confirmation and stop
    if st.session_state.get('submitted'):
        print(f"📌 TERMINAL STATE: Application already submitted (ID: {st.session_state.submission_id})")
        
        st.title("✅ Application Submitted!")
        st.success("Your application has been received.")
        
        # Show submission details
        if st.session_state.submission_id:
            st.info(f"**Reference ID:** {st.session_state.submission_id}")
        
        if st.session_state.full_data:
            st.markdown("### Your Interview Details:")
            st.write(f"**Name:** {st.session_state.full_data.get('first_name')} {st.session_state.full_data.get('last_name')}")
            st.write(f"**Location:** {st.session_state.full_data.get('location', 'N/A')}")
            st.write(f"**Date:** {st.session_state.full_data.get('date', 'N/A')}")
            st.write(f"**Time:** {st.session_state.full_data.get('time_slot', 'N/A')}")
        
        # Show status
        status = st.session_state.submission_status
        if status:
            st.markdown("### Submission Status:")
            if status.get('sheets'):
                st.write("✅ Application saved to database")
            if status.get('pdf'):
                st.write("✅ PDF generated")
            if status.get('confirmation_email'):
                st.write("✅ Confirmation email sent")
        
        # Download button
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
            print(f"🔄 New application requested")
            reset_app()
            st.rerun()
        
        st.stop()  # CRITICAL: Prevents any further rendering
    
    # Normal flow continues only if NOT submitted
    st.title("Wilson Plant Co. + Sage Garden Cafe Job Fair")
    st.markdown("""
    Apply to begin a challenging and rewarding career path in the horticulture, retail, and hospitality industries.
    Interview for a full or part-time, seasonal or year-round position with Wilson Plant Co, Sage Garden Café,
    or our landscaping & production teams.
    """)
    st.markdown("---")
    
    # PHASE 1: Registration
    if st.session_state.phase == 1:
        print(f"📋 PHASE 1: Registration")
        from application_scheduling import render_scheduling_section
        
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
            print(f"🔘 BUTTON CLICKED: Continue to Application")
            print(f"   First: '{first_name}', Last: '{last_name}', Email: '{email}'")
            
            if not all([first_name.strip(), last_name.strip(), email.strip()]):
                print("❌ VALIDATION FAILED: Missing required fields")
                st.error("Please fill in all required fields (First Name, Last Name, Email)")
            elif not schedule_data:
                print("❌ VALIDATION FAILED: No schedule selected")
                st.error("Please select a time slot for your interview")
            else:
                st.session_state.basic_info = {
                    'first_name': first_name.strip(),
                    'last_name': last_name.strip(),
                    'email': email.strip()
                }
                st.session_state.schedule_data = schedule_data
                st.session_state.phase = 2
                print(f"✅ PHASE 1 COMPLETE - Advancing to Phase 2")
                st.rerun()
    
    # PHASE 2: Application Form
    elif st.session_state.phase == 2:
        print(f"📝 PHASE 2: Application Form")
        from application import render_application_form
        
        st.header("Application for Employment")
        
        if st.button("← Back to Registration", key="phase2_back"):
            print("🔙 BACK BUTTON - Returning to Phase 1")
            st.session_state.phase = 1
            st.rerun()
        
        st.markdown("---")
        
        application_data = render_application_form(
            st.session_state.basic_info.get('first_name', ''),
            st.session_state.basic_info.get('last_name', ''),
            st.session_state.basic_info.get('email', '')
        )
        
        if application_data:
            print(f"✅ APPLICATION FORM SUBMITTED")
            st.session_state.application_data = application_data
            st.session_state.phase = 3
            st.rerun()
    
    # PHASE 3: Processing & Confirmation
    elif st.session_state.phase == 3:
        print(f"🎯 PHASE 3: Processing Submission")
        
        # ONE-SHOT GUARD
        if not st.session_state.submission_started:
            st.session_state.submission_started = True
            st.session_state.submission_id = generate_submission_id()
            sub_id = st.session_state.submission_id
            
            print(f"🚀 SUBMISSION {sub_id}: Starting processing")
            
            # Combine data
            full_data = {
                **st.session_state.basic_info,
                **st.session_state.schedule_data,
                **st.session_state.application_data,
                'submission_id': sub_id
            }
            st.session_state.full_data = full_data
            print(f"📦 SUBMISSION {sub_id}: Data combined")
            
            # Show processing UI
            st.title("Submitting Your Application")
            st.info(f"**Reference ID:** {sub_id}")
            
            # Progress container
            progress_container = st.container()
            
            with progress_container:
                step1 = st.empty()
                step2 = st.empty()
                step3 = st.empty()
                step4 = st.empty()
                
                step1.markdown(show_progress_step(1, 1, "Preparing your application"))
                step2.markdown(show_progress_step(2, 2, "Sending to our HR team"))
                step3.markdown(show_progress_step(3, 3, "Registering for job fair"))
                step4.markdown(show_progress_step(4, 4, "Finalizing submission"))
            
            # Lazy imports
            from application_sheets_manager import send_application_to_sheet, upload_pdf_to_drive
            from application_pdf_generator import generate_application_pdf
            from application_notifications import send_application_notification, send_confirmation_email
            
            status = {
                'pdf': False,
                'drive': False,
                'sheets': False,
                'company_email': False,
                'confirmation_email': False
            }
            
            # STEP 1: Generate PDF
            pdf_buffer = None
            if not st.session_state.pdf_generated:
                try:
                    print(f"📄 SUBMISSION {sub_id}: STEP 1 - Generating PDF")
                    step1.markdown(show_progress_step(1, 1, "Preparing your application"))
                    
                    pdf_buffer = generate_application_pdf(full_data)
                    
                    if pdf_buffer:
                        st.session_state.pdf_buffer = pdf_buffer
                        st.session_state.pdf_generated = True
                        status['pdf'] = True
                        print(f"✅ SUBMISSION {sub_id}: PDF generated")
                        step1.markdown(show_progress_step(1, 0, "Preparing your application", complete=True))
                    else:
                        print(f"⚠️ SUBMISSION {sub_id}: PDF generation failed")
                        step1.markdown("⚠️ Preparing your application (PDF unavailable)")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: PDF error - {e}")
                    print(traceback.format_exc())
                    step1.markdown("⚠️ Preparing your application (PDF unavailable)")
            else:
                pdf_buffer = st.session_state.pdf_buffer
                status['pdf'] = True if pdf_buffer else False
                step1.markdown(show_progress_step(1, 0, "Preparing your application", complete=True))
            
            # STEP 2: Upload to Drive & Save to Sheets
            step2.markdown(show_progress_step(2, 2, "Sending to our HR team"))
            
            pdf_link = ""
            pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
            
            if pdf_buffer:
                try:
                    print(f"☁️ SUBMISSION {sub_id}: Uploading PDF")
                    pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename)
                    if pdf_link:
                        status['drive'] = True
                        print(f"✅ SUBMISSION {sub_id}: PDF uploaded")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: Upload failed - {e}")
                    print(traceback.format_exc())
            
            full_data['pdf_link'] = pdf_link
            st.session_state.full_data = full_data
            
            try:
                print(f"📊 SUBMISSION {sub_id}: Saving to Sheets")
                status['sheets'] = send_application_to_sheet(full_data)
                if status['sheets']:
                    print(f"✅ SUBMISSION {sub_id}: Saved to Sheets")
                    step2.markdown(show_progress_step(2, 0, "Sending to our HR team", complete=True))
                else:
                    print(f"❌ SUBMISSION {sub_id}: Sheets save failed")
                    step2.markdown("❌ Sending to our HR team (failed)")
            except Exception as e:
                print(f"❌ SUBMISSION {sub_id}: Sheets error - {e}")
                print(traceback.format_exc())
                step2.markdown("❌ Sending to our HR team (error)")
            
            # STEP 3: Send Notifications
            step3.markdown(show_progress_step(3, 3, "Registering for job fair"))
            
            if pdf_buffer and status['sheets']:
                try:
                    print(f"📧 SUBMISSION {sub_id}: Sending company email")
                    pdf_buffer.seek(0)
                    status['company_email'] = send_application_notification(full_data, pdf_buffer)
                    if status['company_email']:
                        print(f"✅ SUBMISSION {sub_id}: Company email sent")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: Company email error - {e}")
                    print(traceback.format_exc())
            
            try:
                print(f"📧 SUBMISSION {sub_id}: Sending confirmation email")
                status['confirmation_email'] = send_confirmation_email(full_data)
                if status['confirmation_email']:
                    print(f"✅ SUBMISSION {sub_id}: Confirmation sent")
                    step3.markdown(show_progress_step(3, 0, "Registering for job fair", complete=True))
                else:
                    print(f"⚠️ SUBMISSION {sub_id}: Confirmation failed")
                    step3.markdown("⚠️ Registering for job fair (email pending)")
            except Exception as e:
                print(f"❌ SUBMISSION {sub_id}: Confirmation error - {e}")
                print(traceback.format_exc())
                step3.markdown("⚠️ Registering for job fair (email pending)")
            
            # STEP 4: Finalize
            step4.markdown(show_progress_step(4, 4, "Finalizing submission"))
            time.sleep(0.5)
            step4.markdown(show_progress_step(4, 0, "Finalizing submission", complete=True))
            
            # Store results
            st.session_state.pdf_filename = pdf_filename
            st.session_state.submission_status = status
            
            # SET TERMINAL STATE
            st.session_state.submitted = True
            
            print(f"📊 SUBMISSION {sub_id}: COMPLETE")
            print(f"   PDF: {'✅' if status['pdf'] else '❌'}")
            print(f"   Drive: {'✅' if status['drive'] else '❌'}")
            print(f"   Sheets: {'✅' if status['sheets'] else '❌'}")
            print(f"   Company Email: {'✅' if status['company_email'] else '❌'}")
            print(f"   Confirmation: {'✅' if status['confirmation_email'] else '❌'}")
            
            # Force rerun to show terminal state
            time.sleep(1)
            st.rerun()

if __name__ == "__main__":
    main()