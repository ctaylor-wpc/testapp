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

This application can run on BOTH Streamlit Cloud and Render.

================================================================================
FILE STRUCTURE
================================================================================

Your repository should contain these files:

app.py - Main application file (UI and flow control)
application.py - Application form module
application_scheduling.py - Scheduling module
application_pdf_generator.py - PDF generation module
application_sheets_manager.py - Google Sheets integration
application_notifications.py - Email notification system
secrets.py - Centralized secrets management (NEW - handles both Streamlit & Render)
requirements.txt - Python dependencies
application_template.pdf - PDF template (YOU MUST CREATE THIS)
.streamlit/secrets.toml - Configuration secrets for Streamlit Cloud
README.txt - This file

================================================================================
SETUP INSTRUCTIONS
================================================================================

STEP 1: CREATE GOOGLE SHEET
----------------------------
1. Go to Google Sheets and create a new spreadsheet in your Shared Drive
2. Name it "Applications"
3. Create a worksheet named "2026"
4. Add these 66 column headers in row 1 (columns A through BN):

A: First Name
B: Last Name
C: Email
D: Phone
E: Alternate Phone
F: Date of Birth
G: Street Address
H: City
I: State
J: Zip
K: Interview Location
L: Interview Date
M: Interview Time
N: Positions Applied For
O: Hours Preferred
P: Expected Payrate
Q: Availability Restrictions
R: Available to Start
S: Why Applying
T: Special Training/Skills
U: Legally Entitled to Work
V: Can Perform Physical Duties
W: Drug Test Willing
X: Background Check Willing
Y: Valid Drivers License
Z: Reliable Transportation
AA: Submission Timestamp
AB: Employer 1 Name
AC: Employer 1 Location
AD: Employer 1 Hire Date
AE: Employer 1 End Date
AF: Employer 1 Position
AG: Employer 1 Pay Rate
AH: Employer 1 Reason for Leaving
AI: Employer 2 Name
AJ: Employer 2 Location
AK: Employer 2 Hire Date
AL: Employer 2 End Date
AM: Employer 2 Position
AN: Employer 2 Pay Rate
AO: Employer 2 Reason for Leaving
AP: Employer 3 Name
AQ: Employer 3 Location
AR: Employer 3 Hire Date
AS: Employer 3 End Date
AT: Employer 3 Position
AU: Employer 3 Pay Rate
AV: Employer 3 Reason for Leaving
AW: College Name & City
AX: College Area of Study
AY: College Graduated
AZ: College Completion Date
BA: High School Name & City
BB: High School Area of Study
BC: High School Graduated
BD: High School Completion Date
BE: Reference 1 Name
BF: Reference 1 Contact
BG: Reference 1 Relationship
BH: Reference 2 Name
BI: Reference 2 Contact
BJ: Reference 2 Relationship
BK: Reference 3 Name
BL: Reference 3 Contact
BM: Reference 3 Relationship
BN: PDF Link

5. Note the Sheet ID from the URL (it's the long string between /d/ and /edit)
   The Sheet ID is already set to: 1QZ5gO5farg4E03dhaSINJljvn6qfocUgvHH4tjOSkIc

6. Make sure the sheet is in a Shared Drive (not "My Drive")

7. Share the Shared Drive with your service account email:
   delivery-app-calendar-access@deliverycalculator-462121.iam.gserviceaccount.com
   Give it "Content Manager" or "Manager" permissions on the Shared Drive

8. Create a folder in your Shared Drive for PDF storage
   The PDF Folder ID is already set to: 1X5crtAwvuIgmgrGOSUR9M1gq21e0oUwh
   Make sure the service account has access to this folder too

STEP 2: CREATE PDF TEMPLATE
----------------------------
You must create a PDF file named "application_template.pdf" with form fields
that match the field names in the application_pdf_generator.py file.

The PDF should include these form fields (exact names):
- first_name
- last_name
- email
- phone
- alternate_phone
- dob
- street_address
- city
- state
- zip
- location
- date
- time_slot
- positions
- schedule_preference
- expected_payrate
- availability_restrictions
- start_date
- why_applying
- special_training
- legally_entitled
- perform_duties
- drug_test
- background_check
- drivers_license
- reliable_transport
- submission_timestamp
- employer1_name, employer1_location, employer1_hire, employer1_end, employer1_position, employer1_pay, employer1_reason
- employer2_name, employer2_location, employer2_hire, employer2_end, employer2_position, employer2_pay, employer2_reason
- employer3_name, employer3_location, employer3_hire, employer3_end, employer3_position, employer3_pay, employer3_reason
- college_name
- college_study
- college_graduated
- college_completion
- hs_name
- hs_study
- hs_graduated
- hs_completion
- reference1_name, reference1_contact, reference1_relationship
- reference2_name, reference2_contact, reference2_relationship
- reference3_name, reference3_contact, reference3_relationship

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

*** SEE README_private.txt for the full instructions for this section ***


STEP 5: MANAGE SCHEDULING AVAILABILITY
---------------------------------------
To grey out time slots as they fill up, edit application_scheduling.py:

Find the UNAVAILABLE_SLOTS dictionary (around line 35) and add time slots:

UNAVAILABLE_SLOTS = {
    '2026-02-18': ['10am-12pm'],  # This slot is now greyed out
    '2026-02-19': [],
    '2026-02-20': ['12pm-2pm', '2pm-4pm'],  # These two are greyed out
    '2026-02-21': []
}

NOTE: The dates are now tied to specific locations:
- Feb 18 & 19 are LEXINGTON only
- Feb 20 & 21 are FRANKFORT only

This is configured in the SCHEDULING_CONFIG at the top of application_scheduling.py.

================================================================================
RUNNING THE APPLICATION
================================================================================

*** LOCALLY (FOR TESTING) ***

1. Open terminal/command prompt
2. Navigate to your project directory
3. Run: streamlit run app.py
4. The app will open in your default web browser

*** ON STREAMLIT CLOUD ***

1. Push your code to GitHub
2. Go to share.streamlit.io
3. Deploy from your GitHub repository
4. Add secrets in the Streamlit Cloud dashboard under app settings
5. Your app will be live at your-app-name.streamlit.app

*** ON RENDER ***

1. Push your code to GitHub
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Set build command: pip install -r requirements.txt
5. Set start command: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
6. Add all environment variables listed in STEP 4 above
7. Deploy

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
3. PDF is uploaded to Google Drive
4. Email notification is sent to company with PDF attachment
5. Confirmation email is sent to applicant
6. Applicant can download their PDF
7. Confirmation message shows interview details

================================================================================
CUSTOMIZATION
================================================================================

CHANGING EMAIL SETTINGS
------------------------
Streamlit Cloud: Edit .streamlit/secrets.toml [email] section
Render: Update EMAIL_* environment variables

CHANGING GOOGLE SHEETS/DRIVE SETTINGS
--------------------------------------
Streamlit Cloud: Edit .streamlit/secrets.toml [gcp] section
Render: Update GCP_* environment variables

CHANGING INTERVIEW DATES
-------------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary:
'dates': [
    {'display': 'Wednesday, February 18', 'value': '2026-02-18'},
    # Add or modify dates here
]

CHANGING LOCATIONS
------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary - update location
and address fields in the dates array

CHANGING TIME SLOTS
-------------------
Edit application_scheduling.py, SCHEDULING_CONFIG dictionary:
'time_slots': ['10am-12pm', '12pm-2pm', '2pm-4pm']  # Modify as needed

ADJUSTING SIGNATURE PLACEMENT IN PDF
-------------------------------------
Edit application_pdf_generator.py, around line 232:
rect = fitz.Rect(100, 650, 300, 700)  # Adjust these coordinates

MODIFYING POSITION OPTIONS
---------------------------
Edit application.py, around lines 30-80, in the "Position Information" section

================================================================================
ARCHITECTURE - HOW SECRETS WORK
================================================================================

The app uses a centralized secrets management system (secrets.py) that 
automatically detects whether it's running on Streamlit Cloud or Render:

1. STREAMLIT CLOUD: Reads from st.secrets (populated from secrets.toml)
2. RENDER: Reads from environment variables (set in Render dashboard)

All other modules import from secrets.py, so they work on both platforms
without any code changes.

Files that access secrets:
- application_notifications.py: Imports get_email_config()
- application_sheets_manager.py: Imports get_gcp_service_account(), get_sheet_config()

The secrets.py file automatically converts between the two formats:
- Streamlit uses nested dictionaries: st.secrets["email"]["smtp_server"]
- Render uses flat env vars: EMAIL_SMTP_SERVER

================================================================================
TROUBLESHOOTING
================================================================================

ERROR: "Service account JSON not found"
----------------------------------------
Streamlit: Check that .streamlit/secrets.toml exists and has [gcp] section
Render: Check that GCP_SERVICE_ACCOUNT_JSON environment variable is set

ERROR: "Failed to send to Google Sheet"
----------------------------------------
Solution:
- Verify Sheet ID in secrets configuration
- Check that service account has Editor access to the Shared Drive
- Verify worksheet name is exactly "2026"
- Ensure the sheet is in a Shared Drive, not "My Drive"

ERROR: "Error generating PDF"
------------------------------
Solution:
- Ensure application_template.pdf exists in project directory
- Check that PDF has properly named form fields
- Verify pdfrw and PyMuPDF are installed

ERROR: "Failed to send notification email"
------------------------------------------
Solution:
- Check email credentials in secrets
- Verify sender_password (app password) is correct
- Check that SMTP settings are correct for your email provider
- For Gmail, ensure "App Passwords" is enabled

ERROR: "Failed to upload PDF to Google Drive"
----------------------------------------------
Solution:
- Verify PDF_FOLDER_ID in secrets
- Check that service account has access to the folder
- Ensure the folder is in a Shared Drive
- Verify the service account has "Content Manager" role

APP RUNS BUT BUTTONS DON'T WORK
--------------------------------
Solution: Check browser console for JavaScript errors
- Try refreshing the page
- Clear browser cache
- Try a different browser

RENDER: "Module not found" error
---------------------------------
Solution:
- Verify all packages are in requirements.txt
- Check build logs in Render dashboard
- Ensure Python version is compatible (3.9+)

RENDER: App won't start
-----------------------
Solution:
- Check that start command includes --server.port=$PORT
- Verify all environment variables are set
- Check application logs in Render dashboard

================================================================================
MAINTENANCE TIPS
================================================================================

1. BEFORE JOB FAIR:
   - Test the entire flow yourself on both platforms
   - Verify all time slots are correctly marked as available/unavailable
   - Check that email notifications are arriving
   - Verify Google Sheet is receiving data correctly
   - Test PDF generation and download

2. DURING JOB FAIR:
   - Monitor the Google Sheet for new applications
   - Update UNAVAILABLE_SLOTS as slots fill up
   - Keep the app running continuously
   - Monitor for any error emails or notifications

3. AFTER JOB FAIR:
   - Download all applications from Google Sheet
   - Download all PDFs from Google Drive folder
   - Archive the data
   - Reset UNAVAILABLE_SLOTS for next year
   - Consider clearing old data from the sheet

================================================================================
SECURITY BEST PRACTICES
================================================================================

1. NEVER commit secrets.toml to Git
   - Add .streamlit/secrets.toml to .gitignore
   - Only store secrets in Streamlit Cloud dashboard or Render env vars

2. Rotate passwords periodically
   - Update email app password annually
   - Generate new GCP service account keys if needed

3. Monitor access logs
   - Check Google Sheet access logs
   - Review email sent logs
   - Monitor for unusual activity

4. Keep dependencies updated
   - Regularly update requirements.txt
   - Test after updates

================================================================================
SUPPORT
================================================================================

For issues or questions:
1. Check this README first
2. Review error messages carefully
3. Check application logs (Streamlit/Render dashboard)
4. Verify all configuration in secrets
5. Test locally before deploying
6. Contact your developer/IT support

================================================================================
NOTES
================================================================================

- The app uses your existing Google Cloud Platform service account
- All times are displayed in the user's local timezone
- PDF signatures are stored as base64-encoded PNG images
- The app does not store any data locally - everything goes to Google Sheets
- Applications are processed immediately upon submission
- Each module is independent and can be reused in other projects
- The secrets.py module provides seamless multi-platform deployment
- PDFs are stored permanently in Google Drive for record-keeping

================================================================================
VERSION HISTORY
================================================================================

v2.0 (Current)
- Added centralized secrets management (secrets.py)
- Added support for Render deployment
- Improved error handling for missing secrets
- Enhanced PDF template file checking
- Updated documentation for multi-platform deployment

v1.0 (Initial)
- Streamlit Cloud only deployment
- Basic job fair registration and application system
- Google Sheets integration
- PDF generation with signatures
- Email notifications

================================================================================
END OF README
================================================================================
