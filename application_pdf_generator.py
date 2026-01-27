# application_pdf_generator.py
# PDF generation for job fair applications

import io
import os
import base64
import traceback

def sanitize_for_pdf(value):
    """Clean value for PDF field insertion"""
    if not isinstance(value, str):
        value = str(value)
    
    # Remove or replace problematic characters
    value = (
        value.replace("(", "[")
        .replace(")", "]")
        .replace("&", "and")
        .replace("\n", " / ")
        .replace("\r", "")
        .replace(":", "-")
        .replace("\"", "'")
        .replace("\\", "/")
        .replace("'", "'")  # Replace smart quotes
        .replace("'", "'")
        .replace(""", '"')
        .replace(""", '"')
        .replace("—", "-")  # Em dash
        .replace("–", "-")  # En dash
        .strip()
    )
    
    # Limit length to prevent overflow
    if len(value) > 500:
        value = value[:497] + "..."
    
    return value

def format_positions(positions):
    """Format positions dictionary into readable string"""
    position_list = []
    
    # Wilson Plant Co positions
    wpc_positions = []
    if positions.get('wpc_cashier'): wpc_positions.append("Cashier")
    if positions.get('wpc_greenhouse'): wpc_positions.append("Greenhouse")
    if positions.get('wpc_nursery'): wpc_positions.append("Nursery")
    if positions.get('wpc_waterer'): wpc_positions.append("Waterer/Production")
    if positions.get('wpc_admin'): wpc_positions.append("Administration")
    if wpc_positions:
        position_list.append("Wilson Plant Co: " + ", ".join(wpc_positions))
    
    # Landscaping positions
    land_positions = []
    if positions.get('land_designer'): land_positions.append("Designer")
    if positions.get('land_foreman'): land_positions.append("Foreman")
    if positions.get('land_installer'): land_positions.append("Installer")
    if land_positions:
        position_list.append("Landscaping: " + ", ".join(land_positions))
    
    # Cafe positions
    cafe_positions = []
    if positions.get('cafe_foh'): cafe_positions.append("Front-of-house")
    if positions.get('cafe_boh'): cafe_positions.append("Back-of-house")
    if positions.get('cafe_admin'): cafe_positions.append("Management")
    if cafe_positions:
        position_list.append("Sage Garden Cafe: " + ", ".join(cafe_positions))
    
    # Other
    if positions.get('other'):
        other_desc = positions.get('other_description', 'Not specified')
        position_list.append(f"Other: {other_desc}")
    
    return " | ".join(position_list) if position_list else "Not specified"

def generate_application_pdf(data):
    """Generate a filled PDF from the application data"""
    print(">>> Entering generate_application_pdf()")
    print(f">>> Applicant: {data.get('first_name')} {data.get('last_name')}")
    
    try:
        # Import here to avoid issues if libraries aren't available
        print(">>> Importing PDF libraries...")
        from pdfrw import PdfObject, PdfName, PdfReader, PdfWriter
        import fitz
        from PIL import Image
        print(">>> PDF libraries imported successfully")
        
        template_path = "application_template.pdf"
        
        # Check if template exists
        if not os.path.exists(template_path):
            print(f">>> ERROR: PDF template not found at {template_path}")
            print(">>> PDF generation skipped. Application will still be saved to Google Sheets.")
            return None
        
        print(f">>> PDF template found at {template_path}")
        
        filled_path = "/tmp/filled_application.pdf"
        output_buffer = io.BytesIO()
        
        ANNOT_KEY = "/Annots"
        ANNOT_FIELD_KEY = "/T"
        ANNOT_VAL_KEY = "/V"
        SUBTYPE_KEY = "/Subtype"
        WIDGET_SUBTYPE_KEY = "/Widget"
        
        print(">>> Preparing PDF data...")
        # Prepare data for PDF fields
        pdf_data = {
            # Basic info
            "first_name": data.get('first_name', ''),
            "last_name": data.get('last_name', ''),
            "email": data.get('email', ''),
            "phone": data.get('phone', ''),
            "alternate_phone": data.get('alternate_phone', ''),
            "dob": data.get('dob', ''),
            "street_address": data.get('street_address', ''),
            "city": data.get('city', ''),
            "state": data.get('state', ''),
            "zip": data.get('zip', ''),
            
            # Schedule
            "location": data.get('location', ''),
            "date": data.get('date', ''),
            "time_slot": data.get('time_slot', ''),
            
            # Position info
            "positions": format_positions(data.get('positions', {})),
            "schedule_preference": data.get('schedule_preference', ''),
            "expected_payrate": data.get('expected_payrate', ''),
            
            # Availability
            "availability_restrictions": data.get('availability_restrictions', ''),
            "start_date": data.get('start_date', ''),
            
            # About
            "why_applying": data.get('why_applying', ''),
            "special_training": data.get('special_training', ''),
            
            # Legal
            "legally_entitled": data.get('legally_entitled', ''),
            "perform_duties": data.get('perform_duties', ''),
            "drug_test": data.get('drug_test', ''),
            "background_check": data.get('background_check', ''),
            "drivers_license": data.get('drivers_license', ''),
            "reliable_transport": data.get('reliable_transport', ''),
            "submission_timestamp": data.get('submission_timestamp', ''),
            
            # Education
            "college_name": data.get('college_name', ''),
            "college_study": data.get('college_study', ''),
            "college_graduated": data.get('college_graduated', ''),
            "college_completion": data.get('college_completion', ''),
            "hs_name": data.get('hs_name', ''),
            "hs_study": data.get('hs_study', ''),
            "hs_graduated": data.get('hs_graduated', ''),
            "hs_completion": data.get('hs_completion', ''),
        }
        
        # Add individual employer fields (up to 3 employers)
        employers = data.get('employers', [])
        for i in range(3):
            emp_num = i + 1
            if i < len(employers):
                emp = employers[i]
                pdf_data[f"employer{emp_num}_name"] = emp.get('employer', '')
                pdf_data[f"employer{emp_num}_location"] = emp.get('location', '')
                pdf_data[f"employer{emp_num}_hire"] = emp.get('hire_date', '')
                pdf_data[f"employer{emp_num}_end"] = emp.get('end_date', '')
                pdf_data[f"employer{emp_num}_position"] = emp.get('position', '')
                pdf_data[f"employer{emp_num}_pay"] = emp.get('pay_rate', '')
                pdf_data[f"employer{emp_num}_reason"] = emp.get('reason', '')
            else:
                pdf_data[f"employer{emp_num}_name"] = ''
                pdf_data[f"employer{emp_num}_location"] = ''
                pdf_data[f"employer{emp_num}_hire"] = ''
                pdf_data[f"employer{emp_num}_end"] = ''
                pdf_data[f"employer{emp_num}_position"] = ''
                pdf_data[f"employer{emp_num}_pay"] = ''
                pdf_data[f"employer{emp_num}_reason"] = ''
        
        # Add individual reference fields (up to 3 references)
        references = data.get('references', [])
        for i in range(3):
            ref_num = i + 1
            if i < len(references):
                ref = references[i]
                pdf_data[f"reference{ref_num}_name"] = ref.get('name', '')
                pdf_data[f"reference{ref_num}_contact"] = ref.get('contact', '')
                pdf_data[f"reference{ref_num}_relationship"] = ref.get('relationship', '')
            else:
                pdf_data[f"reference{ref_num}_name"] = ''
                pdf_data[f"reference{ref_num}_contact"] = ''
                pdf_data[f"reference{ref_num}_relationship"] = ''
        
        print(">>> Reading PDF template...")
        # Read template and fill fields
        template_pdf = PdfReader(template_path)
        
        print(">>> Filling PDF fields...")
        field_count = 0
        for page in template_pdf.pages:
            annotations = page.get(ANNOT_KEY)
            if annotations:
                for annotation in annotations:
                    if annotation.get(SUBTYPE_KEY) == WIDGET_SUBTYPE_KEY:
                        key = annotation.get(ANNOT_FIELD_KEY)
                        if key:
                            key_name = str(key)[1:-1] if not isinstance(key, str) else key.strip("()")
                            if key_name in pdf_data:
                                value = sanitize_for_pdf(pdf_data[key_name])
                                annotation[PdfName("V")] = PdfObject(f"({value})")
                                field_count += 1
        
        print(f">>> Filled {field_count} PDF fields")
        
        print(">>> Writing filled PDF...")
        PdfWriter(filled_path, trailer=template_pdf).write()
        
        print(">>> Flattening PDF with fitz...")
        # Flatten and add signature
        doc = fitz.open(filled_path)
        
        # Add signature if present
        signature_base64 = data.get('signature_base64')
        signature_placed = False
        
        if signature_base64:
            print(">>> Adding signature to PDF...")
            try:
                sig_bytes = base64.b64decode(signature_base64)
                sig_img = Image.open(io.BytesIO(sig_bytes))
                sig_buffer = io.BytesIO()
                sig_img.save(sig_buffer, format='PNG')
                sig_buffer.seek(0)
                
                # Try to find signature field first
                for page_num, page in enumerate(doc):
                    widgets = page.widgets()
                    if widgets:
                        for widget in widgets:
                            if widget.field_name and 'signature' in widget.field_name.lower():
                                # Get widget rectangle
                                rect = widget.rect
                                if rect and rect.is_valid and not rect.is_empty:
                                    page.insert_image(rect, stream=sig_buffer.getvalue(), keep_proportion=True)
                                    signature_placed = True
                                    widget.field_flags |= 1 << 0  # Set ReadOnly
                                    widget.update()
                                    break
                    if signature_placed:
                        break
                
                # If no signature field found, place on last page at default location
                if not signature_placed:
                    page = doc[-1]
                    # Adjust these coordinates to match your PDF template
                    rect = fitz.Rect(100, 650, 300, 700)
                    
                    if rect and rect.is_valid and not rect.is_empty:
                        page.insert_image(rect, stream=sig_buffer.getvalue(), keep_proportion=True)
                        signature_placed = True
                
                print(f">>> Signature placed: {signature_placed}")
                
            except Exception as e:
                print(f">>> Could not add signature to PDF: {e}")
                print(traceback.format_exc())
        
        print(">>> Making all fields read-only...")
        # Make all fields read-only
        for page in doc:
            widgets = page.widgets()
            if widgets:
                for widget in widgets:
                    widget.update()
                    widget.field_flags |= 1 << 0  # Set ReadOnly
        
        print(">>> Saving final PDF to buffer...")
        doc.save(output_buffer, deflate=True)
        output_buffer.seek(0)
        
        print(">>> PDF generated successfully!")
        return output_buffer
        
    except ImportError as e:
        print(f">>> ERROR: Required PDF libraries not available: {e}")
        print(traceback.format_exc())
        print(">>> Application will be saved to Google Sheets without PDF generation.")
        return None
    except Exception as e:
        print(f">>> ERROR generating PDF: {e}")
        print(traceback.format_exc())
        return None