# application_scheduling.py
# Scheduling module for job fair appointments

import streamlit as st
import datetime

# Configuration for scheduling
SCHEDULING_CONFIG = {
    'dates': [
        {
            'display': 'Wednesday, February 18 in Lexington',
            'short_display': 'Wed, Feb 18',
            'value': '2026-02-18',
            'location': 'Lexington',
            'address': '2700 Palumbo Drive, Lexington KY 40509'
        },
        {
            'display': 'Thursday, February 19 in Lexington',
            'short_display': 'Thu, Feb 19',
            'value': '2026-02-19',
            'location': 'Lexington',
            'address': '2700 Palumbo Drive, Lexington KY 40509'
        },
        {
            'display': 'Friday, February 20 in Frankfort',
            'short_display': 'Fri, Feb 20',
            'value': '2026-02-20',
            'location': 'Frankfort',
            'address': '3690 East West Connector, Frankfort KY 40601'
        },
        {
            'display': 'Saturday, February 21 in Frankfort',
            'short_display': 'Sat, Feb 21',
            'value': '2026-02-21',
            'location': 'Frankfort',
            'address': '3690 East West Connector, Frankfort KY 40601'
        }
    ],
    'time_slots': ['10am-12pm', '12pm-2pm', '2pm-4pm']
}

# Track which slots are unavailable (greyed out)
# Format: {date_value: [time_slots]}
# Edit this dictionary to grey out slots as they fill up
UNAVAILABLE_SLOTS = {
    '2026-02-18': [],  # Add time slots here like ['10am-12pm'] to grey them out
    '2026-02-19': [],
    '2026-02-20': [],
    '2026-02-21': []
}

def is_slot_available(date, time_slot):
    """Check if a time slot is available"""
    if date in UNAVAILABLE_SLOTS:
        return time_slot not in UNAVAILABLE_SLOTS[date]
    return True

def render_scheduling_section():
    """Render the scheduling interface and return selected schedule data"""
    
    # Date selection - mobile-friendly single column
    st.subheader("Select Your Interview Day & Location")
    
    # Show each date as a button
    for date_info in SCHEDULING_CONFIG['dates']:
        if st.button(
            date_info['display'],
            key=f"date_{date_info['value']}",
            use_container_width=True
        ):
            st.session_state.selected_date = date_info
            if 'selected_time' in st.session_state:
                del st.session_state.selected_time  # Clear time selection when date changes
    
    # Show selected date
    if 'selected_date' not in st.session_state:
        st.info("👆 Please select a day above")
        return None
    
    selected_date = st.session_state.selected_date
    st.success(f"Selected: **{selected_date['display']}**")
    
    st.markdown("---")
    
    # Time selection
    st.subheader("Select Your Interview Time")
    
    for time_slot in SCHEDULING_CONFIG['time_slots']:
        is_available = is_slot_available(selected_date['value'], time_slot)
        
        if not is_available:
            st.button(
                f"~~{time_slot}~~ (Full)",
                key=f"time_{selected_date['value']}_{time_slot}",
                disabled=True,
                use_container_width=True
            )
        else:
            if st.button(
                time_slot,
                key=f"time_{selected_date['value']}_{time_slot}",
                use_container_width=True
            ):
                st.session_state.selected_time = time_slot
                st.session_state.selected_schedule = {
                    'location': selected_date['location'],
                    'address': selected_date['address'],
                    'date': selected_date['display'],
                    'date_value': selected_date['value'],
                    'time_slot': time_slot
                }
    
    # Show complete selection
    if 'selected_schedule' in st.session_state:
        schedule = st.session_state.selected_schedule
        st.success(
            f"✓ You're scheduled for: **{schedule['time_slot']}** on **{schedule['date']}**"
        )
        return schedule
    else:
        st.info("👆 Please select a time above")
    
    return None

def get_schedule_data():
    """Get the currently selected schedule data"""
    return st.session_state.get('selected_schedule', None)

def mark_slot_unavailable(date, time_slot):
    """
    Mark a time slot as unavailable (for manual management)
    This function is provided for future use if you want to programmatically
    manage availability from within the app
    """
    if date not in UNAVAILABLE_SLOTS:
        UNAVAILABLE_SLOTS[date] = []
    if time_slot not in UNAVAILABLE_SLOTS[date]:
        UNAVAILABLE_SLOTS[date].append(time_slot)

def mark_slot_available(date, time_slot):
    """
    Mark a time slot as available again (for manual management)
    """
    if date in UNAVAILABLE_SLOTS:
        if time_slot in UNAVAILABLE_SLOTS[date]:
            UNAVAILABLE_SLOTS[date].remove(time_slot)
