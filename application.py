# application.py
# Application for Employment form module
#
# CHANGES FROM ORIGINAL:
#   1. The submit button is disabled when session_state['form_submitted'] is
#      True.  This flag is set to True the instant the user clicks Submit and
#      is only cleared when reset_app() is called.  This prevents double
#      submissions from accidental double-clicks or page re-renders.
#   2. A clear "Submitting…" message replaces the button while processing,
#      so the user knows their click was registered.
#   3. Everything else is unchanged — validation, data compilation, and the
#      session_state handoff to app.py are identical to the original.

import streamlit as st
from streamlit_drawable_canvas import st_canvas
import datetime
import base64
import io
from PIL import Image


def render_application_form(first_name_prefill='', last_name_prefill='', email_prefill=''):
    """Render the complete application form and return data when submitted"""

    # Personal Information
    st.header("Personal Information")

    first_name = st.text_input("First Name *", value=first_name_prefill, key="app_first_name")
    last_name = st.text_input("Last Name *", value=last_name_prefill, key="app_last_name")
    email = st.text_input("Email Address *", value=email_prefill, key="app_email")
    phone = st.text_input("Phone Number *", key="phone")
    alternate_phone = st.text_input("Alternate Phone Number (optional)", key="alternate_phone")

    dob = st.text_input(
        "Date of Birth (MM/DD/YYYY - required if under 18) *",
        key="dob",
        placeholder="MM/DD/YYYY",
        help="Enter your date of birth in MM/DD/YYYY format (e.g., 03/15/1995)"
    )

    street_address = st.text_input("Street Address *", key="street_address")
    city = st.text_input("City *", key="city")
    state = st.text_input("State *", value="KY", key="state")
    zip_code = st.text_input("Zip *", key="zip")

    st.markdown("---")

    # Position Information
    st.header("Position Information")
    st.subheader("Which positions interest you?")
    st.write("Select all that apply. Hover over each position for details.")

    positions = {}

    st.markdown("**🌿 Wilson Plant Co.**")
    positions['wpc_cashier'] = st.checkbox(
        "Cashier",
        key="pos_wpc_cashier",
        help="Process sales, assist customers, handle cash and card transactions"
    )
    positions['wpc_greenhouse'] = st.checkbox(
        "Greenhouse Associate (Annuals, Perennials, & Houseplants)",
        key="pos_wpc_greenhouse",
        help="Assist customers, maintain plant displays, water and care for greenhouse plants"
    )
    positions['wpc_nursery'] = st.checkbox(
        "Nursery Associate (Trees & Shrubs)",
        key="pos_wpc_nursery",
        help="Help customers select trees and shrubs, load materials, maintain outdoor displays"
    )
    positions['wpc_waterer'] = st.checkbox(
        "Production/Waterer (Growing Greenhouses)",
        key="pos_wpc_waterer",
        help="Water plants, transplant, maintain growing areas, assist with plant production"
    )
    positions['wpc_admin'] = st.checkbox(
        "Administration (Marketing, Accounting, & HR)",
        key="pos_wpc_admin",
        help="Office support, marketing tasks, bookkeeping, HR assistance"
    )

    st.markdown("**🏡 Landscaping**")
    positions['land_designer'] = st.checkbox(
        "Designer",
        key="pos_land_designer",
        help="Create landscape designs, meet with clients, develop planting plans"
    )
    positions['land_foreman'] = st.checkbox(
        "Foreman",
        key="pos_land_foreman",
        help="Lead installation crews, manage projects, coordinate schedules"
    )
    positions['land_installer'] = st.checkbox(
        "Installer",
        key="pos_land_installer",
        help="Plant installation, hardscape work, outdoor construction and maintenance"
    )

    st.markdown("**☕ Sage Garden Cafe**")
    positions['cafe_foh'] = st.checkbox(
        "Front-of-House (Server, Cashier, Barista)",
        key="pos_cafe_foh",
        help="Take orders, serve customers, prepare beverages, handle payments"
    )
    positions['cafe_boh'] = st.checkbox(
        "Back-of-House (Cook, Dishwasher)",
        key="pos_cafe_boh",
        help="Food preparation, cooking, dishwashing, kitchen maintenance"
    )
    positions['cafe_admin'] = st.checkbox(
        "Management",
        key="pos_cafe_admin",
        help="Supervise staff, manage operations, scheduling, inventory management"
    )

    positions['other'] = st.checkbox("Something else", key="pos_other")
    if positions['other']:
        positions['other_description'] = st.text_input("Please describe:", key="pos_other_desc")

    st.markdown("---")

    # Hours
    st.subheader("Work Schedule Preference")

    schedule_type = st.radio(
        "What type of schedule are you looking for?",
        ["Part-time (under 30 hours/week)", "Full-time (30+ hours/week)"],
        key="schedule_type"
    )

    if "Part-time" in schedule_type:
        hours_detail = st.selectbox(
            "How many hours per week?",
            ["15-20 hours", "20-25 hours", "25-30 hours", "Flexible/Open"],
            key="hours_detail"
        )
    else:
        hours_detail = st.selectbox(
            "How many hours per week?",
            ["30-35 hours", "35-40 hours", "40+ hours", "Flexible/Open"],
            key="hours_detail"
        )

    hours_15_25  = "Part-time" in schedule_type and ("15-20" in hours_detail or "20-25" in hours_detail)
    hours_30_40  = "Full-time" in schedule_type and ("30-35" in hours_detail or "35-40" in hours_detail)
    hours_40_plus = "Full-time" in schedule_type and "40+" in hours_detail

    st.markdown("---")

    expected_payrate = st.text_input(
        "Based on your skills, education, and experience, what pay rate would you expect? *",
        key="expected_payrate",
        placeholder="e.g., $15/hour or $35,000/year",
        help="Please provide a specific hourly rate or annual salary"
    )

    payrate_error = False
    if expected_payrate:
        payrate_lower = expected_payrate.lower().strip()
        forbidden_terms = ['negotiable', 'willing to discuss', 'open to discussion', 'flexible', 'open']
        if any(term in payrate_lower for term in forbidden_terms):
            st.error("Please provide a specific pay rate rather than 'negotiable' or similar. We understand pay is flexible, but need a starting point for discussion.")
            payrate_error = True

    st.markdown("---")

    # Availability
    st.header("Availability")

    availability_restrictions = st.text_area(
        "Are there any days or times you would NOT be available for work?",
        key="availability_restrictions",
        height=100,
        placeholder="e.g., 'Not available Sundays' or 'Cannot work before 3pm on weekdays'",
        help="Let us know any scheduling restrictions you have"
    )

    start_date = st.text_input(
        "If hired, when would you be available to start? *",
        key="start_date",
        placeholder="e.g., 'Immediately', 'Two weeks notice required', or a specific date",
        help="When can you begin working?"
    )

    st.markdown("---")

    # About You
    st.header("About You")

    why_applying = st.text_area(
        "Briefly state why you are applying. *",
        key="why_applying",
        height=100,
        placeholder="What interests you about this position?"
    )

    special_training = st.text_area(
        "Do you have any special training, education, skills, or personal passions that are relevant?",
        key="special_training",
        height=100,
        placeholder="e.g., horticulture degree, food service certification, landscape design experience"
    )

    st.markdown("---")

    # Legal Information
    st.header("Legal Information")

    legally_entitled = st.radio(
        "Are you legally entitled to work in the U.S.? *",
        ["Yes", "No"],
        key="legally_entitled"
    )

    perform_duties = st.radio(
        "This job requires physical duties such as bending, lifting, and extended standing in all weather conditions. If hired, would you be able to perform the essential duties of this position with or without reasonable accommodations? *",
        ["Yes", "No"],
        key="perform_duties"
    )

    drug_test = st.radio(
        "Are you willing to submit to a drug test? *",
        ["Yes", "No"],
        key="drug_test"
    )

    background_check = st.radio(
        "Are you willing to submit to a background check? *",
        ["Yes", "No"],
        key="background_check"
    )

    drivers_license = st.radio(
        "Do you have a valid drivers license? *",
        ["Yes", "No"],
        key="drivers_license"
    )

    reliable_transport = st.radio(
        "Do you have reliable transportation to and from work? *",
        ["Yes", "No"],
        key="reliable_transport"
    )

    st.markdown("---")

    # Signature
    st.header("Signature")
    st.markdown("""
    I agree that all statements are true and I understand that any falsification or willful omission
    is sufficient cause for dismissal or refusal of employment. I understand that this application is
    not a contractual agreement and by signing I agree that work at Wilson Nurseries, Inc. or Sage Garden Cafe, LLC
    may be terminated at any time by either party. This waiver does not permit the release or use of disability
    or medical information in a manner prohibited by the Americans with Disabilities Act (ADA) and other relevant
    federal and state laws.

    **Please sign below:**
    """)

    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=2,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=133,
        width=400,
        drawing_mode="freedraw",
        key="legal_signature_canvas"
    )

    st.markdown("---")

    # Employment History
    st.header("Employment History")
    st.info("This section is optional but recommended")

    if 'num_employers' not in st.session_state:
        st.session_state.num_employers = 1

    employers = []
    for i in range(st.session_state.num_employers):
        if i == 0:
            st.subheader("Most Recent Employer")
        else:
            st.subheader(f"Employer {i + 1}")

        employer  = st.text_input("Employer Name:", key=f"employer_{i}")
        location  = st.text_input("Location (City/State):", key=f"location_{i}")

        col1, col2 = st.columns(2)
        with col1:
            hire_date = st.text_input("Hire Date (MM/YYYY):", key=f"hire_date_{i}", placeholder="MM/YYYY")
        with col2:
            end_date  = st.text_input("End Date (MM/YYYY):", key=f"end_date_{i}", placeholder="MM/YYYY")

        col1, col2 = st.columns(2)
        with col1:
            position = st.text_input("Position/Title:", key=f"position_{i}")
        with col2:
            pay_rate = st.text_input("Pay Rate:", key=f"pay_rate_{i}", placeholder="e.g., $15/hr")

        reason = st.text_input("Reason for Leaving:", key=f"reason_{i}")

        employers.append({
            'employer': employer,
            'location': location,
            'hire_date': hire_date,
            'end_date': end_date,
            'position': position,
            'pay_rate': pay_rate,
            'reason': reason,
        })

        st.markdown("---")

    if st.session_state.num_employers < 3:
        if st.button("Add Another Employer", use_container_width=True):
            st.session_state.num_employers += 1
            st.rerun()

    # Educational Background
    st.header("Educational Background")

    st.subheader("College")
    college_name      = st.text_input("College Name & City:", key="college_name")
    college_study     = st.text_input("Area of Study:", key="college_study")
    college_graduated = st.radio("Graduated:", ["Yes", "No"], key="college_graduated", horizontal=True)
    college_completion = st.text_input("Completion Date:", key="college_completion", placeholder="MM/YYYY")

    st.markdown("---")

    st.subheader("High School")
    hs_name       = st.text_input("High School Name & City:", key="hs_name")
    hs_study      = st.text_input("Area of Study:", key="hs_study")
    hs_graduated  = st.radio("Graduated:", ["Yes", "No"], key="hs_graduated", horizontal=True)
    hs_completion = st.text_input("Completion Date:", key="hs_completion", placeholder="MM/YYYY")

    st.markdown("---")

    # Personal References
    st.header("Personal References")

    if 'num_references' not in st.session_state:
        st.session_state.num_references = 1

    references = []
    for i in range(st.session_state.num_references):
        st.subheader(f"Reference {i + 1}")
        ref_name         = st.text_input("Reference Name:", key=f"ref_name_{i}")
        ref_contact      = st.text_input("Phone Number or Email Address:", key=f"ref_contact_{i}")
        ref_relationship = st.text_input("Relationship:", key=f"ref_relationship_{i}", placeholder="e.g., Former supervisor, colleague, professor")

        references.append({
            'name': ref_name,
            'contact': ref_contact,
            'relationship': ref_relationship,
        })

        st.markdown("---")

    if st.session_state.num_references < 3:
        if st.button("Add Another Reference", use_container_width=True):
            st.session_state.num_references += 1
            st.rerun()

    # ------------------------------------------------------------------
    # SUBMIT BUTTON — with duplicate-submission protection
    # ------------------------------------------------------------------

    # If the form has already been submitted this session, show a "please
    # wait" message instead of the button.  This prevents the user from
    # clicking Submit a second time while the background thread is running.
    if st.session_state.get('form_submitted'):
        st.info("⏳ Your application is being submitted. Please do not click again or close this page.")
        return None

    if st.button(
        "Submit Application",
        type="primary",
        use_container_width=True,
        # Streamlit's `disabled` kwarg is the cleanest way to grey out the
        # button.  We pass the flag here as a belt-and-suspenders guard
        # (the early-return above is the primary guard).
        disabled=st.session_state.get('form_submitted', False),
    ):
        # ---- Validate required fields ----
        required_fields = [
            first_name, last_name, email, street_address, city, state,
            zip_code, phone, expected_payrate, start_date, why_applying, dob
        ]

        if not all(required_fields):
            st.error("Please fill in all required fields marked with *")
            return None

        if payrate_error:
            st.error("Please correct the expected payrate field")
            return None

        # ---- Validate signature ----
        has_signature    = False
        signature_base64 = None
        if canvas_result.image_data is not None:
            import numpy as np
            if np.any(canvas_result.image_data[:, :, 3] > 0):
                has_signature = True
                sig_img    = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                sig_buffer = io.BytesIO()
                sig_img.save(sig_buffer, format='PNG')
                sig_buffer.seek(0)
                signature_base64 = base64.b64encode(sig_buffer.getvalue()).decode('utf-8')

        if not has_signature:
            st.error("Please provide your signature")
            return None

        # ---- All validation passed: lock the button immediately ----
        # Setting this flag before st.rerun() means the button will be
        # rendered as disabled (or replaced by the info message) on all
        # future renders of this form, preventing double-submission.
        st.session_state.form_submitted = True

        submission_timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        schedule_preference  = f"{schedule_type} - {hours_detail}"

        application_data = {
            'first_name':               first_name,
            'last_name':                last_name,
            'email':                    email,
            'phone':                    phone,
            'alternate_phone':          alternate_phone,
            'dob':                      dob,
            'street_address':           street_address,
            'city':                     city,
            'state':                    state,
            'zip':                      zip_code,
            'positions':                positions,
            'schedule_preference':      schedule_preference,
            'hours_15_25':              hours_15_25,
            'hours_30_40':              hours_30_40,
            'hours_40_plus':            hours_40_plus,
            'expected_payrate':         expected_payrate,
            'availability_restrictions': availability_restrictions,
            'start_date':               start_date,
            'why_applying':             why_applying,
            'special_training':         special_training,
            'legally_entitled':         legally_entitled,
            'perform_duties':           perform_duties,
            'drug_test':                drug_test,
            'background_check':         background_check,
            'drivers_license':          drivers_license,
            'reliable_transport':       reliable_transport,
            'submission_timestamp':     submission_timestamp,
            'employers':                employers,
            'college_name':             college_name,
            'college_study':            college_study,
            'college_graduated':        college_graduated,
            'college_completion':       college_completion,
            'hs_name':                  hs_name,
            'hs_study':                 hs_study,
            'hs_graduated':             hs_graduated,
            'hs_completion':            hs_completion,
            'references':               references,
            'signature_base64':         signature_base64,
            # scheduling fields (populated by application_scheduling if active)
            'location':                 st.session_state.get('selected_location', ''),
            'date':                     st.session_state.get('selected_date_value', ''),
            'time_slot':                st.session_state.get('selected_time', ''),
        }

        # Hand data to app.py via session_state and trigger the phase flip
        st.session_state.pending_application   = application_data
        st.session_state.form_ready_to_process = True
        st.rerun()

    return None
