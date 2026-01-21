# application_scheduling.py
# Scheduling module for job fair appointments

import streamlit as st
import datetime

# Configuration for scheduling
SCHEDULING_CONFIG = {
    'locations': ['LEXINGTON', 'FRANKFORT'],
    'dates': [
        {'display': 'Wednesday, February 18', 'value': '2026-02-18'},
        {'display': 'Thursday, February 19', 'value': '2026-02-19'},
        {'display': 'Friday, February 20', 'value': '2026-02-20'},
        {'display': 'Saturday, February 21', 'value': '2026-02-21'}
    ],
    'time_slots': ['10am-12pm', '12pm-2pm', '2pm-4pm']
}

# Track which slots are unavailable (greyed out)
# Format: {location: {date: [time_slots]}}
# Edit this dictionary to grey out slots as they fill up
UNAVAILABLE_SLOTS = {
    'LEXINGTON': {
        '2026-02-18': [],  # Add time slots here like ['10am-12pm'] to grey them out
        '2026-02-19': [],
        '2026-02-20': [],
        '2026-02-21': []
    },
    'FRANKFORT': {
        '2026-02-18': [],
        '2026-02-19': [],
        '2026-02-20': [],
        '2026-02-21': []
    }
}

def is_slot_available(location, date, time_slot):
    """Check if a time slot is available"""
    if location in UNAVAILABLE_SLOTS and date in UNAVAILABLE_SLOTS[location]:
        return time_slot not in UNAVAILABLE_SLOTS[location][date]
    return True

def render_scheduling_section():
    """Render the scheduling interface and return selected schedule data"""
    
    # Location selection
    st.subheader("Select Location")
    cols = st.columns(len(SCHEDULING_CONFIG['locations']))
    
    selected_location = None
    for idx, location in enumerate(SCHEDULING_CONFIG['locations']):
        with cols[idx]:
            if st.button(location, key=f"loc_{location}", use_container_width=True):
                st.session_state.selected_location = location
    
    if 'selected_location' in st.session_state:
        selected_location = st.session_state.selected_location
        st.info(f"Selected Location: **{selected_location}**")
    
    st.markdown("---")
    
    # Date and time selection
    st.subheader("Select Date and Time")
    
    # Create columns for each date
    date_cols = st.columns(len(SCHEDULING_CONFIG['dates']))
    
    selected_schedule = None
    
    for idx, date_info in enumerate(SCHEDULING_CONFIG['dates']):
        with date_cols[idx]:
            st.markdown(f"**{date_info['display'].split(',')[0]}**")
            st.markdown(f"{date_info['display'].split(',')[1].strip()}")
            st.markdown("---")
            
            # Display time slots for this date
            for time_slot in SCHEDULING_CONFIG['time_slots']:
                # Check if location is selected
                if not selected_location:
                    st.button(
                        time_slot, 
                        key=f"slot_{date_info['value']}_{time_slot}",
                        disabled=True,
                        use_container_width=True
                    )
                else:
                    # Check if slot is available
                    is_available = is_slot_available(selected_location, date_info['value'], time_slot)
                    
                    if not is_available:
                        st.button(
                            f"~~{time_slot}~~ (Full)",
                            key=f"slot_{date_info['value']}_{time_slot}",
                            disabled=True,
                            use_container_width=True
                        )
                    else:
                        if st.button(
                            time_slot,
                            key=f"slot_{date_info['value']}_{time_slot}",
                            use_container_width=True
                        ):
                            st.session_state.selected_schedule = {
                                'location': selected_location,
                                'date': date_info['display'],
                                'date_value': date_info['value'],
                                'time_slot': time_slot
                            }
    
    # Show selected schedule
    if 'selected_schedule' in st.session_state:
        selected_schedule = st.session_state.selected_schedule
        st.success(
            f"Selected: {selected_schedule['location']} - "
            f"{selected_schedule['date']} - {selected_schedule['time_slot']}"
        )
        return selected_schedule
    elif selected_location:
        st.warning("Please select a date and time slot above")
    else:
        st.warning("Please select a location first, then choose your date and time")
    
    return None

def get_schedule_data():
    """Get the currently selected schedule data"""
    return st.session_state.get('selected_schedule', None)

def mark_slot_unavailable(location, date, time_slot):
    """
    Mark a time slot as unavailable (for manual management)
    This function is provided for future use if you want to programmatically
    manage availability from within the app
    """
    if location not in UNAVAILABLE_SLOTS:
        UNAVAILABLE_SLOTS[location] = {}
    if date not in UNAVAILABLE_SLOTS[location]:
        UNAVAILABLE_SLOTS[location][date] = []
    if time_slot not in UNAVAILABLE_SLOTS[location][date]:
        UNAVAILABLE_SLOTS[location][date].append(time_slot)

def mark_slot_available(location, date, time_slot):
    """
    Mark a time slot as available again (for manual management)
    """
    if location in UNAVAILABLE_SLOTS and date in UNAVAILABLE_SLOTS[location]:
        if time_slot in UNAVAILABLE_SLOTS[location][date]:
            UNAVAILABLE_SLOTS[location][date].remove(time_slot)
