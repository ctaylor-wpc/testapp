================================================================================
JOB FAIR APPLICATION SYSTEM - SETUP & USAGE GUIDE
================================================================================

OVERVIEW
--------
This is a Streamlit-based application system for managing job fair registrations
and applications for Wilson Plant Co. + Sage Garden Cafe. The system allows
applicants to:
1. Register and schedule an interview time
2. Complete a full employment application
3. Provide digital signature
4. Automatically send data to Google Sheets and generate PDF applications

================================================================================
FILE STRUCTURE
================================================================================

Your repository should contain these files:

app.py                           - Main application file (UI and flow control)
application.py                   - Application form module
application_scheduling.py        - Scheduling module
application_pdf_generator.py     - PDF generation module
application_sheets_manager.py    - Google Sheets integration
application_notifications.py     - Email notification system
requirements.txt                 - Python dependencies
application_template.pdf         - PDF template (YOU MUST CREATE THIS)
.streamlit/secrets.toml         - Configuration secrets (create this folder/file)
README.txt                      - This file

================================================================================
SETUP INSTRUCTIONS
================================================================================

STEP 1: CREATE GOOGLE SHEET
----------------------------
1. Go to Google Sheets and create a new spreadsheet
2. Name it "Applications"
3. Create a worksheet named "2026"
4. Add these 61 column headers in row 1 (columns A through BI):

   A: First Name
   B: Last Name
   C: Email
   D: Phone
   E: Street Address
   F: City
   G: State
   H: Zip
   I: Interview Location
   J: Interview Date
   K: Interview Time
   L: Positions Applied For
   M: Hours Preferred
   N: Expected Payrate
   O: Why Applying
   P: Special Training/Skills
   Q: Legally Entitled to Work
   R: Can Perform Physical Duties
   S: Drug Test Willing
   T: Background Check Willing
   U: Valid Drivers License
   V: Reliable Transportation
   W: Submission Timestamp
   X: Employer 1 Name
   Y: Employer 1 Location
   Z: Employer 1 Hire Date
   AA: Employer 1 End Date
   AB: Employer 1 Position
   AC: Employer 1 Pay Rate
   AD: Employer 1 Reason for Leaving
   AE: Employer 2 Name
   AF: Employer 2 Location
   AG: Employer 2 Hire Date
   AH: Employer 2 End Date
   AI: Employer 2 Position
   AJ: Employer 2 Pay Rate
   AK: Employer 2 Reason for Leaving
   AL: Employer 3 Name
   AM: Employer 3 Location
   AN: Employer 3 Hire Date
   AO: Employer 3 End Date
   AP: Employer 3 Position
   AQ: Employer 3 Pay Rate
   AR: Employer 3 Reason for Leaving
   AS: College Name & City
   AT: College Area of Study
   AU: College Graduated
   AV: College Completion Date
   AW: High School Name & City
   AX: High School Area of Study
   AY: High School Graduated
   AZ: High School Completion Date
   BA: Reference 1 Name
   BB: Reference 1 Contact
   BC: Reference 1 Relationship
   BD: Reference 2 Name
   BE: Reference 2 Contact
   BF: Reference 2 Relationship
   BG: Reference 3 Name
   BH: Reference 3 Contact
   BI: Reference 3 Relationship

5. Note the Sheet ID from the URL (it's the long string between /d/ and /edit)
   The Sheet ID is already set to: 1QZ5gO5farg4E03dhaSINJljvn6qfocUgvHH4tjOSkIc
   
6. Share the sheet with your service account email:
   delivery-app-calendar-access@deliverycalculator-462121.iam.gserviceaccount.com
   Give it "Editor" permissions

STEP 2: CREATE PDF TEMPLATE
----------------------------
You must create a PDF file named "application_template.pdf" with form fields
that match the field names in the application_pdf_generator.py file.

The PDF should include these form fields (exact names):
- first_name
- last_name
- email
- street_address
- city
- state
- zip
- phone
- location
- date
- time_slot
- positions
- hours
- expected_payrate
- why_applying
- special_training
- legally_entitled
- perform_duties
- drug_test
- background_check
- drivers_license
- reliable_transport
- submission_timestamp
- employment_history
- college_name
- college_study
- college_graduated
- college_completion
- hs_name
- hs_study
- hs_graduated
- hs_completion
- references

You can create this PDF using:
- Adobe Acrobat Pro (recommended)
- PDFescape (free online tool)
- LibreOffice Draw with PDF forms
- Any PDF form editor

The signature will be placed automatically on the last page at coordinates
you can adjust in application_pdf_generator.py (currently set to rect(100, 650, 300, 700))

STEP 3: INSTALL DEPENDENCIES
-----------------------------
In your terminal/command prompt, navigate to your project directory and run:

pip install -r requirements.txt

STEP 4: CONFIGURE SECRETS
--------------------------
1. Create a folder named ".streamlit" in your project directory
2. Create a file named "secrets.toml" inside the .streamlit folder
3. Copy the contents from the secrets.toml template provided
4. Update the notify_email to where you want application notifications sent
5. Keep all other settings as-is (they're already configured for your organization)

STEP 5: MANAGE SCHEDULING AVAILABILITY
---------------------------------------
To grey out time slots as they fill up, edit application_scheduling.py:

Find the UNAVAILABLE_SLOTS dictionary (around line 17) and add time slots:

UNAVAILABLE_SLOTS = {
    'LEXINGTON': {
        '2026-02-18': ['10am-12pm'],  # This slot is now greyed out
        '2026-02-19': [],
        '2026-02-20': ['12pm-2pm', '2pm-4pm'],  # These two are greyed out
        '2026-02-21': []
    },
    'FRANKFORT': {
        '2026-02-18': [],
        '2026-02-19': ['10am-12pm'],
        '2026-02-20': [],
        '2026-02-21': []
    }
}

To change dates, locations, or time slots entirely, edit the SCHEDULING_CONFIG
dictionary at the top of application_scheduling.py.

================================================================================
RUNNING THE APPLICATION
================================================================================

1. Open terminal/command prompt
2. Navigate to your project directory
3. Run: streamlit run app.py
4. The app will open in your default web browser
5. Share the URL with job fair applicants

================================================================================
HOW THE APP WORKS
================================================================================

PHASE 1: Registration & Scheduling
-----------------------------------
1. Applicant enters basic info (name, email)
2. Applicant selects interview location (Lexington or Frankfort)
3. Applicant selects date and time slot
4. Greyed-out slots are unavailable
5. Click "Continue to Application"

PHASE 2: Application Form
--------------------------
1. Personal information (pre-filled from Phase 1)
2. Position preferences (checkboxes for different departments)
3. Hours and pay expectations
4. Legal questions (work authorization, background checks, etc.)
5. Digital signature
6. Employment history (optional, up to 3 employers)
7. Education (college and high school)
8. References (up to 3)
9. Click "Submit Application"

PHASE 3: Confirmation
----------------------
1. Application is saved to Google Sheets
2. PDF is generated
3. Email notification is sent with PDF attachment
4. Applicant can download their PDF
5. Confirmation message shows interview details

================================================================================
CUSTOMIZATION
================================================================================

CHANGING EMAIL SETTINGS
------------------------
Edit .streamlit/secrets.toml:
- notify_email: where notifications are sent
- sender_email/sender_password: outgoing email credentials

CHANGING INTERVIEW DATES
-------------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary:
    'dates': [
        {'display': 'Wednesday, February 18', 'value': '2026-02-18'},
        # Add or modify dates here
    ]

CHANGING LOCATIONS
-------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary:
    'locations': ['LEXINGTON', 'FRANKFORT']  # Modify as needed

CHANGING TIME SLOTS
--------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary:
    'time_slots': ['10am-12pm', '12pm-2pm', '2pm-4pm']  # Modify as needed

ADJUSTING SIGNATURE PLACEMENT IN PDF
-------------------------------------
Edit application_pdf_generator.py, around line 165:
    rect = fitz.Rect(100, 650, 300, 700)  # Adjust these coordinates

MODIFYING POSITION OPTIONS
---------------------------
Edit application.py, around lines 30-55, in the "Position Information" section

================================================================================
TROUBLESHOOTING
================================================================================

ERROR: "Service account JSON not found"
-----------------------------------------
Solution: Check that .streamlit/secrets.toml exists and has the correct format

ERROR: "Failed to send to Google Sheet"
-----------------------------------------
Solution: 
- Verify Sheet ID in application_sheets_manager.py
- Check that service account has Editor access to the sheet
- Verify worksheet name is exactly "2026"

ERROR: "Error generating PDF"
-------------------------------
Solution:
- Ensure application_template.pdf exists in project directory
- Check that PDF has properly named form fields
- Verify pdfrw and PyMuPDF are installed

ERROR: "Failed to send notification email"
-------------------------------------------
Solution:
- Check email credentials in secrets.toml
- Verify sender_password (app password) is correct
- Check that SMTP settings are correct for your email provider

APP RUNS BUT BUTTONS DON'T WORK
---------------------------------
Solution: Check browser console for JavaScript errors
- Try refreshing the page
- Clear browser cache
- Try a different browser

================================================================================
MAINTENANCE TIPS
================================================================================

1. BEFORE JOB FAIR:
   - Test the entire flow yourself
   - Verify all time slots are correctly marked as available/unavailable
   - Check that email notifications are arriving
   - Verify Google Sheet is receiving data correctly

2. DURING JOB FAIR:
   - Monitor the Google Sheet for new applications
   - Update UNAVAILABLE_SLOTS as slots fill up
   - Keep the app running continuously

3. AFTER JOB FAIR:
   - Download all applications from Google Sheet
   - Archive the data
   - Reset UNAVAILABLE_SLOTS for next year

================================================================================
SUPPORT
================================================================================

For issues or questions:
1. Check this README first
2. Review error messages carefully
3. Check Streamlit logs in terminal
4. Verify all configuration in secrets.toml
5. Contact your developer/IT support

================================================================================
NOTES
================================================================================

- The app uses your existing Google Cloud Platform service account
- All times are in the user's local timezone
- PDF signatures are stored as base64-encoded PNG images
- The app does not store any data locally - everything goes to Google Sheets
- Applications are processed immediately upon submission
- Each module is independent and can be reused in other projects

================================================================================
END OF README
================================================================================
