# app.py
# Main application file with signature capture and load existing install features

import streamlit as st
import googlemaps
import io
import re
import math
import datetime
from streamlit_drawable_canvas import st_canvas

# Import from our modules
from config import *
from sheets_manager import send_to_dashboard, save_install_state, load_install_states, get_install_by_id
from pdf_generator import generate_pdf, upload_pdf_to_drive


# STEP 0: Initialize session state and configuration
def initialize_app():
    """Initialize the Streamlit app with session state variables"""
    if 'phase' not in st.session_state:
        st.session_state.phase = 1
    if 'step' not in st.session_state:
        st.session_state.step = 'A'
    if 'plant_count' not in st.session_state:
        st.session_state.plant_count = 1
    if 'plants' not in st.session_state:
        st.session_state.plants = {}
    if 'install_id' not in st.session_state:
        st.session_state.install_id = None
    if 'editing_existing' not in st.session_state:
        st.session_state.editing_existing = False


def clear_all_data():
    """Clear all session state data to restart the app"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_app()


def load_existing_install(install_data):
    """Load an existing install into session state"""
    st.session_state.plants = install_data['plants_data']
    st.session_state.installation_data = install_data['installation_data']
    st.session_state.customer_data = install_data['customer_data']
    st.session_state.pricing_data = install_data['pricing_data']
    st.session_state.install_id = install_data['install_id']
    st.session_state.plant_count = len(install_data['plants_data'])
    st.session_state.editing_existing = True
    st.session_state.phase = 1
    st.session_state.step = 'B'


# STEP 1: Input validation and character cleaning functions
def clean_text_input(text_input):
    """Remove problematic characters from text input"""
    try:
        if text_input is None:
            return ""
        cleaned = re.sub(r'["\'\!\@\#\$\%\^\&\*\(\)]', '', str(text_input))
        return cleaned.strip()
    except Exception as e:
        st.error(f"Error cleaning text input: {e}")
        return ""


def validate_numeric_input(value, field_name):
    """Validate and convert numeric inputs"""
    try:
        if value is None or value == "":
            return 0
        return float(value)
    except ValueError:
        st.error(f"Invalid numeric value for {field_name}")
        return 0


# STEP 2: Plant size and mulch lookup tables
def get_mulch_soil_tablet_quantities(plant_size, mulch_type, quantity):
    """Calculate mulch, soil conditioner, and tablet quantities based on plant size and type"""
    try:
        if plant_size not in PLANT_SIZE_DATA:
            st.error(f"Unknown plant size: {plant_size}")
            return 0, 0, 0
            
        base_data = PLANT_SIZE_DATA[plant_size]
        
        # Determine mulch column based on category
        if mulch_type in MULCH_CATEGORIES["category_a"]:
            mulch_base = base_data["mulch"][0]
        elif mulch_type in MULCH_CATEGORIES["category_b"]:
            mulch_base = base_data["mulch"][1]
        elif mulch_type in MULCH_CATEGORIES["category_c"]:
            mulch_base = base_data["mulch"][2]
        else:
            st.error(f"Unknown mulch type: {mulch_type}")
            return 0, 0, 0
            
        # Calculate totals for this plant
        mulch_quantity = mulch_base * quantity
        soil_quantity = base_data["soil"] * quantity
        tablet_quantity = base_data["tablets"] * quantity
        
        return mulch_quantity, soil_quantity, tablet_quantity
        
    except Exception as e:
        st.error(f"Error calculating quantities: {e}")
        return 0, 0, 0


# STEP 3: Google Maps API integration for distance calculation
def calculate_driving_distance(origin, destination):
    """Calculate driving distance using Google Maps API"""
    try:
        api_key = st.secrets["api"]["google_maps_api_key"]
        if not api_key:
            st.error("Google Maps API key not found in secrets")
            return 0
            
        gmaps = googlemaps.Client(key=api_key)
        
        result = gmaps.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode="driving",
            units="imperial"
        )
        
        if result['status'] == 'OK':
            distance_text = result['rows'][0]['elements'][0]['distance']['text']
            distance_miles = float(re.findall(r'\d+\.?\d*', distance_text)[0])
            return distance_miles
        else:
            st.error("Could not calculate distance")
            return 0
            
    except Exception as e:
        st.error(f"Error calculating distance: {e}")
        return 0


# STEP 4: Pricing calculations
def calculate_pricing(plants_data, installation_data):
    """Calculate all pricing components"""
    try:
        plant_material_total = 0
        plant_material_discount_total = 0
        total_mulch_quantity = 0
        total_soil_quantity = 0
        total_tablet_quantity = 0
        
        # Process each plant
        for plant_id, plant in plants_data.items():
            quantity = validate_numeric_input(plant.get('quantity', 0), f"Plant {plant_id} quantity")
            price = validate_numeric_input(plant.get('price', 0), f"Plant {plant_id} price")
            discount_percent = validate_numeric_input(plant.get('discount_percent', 0), f"Plant {plant_id} discount percent")
            discount_dollars = validate_numeric_input(plant.get('discount_dollars', 0), f"Plant {plant_id} discount dollars")
            
            plant_total = price * quantity
            plant_material_total += plant_total
            
            discounted_price = price * (1 - discount_percent / 100) - discount_dollars
            plant_material_discount_total += discounted_price * quantity
            
            plant_size = plant.get('size', '')
            mulch_type = installation_data.get('mulch_type', '')
            
            mulch_qty, soil_qty, tablet_qty = get_mulch_soil_tablet_quantities(plant_size, mulch_type, quantity)
            
            total_mulch_quantity += mulch_qty
            total_soil_quantity += soil_qty
            total_tablet_quantity += tablet_qty
        
        total_mulch_quantity = math.ceil(total_mulch_quantity)
        total_soil_quantity = math.ceil(total_soil_quantity)
        total_tablet_quantity = math.ceil(total_tablet_quantity)
        
        # Get pricing from config
        tablet_unit_price = INSTALL_MATERIALS_PRICING["tablet_unit_price"]
        soil_conditioner_unit_price = INSTALL_MATERIALS_PRICING["soil_conditioner_unit_price"]
        deer_guard_unit_price = INSTALL_MATERIALS_PRICING["deer_guard_unit_price"]
        tree_stake_unit_price = INSTALL_MATERIALS_PRICING["tree_stake_unit_price"]
        
        # Get mulch pricing and SKU
        mulch_type = installation_data.get('mulch_type', '')
        mulch_info = MULCH_CONFIG.get(mulch_type, DEFAULT_MULCH)
        mulch_unit_price = mulch_info["price"]
        mulch_sku = mulch_info["sku"]
        
        # Calculate installation material costs
        tablet_total_price = total_tablet_quantity * tablet_unit_price
        mulch_total_price = total_mulch_quantity * mulch_unit_price
        soil_conditioner_total_price = total_soil_quantity * soil_conditioner_unit_price
        deer_guard_price = validate_numeric_input(installation_data.get('deer_guards_quantity', 0), 'deer guards') * deer_guard_unit_price
        tree_stakes_price = validate_numeric_input(installation_data.get('tree_stakes_quantity', 0), 'tree stakes') * tree_stake_unit_price
        
        installation_material_total = tablet_total_price + mulch_total_price + soil_conditioner_total_price + deer_guard_price + tree_stakes_price
        
        # Installation cost multiplier
        installation_type = installation_data.get('installation_type', '')
        install_multiplier = INSTALLATION_MULTIPLIERS.get(installation_type, 0.97)
            
        installation_cost = (installation_material_total + plant_material_total) * install_multiplier
        
        # Calculate delivery cost
        origin_location = installation_data.get('origin_location', 'Frankfort')
        origin_address = ORIGIN_ADDRESSES.get(origin_location, ORIGIN_ADDRESSES["Frankfort"])
            
        customer_address = f"{installation_data.get('customer_street_address', '')}, {installation_data.get('customer_city', '')}, KY {installation_data.get('customer_zip', '')}"
        
        delivery_mileage = calculate_driving_distance(origin_address, customer_address)
        delivery_cost = DELIVERY_MILEAGE_RATE * 2 * delivery_mileage
        
        # Final calculations
        final_subtotal = plant_material_discount_total + installation_material_total + installation_cost + delivery_cost
        final_tax = final_subtotal * TAX_RATE
        final_total = final_subtotal + final_tax
        
        return {
            'plant_material_total': plant_material_total,
            'plant_material_discount_total': plant_material_discount_total,
            'installation_material_total': installation_material_total,
            'installation_cost': installation_cost,
            'delivery_cost': delivery_cost,
            'delivery_mileage': delivery_mileage,
            'final_subtotal': final_subtotal,
            'final_tax': final_tax,
            'final_total': final_total,
            'total_mulch_quantity': total_mulch_quantity,
            'total_soil_quantity': total_soil_quantity,
            'total_tablet_quantity': total_tablet_quantity,
            'tablet_total_quantity': total_tablet_quantity,
            'mulch_total_quantity': total_mulch_quantity,
            'soil_conditioner_total_quantity': total_soil_quantity,
            'tablet_total_price': tablet_total_price,
            'mulch_total_price': mulch_total_price,
            'soil_conditioner_total_price': soil_conditioner_total_price,
            'deer_guard_price': deer_guard_price,
            'tree_stakes_price': tree_stakes_price,
            'mulch_sku': mulch_sku,
            'mulch_type': mulch_type,
        }
        
    except Exception as e:
        st.error(f"Error in pricing calculations: {e}")
        return {}


# MAIN APPLICATION INTERFACE
def main():
    """Main application interface"""
    initialize_app()
    
    st.title("🌿 Install App")
    
    # Load Existing Install button (shown at top of Phase 1)
    if st.session_state.phase == 1 and st.session_state.step == 'A' and not st.session_state.editing_existing:
        with st.expander("📂 Load Existing Install", expanded=False):
            with st.spinner("Loading saved installs..."):
                existing_installs = load_install_states()
            
            if existing_installs:
                st.write(f"Found {len(existing_installs)} saved install(s):")
                
                for install in existing_installs:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.write(f"**{install['customer_name']}**")
                    with col2:
                        st.write(f"ID: {install['install_id']}")
                    with col3:
                        if st.button("Load", key=f"load_{install['install_id']}"):
                            load_existing_install(install)
                            st.rerun()
            else:
                st.info("No saved installs found.")
    
    # Phase 1: Plant & Installation Data
    if st.session_state.phase == 1:
        
        # Step A: Plants to be installed
        if st.session_state.step == 'A':
            st.header("Plants to be Installed")
            
            if st.session_state.editing_existing:
                st.info("✏️ Editing existing install")
            
            current_plant = st.session_state.plant_count
            
            st.subheader(f"Plant #{current_plant}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                quantity = st.number_input(f"Quantity:", min_value=1, key=f"plant_{current_plant}_quantity")
                size = st.selectbox(f"Size:", PLANT_SIZE_OPTIONS, key=f"plant_{current_plant}_size")
                plant_material = st.text_input(f"Plant Material:", key=f"plant_{current_plant}_material")
            
            with col2:
                price = st.number_input(f"Retail Price ($):", min_value=0.0, step=0.01, key=f"plant_{current_plant}_price")
                discount_percent = st.number_input(f"Discount (% Off):", min_value=0.0, max_value=100.0, step=0.1, key=f"plant_{current_plant}_discount_percent")
                discount_dollars = st.number_input(f"Discount ($ Off):", min_value=0.0, step=0.01, key=f"plant_{current_plant}_discount_dollars")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Add Another Plant"):
                    st.session_state.plants[current_plant] = {
                        'quantity': quantity,
                        'size': size,
                        'plant_material': clean_text_input(plant_material),
                        'price': price,
                        'discount_percent': discount_percent,
                        'discount_dollars': discount_dollars
                    }
                    st.session_state.plant_count += 1
                    st.rerun()
            
            with col2:
                if st.button("That's All"):
                    st.session_state.plants[current_plant] = {
                        'quantity': quantity,
                        'size': size,
                        'plant_material': clean_text_input(plant_material),
                        'price': price,
                        'discount_percent': discount_percent,
                        'discount_dollars': discount_dollars
                    }
                    st.session_state.step = 'B'
                    st.rerun()
        
        # Step B: Installation Details
        elif st.session_state.step == 'B':
            st.header("Installation Details")
            
            if st.session_state.editing_existing:
                st.info("✏️ Editing existing install")
            
            col1, col2 = st.columns(2)
            
            with col1:
                origin_location = st.selectbox("Sold From:", ["Frankfort", "Lexington"])
                mulch_type = st.selectbox("Mulch Type:", MULCH_TYPE_OPTIONS)
                tree_stakes = st.number_input("Number of Tree Stakes:", min_value=0, step=1)
                deer_guards = st.number_input("Number of Deer Guards:", min_value=0, step=1)
                installation_type = st.selectbox("Installation Type:", INSTALLATION_TYPE_OPTIONS)
            
            with col2:
                st.subheader("Install Address")
                street_address = st.text_input("Street Address:")
                city = st.text_input("City:")
                zip_code = st.text_input("Zip:")
            
            if st.button("Calculate Quote"):
                if street_address and city and zip_code:
                    st.session_state.installation_data = st.session_state.get("installation_data", {})
                    st.session_state.installation_data.update({
                        'origin_location': origin_location,
                        'mulch_type': mulch_type,
                        'tree_stakes_quantity': tree_stakes,
                        'deer_guards_quantity': deer_guards,
                        'installation_type': installation_type,
                        'customer_street_address': clean_text_input(street_address),
                        'customer_city': clean_text_input(city),
                        'customer_zip': zip_code
                    })
                    st.session_state.step = 'C'
                    st.rerun()
                else:
                    st.error("Please fill in all address fields")
        
        # Step C: Calculations and Quote Display
        elif st.session_state.step == 'C':
            st.header("Quote Calculation")
            
            with st.spinner("Calculating quote..."):
                pricing_data = calculate_pricing(st.session_state.plants, st.session_state.installation_data)
                st.session_state.pricing_data = pricing_data
            
            if pricing_data:
                st.success("Quote calculated successfully!")
                
                st.subheader("Quote Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Plant Materials:** ${pricing_data.get('plant_material_discount_total', 0):.2f}")
                    st.write(f"**Installation Materials:** ${pricing_data.get('installation_material_total', 0):.2f}")
                    st.write(f"**Installation Cost:** ${pricing_data.get('installation_cost', 0):.2f}")
                
                with col2:
                    st.write(f"**Delivery Cost:** ${pricing_data.get('delivery_cost', 0):.2f}")
                    st.write(f"**Subtotal:** ${pricing_data.get('final_subtotal', 0):.2f}")
                    st.write(f"**Tax:** ${pricing_data.get('final_tax', 0):.2f}")
                
                st.markdown(f"### **Total: ${pricing_data.get('final_total', 0):.2f}**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Move Forward with Quote"):
                        st.session_state.phase = 2
                        st.rerun()
                
                with col2:
                    if st.button("No, Restart"):
                        clear_all_data()
                        st.rerun()
    
    # Phase 2: Customer Data with Signature
    elif st.session_state.phase == 2:
        st.header("Customer Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name:*", key="customer_name")
            customer_email = st.text_input("Email Address:*", key="customer_email")
            customer_phone = st.text_input("Phone Number:*", key="customer_phone")
            customer_subdivision = st.text_input("Subdivision:*", key="customer_subdivision")
            customer_cross_street = st.text_input("Nearest Cross Street:*", key="customer_cross_street")
            install_location = st.text_input("Where will this be installed in the yard?*", key="install_location")
            
        with col2:
            customer_number_response = st.text_input("Customer Number (if known):", key="customer_number")
            order_number_response = st.text_input("Order Number (if known):", key="order_number")

            col1a, col2a = st.columns(2)

            with col1a:
                gate_response = st.radio("Is there a gate?*", ["Yes", "No"], key="gate_response")

            with col2a:
                gate_width = st.radio("Is it a minimum of 42\" wide?", ["Yes", "No"], key="gate_width")

            dogs_response = st.radio("Are there dogs?*", ["Yes", "No"], key="dogs_response")

            utilities_check = st.multiselect(
                "Mark Any Obstacles Near Planting:*",
                options=UTILITIES_OPTIONS,
                key="utilities_check"
            )

            if not utilities_check:
                st.warning('Please select at least "No Obstacles Near Planting."')

        notes = st.text_area("Notes:", key="notes")
        employee_initials = st.text_input("Employee Initials:", key="employee_initials")
        
        # Customer Signature Canvas
        st.markdown("---")
        st.subheader("Customer Signature")
        st.write("Please sign below:")
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)",
            stroke_width=2,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=150,
            width=400,
            drawing_mode="freedraw",
            key="customer_signature_canvas",
        )
        
        if st.button("Complete"):
            if customer_name and customer_email and customer_phone and customer_subdivision and customer_cross_street:
                customer_data = {
                    'customer_name': clean_text_input(customer_name),
                    'customer_email': customer_email,
                    'customer_phone': customer_phone,
                    'customer_subdivision': clean_text_input(customer_subdivision),
                    'customer_cross_street': clean_text_input(customer_cross_street),
                    'gate_response': gate_response,
                    'gate_width': gate_width,
                    'dogs_response': dogs_response,
                    'install_location': clean_text_input(install_location),
                    'utilities_check': utilities_check,
                    'notes': clean_text_input(notes),
                    'customer_number': clean_text_input(customer_number_response),
                    'order_number': clean_text_input(order_number_response),
                    'employee_initials': clean_text_input(employee_initials)
                }
                
                st.session_state.customer_data = customer_data
                
                # Store signature if provided
                if canvas_result.image_data is not None:
                    st.session_state.customer_signature = canvas_result
                
                st.session_state.phase = 3
                st.rerun()
            else:
                st.error("Please fill in all required fields marked with *")
    
    # Phase 3: PDF Generation and Completion
    elif st.session_state.phase == 3:
        st.header("Quote Completed!")
        
        st.success("Your quote has been generated successfully!")

        # Get signature if it exists
        customer_signature = st.session_state.get('customer_signature', None)
        
        # Generate PDF
        pdf_buffer = generate_pdf(
            st.session_state.plants, 
            st.session_state.installation_data, 
            st.session_state.customer_data, 
            st.session_state.pricing_data,
            customer_signature
        )

        today_str = datetime.datetime.today().strftime("%m%d%Y")
        customer_name_clean = st.session_state.customer_data['customer_name'].replace(" ", "_")
        install_id = st.session_state.get('install_id', '')
        
        if install_id:
            pdf_filename = f"{install_id}-{customer_name_clean}-{today_str}-Installation.pdf"
        else:
            pdf_filename = f"{customer_name_clean}-{today_str}-Installation.pdf"

        if pdf_buffer:
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=pdf_filename,
                mime="application/pdf"
            )
        
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Create a New Installation"):
                clear_all_data()
                st.rerun()

        with col2:
            if st.button("Send to Google Sheet Dashboard"):
                if not st.session_state.get("customer_data") or not st.session_state.get("installation_data") or not st.session_state.get("pricing_data"):
                    st.error("Missing data – please complete the quote before sending to the dashboard.")
                else:
                    try:
                        # Upload PDF first
                        pdf_buffer.seek(0)
                        pdf_link = upload_pdf_to_drive(pdf_buffer, pdf_filename, st.session_state.get('install_id'))
                        
                        # Send to dashboard
                        install_id = send_to_dashboard(
                            st.session_state.customer_data,
                            st.session_state.installation_data,
                            st.session_state.pricing_data,
                            st.session_state.plants,
                            pdf_link,
                            st.session_state.get('install_id')
                        )
                        
                        if install_id:
                            # Save state for future loading
                            save_install_state(
                                install_id,
                                st.session_state.plants,
                                st.session_state.installation_data,
                                st.session_state.customer_data,
                                st.session_state.pricing_data
                            )
                            
                            st.success(f"Install added to Dashboard ✅ (ID: {install_id})")
                        
                    except Exception as e:
                        st.error(f"Failed to send to Google Sheet: {e}")


if __name__ == "__main__":
    main()