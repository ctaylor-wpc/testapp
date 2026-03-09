# app.py
# Main application file — Wilson Plant Co. + Sage Garden Cafe Employment Application
#
# SUBMISSION FLOW (updated):
#
#   Phase 1: Show application form (application.py renders it).
#             application.py saves data to session_state['pending_application'],
#             sets session_state['form_ready_to_process'] = True, then calls
#             st.rerun(). The submit button is disabled after first click to
#             prevent duplicate submissions.
#
#   Phase 2: On that rerun, app.py detects the flag, clears it, generates a
#             submission_id, and immediately launches ALL processing work in a
#             background thread (PDF → Drive → Sheets → Emails). The UI returns
#             instantly and shows a live progress screen. Every 2 seconds the
#             page reruns to poll the background thread's progress dict and
#             update the progress bar. The user sees real-time step updates
#             without the page ever freezing.
#
#   Phase 3 (terminal): Background thread sets progress['done'] = True. On the
#             next poll rerun, app.py detects this, copies the final status into
#             session_state, and shows the confirmation / download screen.
#
# DUPLICATE PROTECTION:
#   - session_state['form_submitted'] is set to True on first submit click;
#     application.py checks this flag and keeps the button disabled.
#   - session_state['submission_id'] is generated once per phase-2 entry; if
#     phase 2 is re-entered with the same pending data the id is reused and the
#     background thread is not restarted.

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

        # ---- STEP 2: Upload PDF to Google Drive + save to Sheets ----------
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
        st.session_state.phase                 = 2       # go to processing
        st.session_state.submission_id         = None    # generated fresh below
        st.session_state.bg_progress           = None    # reset for new job

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

            # Derive human-readable filename
            pdf_filename = (
                f"{full_data.get('first_name', 'Applicant')} "
                f"{full_data.get('last_name', '')} Application.pdf"
            )
            st.session_state.full_data    = full_data
            st.session_state.pdf_filename = pdf_filename

            # Create the shared progress dict and start the background thread.
            # The dict is stored in session_state so it persists across reruns.
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
                daemon=True,  # thread dies if the Streamlit process exits
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
            # Copy results back into session_state for the confirmation screen
            st.session_state.status     = progress.get('status', {})
            st.session_state.pdf_buffer = progress.get('pdf_buffer')
            # full_data may have been enriched (pdf_link added) by the thread
            st.session_state.full_data  = progress.get('full_data', full_data)
            st.session_state.submitted  = True
            print(f"SUBMISSION {sub_id}: UI detected completion, advancing to terminal state")
            st.rerun()
            return

        # ---- Live processing UI -----------------------------------------
        scroll_to_top()
        st.title("⏳ Processing Your Application")
        st.write(f"**Applicant:** {applicant_name}")
        st.info(f"**Reference ID:** {sub_id}")
        st.markdown("---")

        st.warning(
            "⚠️ **Submitting your application. This may take up to 30 seconds. "
            "Please do not close this window.**"
        )
        st.markdown("---")

        # Map step numbers to progress bar values and labels
        step = progress.get('step', 0) if progress else 0
        STEPS = [
            (0,    "Starting…"),
            (0.20, "✅ Starting"),
            (0.45, "✅ PDF generated — Saving to database…"),
            (0.75, "✅ Saved — Sending confirmation emails…"),
            (1.0,  "✅ Emails sent — Finalizing…"),
        ]
        bar_value, bar_label = STEPS[min(step, len(STEPS) - 1)]

        # Show completed steps as green ticks and current step as spinner text
        completed_labels = [STEPS[i][1] for i in range(1, step + 1)]
        for label in completed_labels:
            st.success(label)

        if step < len(STEPS) - 1:
            current_label = progress.get('step_label', 'Working…') if progress else 'Starting…'
            st.markdown(f"#### ⏳ {current_label}")

        st.progress(bar_value)

        # Show a spinner animation using CSS so the page feels alive
        st.markdown("""
<style>
@keyframes spin { to { transform: rotate(360deg); } }
.spinner {
    display: inline-block;
    width: 32px; height: 32px;
    border: 4px solid #e0e0e0;
    border-top-color: #1a73e8;
    border-radius: 50%;
    animation: spin 0.9s linear infinite;
    vertical-align: middle;
    margin-right: 10px;
}
</style>
<div style="text-align:center; padding: 20px 0;">
  <span class="spinner"></span>
  <span style="font-size:1.1rem; color:#555;">Processing, please wait…</span>
</div>
""", unsafe_allow_html=True)

        # Poll every 2 seconds by scheduling a rerun — this is non-blocking.
        time.sleep(2)
        st.rerun()


if __name__ == "__main__":
    main()
