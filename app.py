# app.py
# Main application file for Wilson Plant Co. + Sage Garden Cafe Employment Application
# v3.0 - Removed job fair scheduling phase; now a standalone application form

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
        st.info("Refresh this page in a few minutes to try again.")
        st.stop()
except ImportError:
    pass

st.set_page_config(page_title="Wilson Plant Co. + Sage Garden Cafe - Employment Application", layout="centered")

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

    # TERMINAL STATE - Completion page
    if st.session_state.get('submitted'):
        sub_id = st.session_state.submission_id
        print(f"TERMINAL STATE: ID {sub_id}")

        st.title("Application Submitted!")
        st.success("Your application has been received.")

        if sub_id:
            st.info(f"**Reference ID:** {sub_id}")

        if st.session_state.full_data:
            data = st.session_state.full_data
            st.write(f"**Name:** {data.get('first_name')} {data.get('last_name')}")

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
                label="Download Your Application PDF",
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

    # PHASE 1: Application Form
    if st.session_state.phase == 1:
        print("PHASE 1: Application Form")
        from application import render_application_form

        st.title("Wilson Plant Co. + Sage Garden Cafe")
        st.markdown("""
        Apply to begin a challenging and rewarding career path in the horticulture, retail, and hospitality industries.
        Apply for a full or part-time, seasonal or year-round position with Wilson Plant Co, Sage Garden Cafe,
        or our landscaping & production teams.
        """)
        st.header("Application for Employment")
        st.markdown("---")

        application_data = render_application_form()

        if application_data:
            print("Form submitted")
            st.session_state.application_data = application_data
            st.session_state.phase = 2
            st.session_state.processing_step = 0
            st.rerun()

    # PHASE 2: PROCESSING VIEW
    elif st.session_state.phase == 2:
        # Generate submission ID and data once
        if not st.session_state.submission_id:
            st.session_state.submission_id = generate_submission_id()
            st.session_state.full_data = {
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

        st.title("Processing Your Application")
        st.write(f"**Applicant:** {applicant_name}")
        st.info(f"**Reference ID:** {sub_id}")

        st.markdown("---")
        st.markdown("### Please wait, do not close this page...")

        # Progress indicators
        if step >= 0:
            if step == 0:
                st.markdown("#### Preparing your application...")
                st.progress(0.25)
            else:
                st.success("✅ Application prepared")

        if step >= 1:
            if step == 1:
                st.markdown("#### Saving application...")
                st.progress(0.50)
            elif step > 1:
                st.success("✅ Application saved")

        if step >= 2:
            if step == 2:
                st.markdown("#### Sending notifications...")
                st.progress(0.75)
            elif step > 2:
                st.success("✅ Notifications sent")

        if step >= 3:
            if step == 3:
                st.markdown("#### Finalizing submission...")
                st.progress(1.0)

        # Execute current step
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
            time.sleep(0.5)
            st.rerun()

        elif step == 1:
            print(f"SUBMISSION {sub_id}: STEP 1 - Saving to sheets for {applicant_name}")

            from application_sheets_manager import upload_pdf_to_drive, send_application_to_sheet

            pdf_filename = f"Application_{full_data['last_name']}_{full_data['first_name']}.pdf"
            pdf_link = ""

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
            time.sleep(0.5)
            st.rerun()

        elif step == 2:
            print(f"SUBMISSION {sub_id}: STEP 2 - Sending emails for {applicant_name}")

            from application_notifications import send_application_notification, send_confirmation_email

            if st.session_state.pdf_buffer:
                try:
                    st.session_state.pdf_buffer.seek(0)
                    status['company_email'] = send_application_notification(full_data, st.session_state.pdf_buffer)
                    if status['company_email']:
                        print(f"SUBMISSION {sub_id}: Company email sent for {applicant_name}")
                except Exception as e:
                    print(f"SUBMISSION {sub_id}: Company email error for {applicant_name} - {e}")
                    print(traceback.format_exc())

            try:
                status['confirmation_email'] = send_confirmation_email(full_data)
                if status['confirmation_email']:
                    print(f"SUBMISSION {sub_id}: Confirmation sent for {applicant_name}")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: Confirmation error for {applicant_name} - {e}")
                print(traceback.format_exc())

            st.session_state.processing_step = 3
            time.sleep(0.5)
            st.rerun()

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
