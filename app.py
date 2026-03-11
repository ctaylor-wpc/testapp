# app.py
# Main application file — Wilson Plant Co. + Sage Garden Cafe Employment Application
#
# SUBMISSION FLOW:
#
#   Phase 1: Application form (application.py). On submit, writes data to
#             session_state['pending_application'], sets 'form_ready_to_process',
#             and calls st.rerun().
#
#   Phase 3: Resume upload page. Intentionally minimal — just a greyed-out
#             resume button and a "Submit Application" button. Keeping this page
#             short ensures the processing screen (phase 2) is always visible at
#             the top of the page when the transition happens, so users never
#             see a frozen-looking blank area.
#
#   Phase 2: Processing screen. Background thread runs PDF/Drive/Sheets/Email
#             work. UI polls every 2s and shows live step-by-step progress.
#             Because phase 3 is short, this screen is always in view.
#
#   Terminal: Background thread sets progress['done'] = True. UI advances to
#             confirmation screen with submission ID and "you may close this page."
#
# DUPLICATE PROTECTION:
#   - session_state['form_submitted'] is set True on first form submit click.
#   - session_state['processing_started'] is set True when phase 3 submit is clicked.
#   - session_state['submission_id'] is generated once; background thread not restarted.

import os
import threading
import time
import traceback
import uuid

import streamlit as st
import streamlit.components.v1 as components


# ------------------------------------------------------------------ #
# SCROLL HELPER
# ------------------------------------------------------------------ #
def scroll_to_top():
    """Inject JS to scroll the browser to the top of the page."""
    components.html(
        """
        <script>
            window.parent.document.querySelector('section.main').scrollTo({top: 0, behavior: 'instant'});
            window.parent.scrollTo({top: 0, behavior: 'instant'});
        </script>
        """,
        height=0,
    )


# ------------------------------------------------------------------ #
# MAINTENANCE CHECK (must be first)
# ------------------------------------------------------------------ #
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


st.set_page_config(
    page_title="Wilson Plant Co. + Sage Garden Cafe – Employment Application",
    layout="centered"
)

st.markdown("""
<style>
.stTextInput, .stTextArea, .stSelectbox, .stRadio, .stCheckbox { margin-bottom: 1rem; }
.stTextInput > div > div > input,
.stTextArea > div > div > textarea { font-size: 16px !important; }
h1, h2, h3 { margin-top: 1.5rem; margin-bottom: 1rem; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ #
# HELPERS
# ------------------------------------------------------------------ #
def check_render_loop():
    if 'render_count' not in st.session_state:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()
    st.session_state.render_count += 1
    if st.session_state.render_count > 30 and (time.time() - st.session_state.render_start) < 5:
        st.error("App error detected. Please refresh the page.")
        st.stop()
    if time.time() - st.session_state.render_start > 5:
        st.session_state.render_count = 0
        st.session_state.render_start = time.time()


def initialize_app():
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized      = True
        st.session_state.phase                = 1
        st.session_state.submission_id        = None
        st.session_state.submitted            = False
        st.session_state.pdf_buffer           = None
        st.session_state.pdf_filename         = None
        st.session_state.full_data            = None
        st.session_state.status               = {}
        st.session_state.form_ready_to_process = False
        st.session_state.pending_application  = {}
        # NEW: flag that disables the submit button after first click
        st.session_state.form_submitted       = False
        st.session_state.processing_started   = False
        st.session_state.resume_bytes         = None
        st.session_state.resume_filename      = None
        st.session_state.resume_mime          = None
        # NEW: shared progress dict written by the background thread and read
        #      by the UI polling loop.  Lives outside of session_state so the
        #      background thread (which has no access to session_state) can
        #      write to it.  We store it as a plain Python dict reference
        #      inside session_state so it survives reruns.
        st.session_state.bg_progress         = None


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_app()


def generate_submission_id():
    sub_id = str(uuid.uuid4())[:8].upper()
    print(f"NEW SUBMISSION ID: {sub_id}")
    return sub_id


# ------------------------------------------------------------------ #
# BACKGROUND WORKER
# ------------------------------------------------------------------ #
def run_background_processing(full_data, pdf_filename, progress):
    """
    Execute all slow operations in a background thread so the HTTP request
    (and therefore the Streamlit UI) returns immediately.

    `progress` is a plain Python dict shared between this thread and the
    Streamlit render loop.  Keys written here:
        step        (int)   0-4  current step number
        step_label  (str)   human-readable description of current step
        pdf_buffer  (BytesIO | None)
        status      (dict)  mirrors the old app.py status dict
        error       (str | None)  set if a fatal exception occurs
        done        (bool)  True when all steps are complete
    """
    sub_id = full_data.get('submission_id', '?')
    status = {}
    pdf_buffer = None

    try:
        # ---- STEP 1: Generate PDF ----------------------------------------
        progress['step'] = 1
        progress['step_label'] = "Generating your application PDF…"
        print(f"SUBMISSION {sub_id}: BG STEP 1 – Generating PDF")
        try:
            from application_pdf_generator import generate_application_pdf
            pdf_buffer = generate_application_pdf(full_data)
            if pdf_buffer:
                status['pdf'] = True
                print(f"SUBMISSION {sub_id}: PDF generated")
            else:
                print(f"SUBMISSION {sub_id}: PDF generation returned None (template missing?)")
        except Exception as e:
            print(f"SUBMISSION {sub_id}: PDF error – {e}")
            print(traceback.format_exc())

        progress['pdf_buffer'] = pdf_buffer

        # ---- STEP 2: Upload PDF + resume to Google Drive + save to Sheets --
        progress['step'] = 2
        progress['step_label'] = "Saving your application to our database…"
        print(f"SUBMISSION {sub_id}: BG STEP 2 – Drive upload + Sheets")

        pdf_link = ""
        if pdf_buffer:
            try:
                from application_sheets_manager import upload_pdf_to_drive
                pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename)
                if pdf_link:
                    status['drive'] = True
                    print(f"SUBMISSION {sub_id}: PDF uploaded to Drive")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: Drive upload failed – {e}")
                print(traceback.format_exc())

        # Upload resume if one was provided
        resume_bytes = full_data.get('resume_bytes')
        if resume_bytes:
            try:
                import io as _io
                from application_sheets_manager import upload_pdf_to_drive
                first = full_data.get('first_name', 'Applicant')
                last  = full_data.get('last_name', '')
                orig_ext = (full_data.get('resume_filename') or 'resume.pdf').rsplit('.', 1)[-1]
                resume_drive_name = f"{first} {last} - Resume.{orig_ext}"
                resume_buf = _io.BytesIO(resume_bytes)
                resume_mime_type = full_data.get('resume_mime') or 'application/octet-stream'
                resume_link = upload_pdf_to_drive(resume_buf, resume_drive_name, mimetype=resume_mime_type)
                if resume_link:
                    status['resume_drive'] = True
                    print(f"SUBMISSION {sub_id}: Resume uploaded to Drive")
            except Exception as e:
                print(f"SUBMISSION {sub_id}: Resume upload failed – {e}")
                print(traceback.format_exc())

        full_data['pdf_link'] = pdf_link

        try:
            from application_sheets_manager import send_application_to_sheet
            status['sheets'] = send_application_to_sheet(full_data)
            print(f"SUBMISSION {sub_id}: Sheets write {'ok' if status.get('sheets') else 'failed'}")
        except Exception as e:
            print(f"SUBMISSION {sub_id}: Sheets error – {e}")
            print(traceback.format_exc())

        # ---- STEP 3: Send email notifications ----------------------------
        progress['step'] = 3
        progress['step_label'] = "Sending confirmation emails…"
        print(f"SUBMISSION {sub_id}: BG STEP 3 – Emails")

        try:
            from application_notifications import send_application_notification
            if pdf_buffer:
                pdf_buffer.seek(0)
                status['company_email'] = send_application_notification(full_data, pdf_buffer)
                print(f"SUBMISSION {sub_id}: Company email {'sent' if status.get('company_email') else 'failed'}")
        except Exception as e:
            print(f"SUBMISSION {sub_id}: Company email error – {e}")
            print(traceback.format_exc())

        try:
            from application_notifications import send_confirmation_email
            status['confirmation_email'] = send_confirmation_email(full_data)
            print(f"SUBMISSION {sub_id}: Confirmation email {'sent' if status.get('confirmation_email') else 'failed'}")
        except Exception as e:
            print(f"SUBMISSION {sub_id}: Confirmation email error – {e}")
            print(traceback.format_exc())

        # ---- STEP 4: Done ------------------------------------------------
        progress['step'] = 4
        progress['step_label'] = "Finalizing…"
        progress['status'] = status
        progress['full_data'] = full_data
        progress['pdf_filename'] = pdf_filename

        print(f"SUBMISSION {sub_id}: BACKGROUND COMPLETE")
        print(f"  PDF:     {status.get('pdf')}")
        print(f"  Drive:   {status.get('drive')}")
        print(f"  Sheets:  {status.get('sheets')}")
        print(f"  BizMail: {status.get('company_email')}")
        print(f"  ConfMail:{status.get('confirmation_email')}")

        # Signal the UI that we're done (checked every 2 s by the poll loop)
        progress['done'] = True

    except Exception as fatal:
        print(f"SUBMISSION {sub_id}: FATAL BACKGROUND ERROR – {fatal}")
        print(traceback.format_exc())
        progress['error'] = str(fatal)
        progress['done'] = True   # still end the polling loop


# ------------------------------------------------------------------ #
# MAIN
# ------------------------------------------------------------------ #
def main():
    check_render_loop()
    initialize_app()

    # ------------------------------------------------------------------ #
    # INTERCEPT: application.py set the flag — advance phase immediately.
    # This happens BEFORE any rendering so the form never appears again.
    # ------------------------------------------------------------------ #
    if st.session_state.get('form_ready_to_process'):
        st.session_state.form_ready_to_process = False   # clear flag
        st.session_state.phase                 = 3       # go to resume page first
        st.session_state.submission_id         = None
        st.session_state.bg_progress           = None

    # ------------------------------------------------------------------ #
    # TERMINAL STATE — Confirmation screen
    # ------------------------------------------------------------------ #
    if st.session_state.get('submitted'):
        sub_id = st.session_state.submission_id
        print(f"TERMINAL STATE: ID {sub_id}")

        scroll_to_top()
        st.title("✅ Application Submitted!")
        st.success("Your application has been received.")

        if sub_id:
            st.info(f"**Reference ID:** {sub_id}")

        if st.session_state.full_data:
            data = st.session_state.full_data
            st.write(f"**Name:** {data.get('first_name', '')} {data.get('last_name', '')}")

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

    # ------------------------------------------------------------------ #
    # PHASE 1 — Application form
    # ------------------------------------------------------------------ #
    if st.session_state.phase == 1:
        print("PHASE 1: Application Form")
        from application import render_application_form

        st.title("Wilson Plant Co. + Sage Garden Cafe")
        st.markdown("""
Apply to begin a challenging and rewarding career path in the horticulture, retail,
and hospitality industries. Apply for a full or part-time, seasonal or year-round
position with Wilson Plant Co, Sage Garden Cafe, or our landscaping & production teams.
""")
        st.header("Application for Employment")
        st.markdown("---")

        # render_application_form does NOT return data.
        # When the user submits, it writes to session_state and calls st.rerun().
        render_application_form()

    # ------------------------------------------------------------------ #
    # PHASE 3 — Resume upload (greyed out) + final submit trigger
    # Kept intentionally short so the phase 2 processing screen is always
    # visible at the top of the page after the user clicks Submit.
    # ------------------------------------------------------------------ #
    elif st.session_state.phase == 3:
        print("PHASE 3: Resume upload page")
        scroll_to_top()

        st.title("Almost Done!")
        st.success("✅ Your application form is complete.")
        st.markdown("---")

        st.subheader("Resume Upload (Optional)")
        uploaded_resume = st.file_uploader(
            "Upload your resume (PDF, Word, or text file)",
            type=["pdf", "doc", "docx", "txt"],
            key="resume_upload",
        )
        if uploaded_resume is not None:
            st.session_state.resume_bytes    = uploaded_resume.read()
            st.session_state.resume_filename = uploaded_resume.name
            st.session_state.resume_mime     = uploaded_resume.type
            st.success(f"✅ Resume ready: {uploaded_resume.name}")
        elif st.session_state.get('resume_bytes'):
            st.success(f"✅ Resume ready: {st.session_state.resume_filename}")

        st.markdown("---")

        if st.session_state.get('processing_started'):
            st.info("⏳ Submitting your application… please do not close this page.")
        else:
            if st.button("Submit Application", type="primary", use_container_width=True):
                st.session_state.processing_started = True
                st.session_state.phase = 2
                st.rerun()

    # ------------------------------------------------------------------ #
    # PHASE 2 — Processing screen (background thread + live progress poll)
    # ------------------------------------------------------------------ #
    elif st.session_state.phase == 2:

        # Generate submission ID and kick off background thread exactly once.
        if not st.session_state.submission_id:
            st.session_state.submission_id = generate_submission_id()

            # Build full_data from pending_application
            pending = st.session_state.get('pending_application', {})
            full_data = dict(pending)
            full_data['submission_id'] = st.session_state.submission_id

            # Attach resume if one was uploaded on the phase 3 page
            full_data['resume_bytes']    = st.session_state.get('resume_bytes')
            full_data['resume_filename'] = st.session_state.get('resume_filename')
            full_data['resume_mime']     = st.session_state.get('resume_mime')

            # Derive human-readable filename
            pdf_filename = (
                f"{full_data.get('first_name', 'Applicant')} "
                f"{full_data.get('last_name', '')} Application.pdf"
            )
            st.session_state.full_data    = full_data
            st.session_state.pdf_filename = pdf_filename

            # Create the shared progress dict and start the background thread.
            progress = {
                'step':        0,
                'step_label':  "Starting…",
                'pdf_buffer':  None,
                'status':      {},
                'full_data':   full_data,
                'pdf_filename': pdf_filename,
                'error':       None,
                'done':        False,
            }
            st.session_state.bg_progress = progress

            t = threading.Thread(
                target=run_background_processing,
                args=(full_data, pdf_filename, progress),
                daemon=True,
            )
            t.start()
            print(f"SUBMISSION {st.session_state.submission_id}: background thread started")

        # ------------------------------------------------------------------
        # From here on, just read the shared progress dict — never block.
        # ------------------------------------------------------------------
        progress  = st.session_state.bg_progress
        sub_id    = st.session_state.submission_id
        full_data = st.session_state.full_data
        applicant_name = (
            f"{full_data.get('first_name', '')} {full_data.get('last_name', '')}"
        )

        # Check if the background thread finished since last render
        if progress and progress.get('done'):
            st.session_state.status     = progress.get('status', {})
            st.session_state.pdf_buffer = progress.get('pdf_buffer')
            st.session_state.full_data  = progress.get('full_data', full_data)
            st.session_state.submitted  = True
            print(f"SUBMISSION {sub_id}: UI detected completion, advancing to terminal state")
            st.rerun()
            return

        # ---- Live processing UI -----------------------------------------
        # Warning banner is rendered first so it's always visible without scrolling.
        scroll_to_top()

        st.markdown("""
<div style="
    background: #192D43;
    border: 1px solid #192D43;
    border-radius: 6px;
    padding: 14px 18px;
    text-align: center;
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: #3D9DF3;
">
  ⚠️ Submitting your application — please do not close this window.
</div>
""", unsafe_allow_html=True)

        st.markdown(f"**Applicant:** {applicant_name} &nbsp;|&nbsp; **Ref:** {sub_id}")

        step = progress.get('step', 0) if progress else 0
        STEPS = [
            (0,    None),
            (0.25, "✅ PDF generated"),
            (0.55, "✅ Application saved to database"),
            (0.80, "✅ Confirmation emails sent"),
            (1.0,  "✅ All done"),
        ]
        bar_value = STEPS[min(step, len(STEPS) - 1)][0]

        # Completed steps
        for i in range(1, step + 1):
            label = STEPS[i][1]
            if label:
                st.success(label)

        # Current step with spinner
        if step < len(STEPS) - 1:
            current_label = progress.get('step_label', 'Working…') if progress else 'Starting…'
            st.markdown(f"""
<div style="
    display:flex; align-items:center; gap:12px;
    background:#f0f4ff; border:1px solid #c5d0f0;
    border-radius:6px; padding:12px 16px; margin:6px 0;
">
  <div style="
    width:20px; height:20px; flex-shrink:0;
    border:3px solid #d0d8f0; border-top-color:#1a5ce8;
    border-radius:50%; animation:spin 0.85s linear infinite;
  "></div>
  <span style="font-size:0.95rem;">{current_label}</span>
</div>
<style>@keyframes spin {{ to {{ transform: rotate(360deg); }} }}</style>
""", unsafe_allow_html=True)

        st.progress(bar_value)
        st.caption("This typically takes 20–40 seconds.")

        # Use JS-based auto-refresh so the HTTP connection closes immediately
        # after rendering rather than blocking for 2 seconds per poll cycle.
        # This is what was causing the very long responseTimeMS in the logs.
        components.html(
            "<script>setTimeout(function(){ window.parent.location.reload(); }, 2000);</script>",
            height=0,
        )


if __name__ == "__main__":
    main()
