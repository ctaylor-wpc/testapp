# app.py
# Main application file for Job Fair Registration
# PRODUCTION-HARDENED VERSION

import os
import streamlit as st
import datetime
import traceback
import uuid
import time

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

# CRITICAL: Circuit breaker to prevent infinite loops
def check_render_loop():
    """Detect and break infinite render loops"""
    if 'render_count' not in st.session_state:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()
    
    st.session_state.render_count += 1
    
    # If >20 renders in 5 seconds, we have a loop
    if st.session_state.render_count > 20 and (time.time() - st.session_state.render_start) < 5:
        print(f"⚠️ INFINITE LOOP DETECTED: {st.session_state.render_count} renders in {time.time() - st.session_state.render_start:.1f}s")
        st.error("⚠️ App error detected. Please refresh the page to start over.")
        st.stop()
    
    # Reset counter every 5 seconds
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
        st.session_state.submission_complete = False
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
    sub_id = str(uuid.uuid4())[:8]
    print(f"🆔 NEW SUBMISSION ID: {sub_id}")
    return sub_id

def main():
    check_render_loop()
    initialize_app()
    
    # Header
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
        
        # Pre-fill from session state if available
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
        
        # ONE-SHOT BUTTON: Only execute once
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
                # SAVE DATA IMMEDIATELY
                st.session_state.basic_info = {
                    'first_name': first_name.strip(),
                    'last_name': last_name.strip(),
                    'email': email.strip()
                }
                st.session_state.schedule_data = schedule_data
                st.session_state.phase = 2
                print(f"✅ PHASE 1 COMPLETE - Advancing to Phase 2")
                print(f"   Saved: {st.session_state.basic_info}")
                st.rerun()
    
    # PHASE 2: Application Form
    elif st.session_state.phase == 2:
        print(f"📝 PHASE 2: Application Form")
        from application import render_application_form
        
        st.header("Application for Employment")
        
        if st.button("← Back to Registration", key="phase2_back"):
            print("🔙 BACK BUTTON CLICKED - Returning to Phase 1")
            st.session_state.phase = 1
            st.rerun()
        
        st.markdown("---")
        
        # Render form with pre-filled data
        application_data = render_application_form(
            st.session_state.basic_info.get('first_name', ''),
            st.session_state.basic_info.get('last_name', ''),
            st.session_state.basic_info.get('email', '')
        )
        
        if application_data:
            print(f"✅ APPLICATION FORM SUBMITTED")
            # SAVE DATA IMMEDIATELY
            st.session_state.application_data = application_data
            st.session_state.phase = 3
            print(f"   Keys received: {list(application_data.keys())[:10]}...")
            st.rerun()
    
    # PHASE 3: Submission & Confirmation
    elif st.session_state.phase == 3:
        print(f"🎯 PHASE 3: Submission")
        
        st.header("Application Submitted Successfully!")
        st.success("Thank you for applying to our job fair!")
        
        # ONE-SHOT GUARD: Only run submission logic once
        if not st.session_state.submission_started:
            st.session_state.submission_started = True
            st.session_state.submission_id = generate_submission_id()
            sub_id = st.session_state.submission_id
            
            print(f"🚀 SUBMISSION {sub_id}: Starting processing")
            
            # Combine all data immediately
            full_data = {
                **st.session_state.basic_info,
                **st.session_state.schedule_data,
                **st.session_state.application_data,
                'submission_id': sub_id
            }
            st.session_state.full_data = full_data
            print(f"📦 SUBMISSION {sub_id}: Data combined ({len(full_data)} fields)")
            
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
            
            progress_bar = st.progress(0, text="Processing your application...")
            
            # STEP 1: Generate PDF (with one-shot guard)
            pdf_buffer = None
            if not st.session_state.pdf_generated:
                try:
                    print(f"📄 SUBMISSION {sub_id}: STEP 1 - Generating PDF")
                    progress_bar.progress(20, text="Generating PDF...")
                    pdf_buffer = generate_application_pdf(full_data)
                    
                    if pdf_buffer:
                        st.session_state.pdf_buffer = pdf_buffer
                        st.session_state.pdf_generated = True
                        status['pdf'] = True
                        print(f"✅ SUBMISSION {sub_id}: PDF generated successfully")
                    else:
                        print(f"⚠️ SUBMISSION {sub_id}: PDF generation returned None")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: PDF generation failed - {e}")
                    print(traceback.format_exc())
            else:
                print(f"♻️ SUBMISSION {sub_id}: PDF already generated, reusing")
                pdf_buffer = st.session_state.pdf_buffer
                status['pdf'] = True if pdf_buffer else False
            
            # STEP 2: Upload to Drive
            pdf_link = ""
            pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
            
            if pdf_buffer:
                try:
                    print(f"☁️ SUBMISSION {sub_id}: STEP 2 - Uploading PDF to Drive")
                    progress_bar.progress(40, text="Uploading PDF...")
                    pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename)
                    
                    if pdf_link:
                        status['drive'] = True
                        print(f"✅ SUBMISSION {sub_id}: PDF uploaded - {pdf_link}")
                    else:
                        print(f"⚠️ SUBMISSION {sub_id}: PDF upload returned empty")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: PDF upload failed - {e}")
                    print(traceback.format_exc())
            else:
                print(f"⏭️ SUBMISSION {sub_id}: Skipping Drive upload (no PDF)")
            
            # Add PDF link to data
            full_data['pdf_link'] = pdf_link
            st.session_state.full_data = full_data
            
            # STEP 3: Save to Sheets
            try:
                print(f"📊 SUBMISSION {sub_id}: STEP 3 - Saving to Google Sheets")
                progress_bar.progress(60, text="Saving to database...")
                status['sheets'] = send_application_to_sheet(full_data)
                
                if status['sheets']:
                    print(f"✅ SUBMISSION {sub_id}: Saved to Sheets")
                else:
                    print(f"❌ SUBMISSION {sub_id}: Sheets save failed")
            except Exception as e:
                print(f"❌ SUBMISSION {sub_id}: Sheets exception - {e}")
                print(traceback.format_exc())
            
            # STEP 4: Company email
            if pdf_buffer and status['sheets']:
                try:
                    print(f"📧 SUBMISSION {sub_id}: STEP 4 - Sending company email")
                    progress_bar.progress(80, text="Sending notifications...")
                    pdf_buffer.seek(0)
                    status['company_email'] = send_application_notification(full_data, pdf_buffer)
                    
                    if status['company_email']:
                        print(f"✅ SUBMISSION {sub_id}: Company email sent")
                    else:
                        print(f"⚠️ SUBMISSION {sub_id}: Company email failed")
                except Exception as e:
                    print(f"❌ SUBMISSION {sub_id}: Company email exception - {e}")
                    print(traceback.format_exc())
            else:
                print(f"⏭️ SUBMISSION {sub_id}: Skipping company email")
            
            # STEP 5: Confirmation email
            try:
                print(f"📧 SUBMISSION {sub_id}: STEP 5 - Sending confirmation email")
                status['confirmation_email'] = send_confirmation_email(full_data)
                
                if status['confirmation_email']:
                    print(f"✅ SUBMISSION {sub_id}: Confirmation email sent")
                else:
                    print(f"⚠️ SUBMISSION {sub_id}: Confirmation email failed")
            except Exception as e:
                print(f"❌ SUBMISSION {sub_id}: Confirmation email exception - {e}")
                print(traceback.format_exc())
            
            progress_bar.progress(100, text="Complete!")
            time.sleep(0.5)
            progress_bar.empty()
            
            # Store results
            st.session_state.pdf_filename = pdf_filename
            st.session_state.submission_status = status
            st.session_state.submission_complete = True
            
            print(f"📊 SUBMISSION {sub_id}: FINAL STATUS")
            print(f"   PDF: {'✅' if status['pdf'] else '❌'}")
            print(f"   Drive: {'✅' if status['drive'] else '❌'}")
            print(f"   Sheets: {'✅' if status['sheets'] else '❌'}")
            print(f"   Company Email: {'✅' if status['company_email'] else '❌'}")
            print(f"   Confirmation: {'✅' if status['confirmation_email'] else '❌'}")
        
        # Show status (persists across reruns)
        status = st.session_state.submission_status
        
        if status.get('sheets'):
            st.success("✅ Your application has been saved")
        else:
            st.error("❌ Failed to save application - please contact us at info@wilsonnurseriesky.com")
            st.info(f"Reference ID: {st.session_state.submission_id}")
        
        if status.get('pdf'):
            st.success("✅ PDF generated successfully")
        else:
            st.warning("⚠️ PDF could not be generated, but your application was saved")
        
        if status.get('confirmation_email'):
            st.success("✅ Confirmation email sent")
        else:
            st.warning("⚠️ Confirmation email could not be sent")
        
        # Download button
        if st.session_state.pdf_buffer:
            st.session_state.pdf_buffer.seek(0)
            st.download_button(
                label="📄 Download Your Application",
                data=st.session_state.pdf_buffer,
                file_name=st.session_state.pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )
        
        # Interview details
        if st.session_state.full_data:
            st.markdown("### Your Interview Details:")
            st.write(f"**Location:** {st.session_state.full_data.get('location', 'N/A')}")
            st.write(f"**Date:** {st.session_state.full_data.get('date', 'N/A')}")
            st.write(f"**Time:** {st.session_state.full_data.get('time_slot', 'N/A')}")
        
        st.markdown("---")
        
        if st.button("Submit Another Application", use_container_width=True, key="submit_another"):
            print(f"🔄 SUBMIT ANOTHER CLICKED - Resetting app")
            reset_app()
            st.rerun()

if __name__ == "__main__":
    main()
