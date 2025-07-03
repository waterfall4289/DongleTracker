"""Reusable UI components for HALCON Dongle Tracker."""

import streamlit as st
import pandas as pd
import datetime
from typing import List, Dict, Any, Optional, Tuple
from database import DongleState, DatabaseError


class UIComponents:
    """Reusable UI components."""
    
    @staticmethod
    def get_state_emoji(state: str) -> str:
        """Get emoji for dongle state."""
        state_emojis = {
            DongleState.WORKING.value: "🟢",
            DongleState.NOT_WORKING.value: "🔴",
            DongleState.MISSING.value: "❌",
            DongleState.RETIRED.value: "🗄️",
            "Under Repair": "🔧"  # Backward compatibility
        }
        return state_emojis.get(state, "🟢")
    
    @staticmethod
    def format_action(action: str) -> str:
        """Format action with emoji."""
        action_map = {
            "check_out": "📤 Check Out",
            "check_in": "📥 Check In"
        }
        return action_map.get(action, action)
    
    @staticmethod
    def display_dongle_overview(dongles: List[Dict[str, Any]]) -> None:
        """Display dongles overview with summary statistics."""
        if not dongles:
            st.info("No dongles found. Add some dongles first!")
            return
        
        # Prepare display data
        display_data = []
        for dongle in dongles:
            state_emoji = UIComponents.get_state_emoji(dongle['state'])
            
            if dongle['assigned_to']:
                status = f"{state_emoji} Checked Out"
                current_owner = dongle['assigned_to']
            else:
                status = f"{state_emoji} Available"
                current_owner = dongle['default_owner']
            
            display_data.append({
                "Status": status,
                "State": f"{state_emoji} {dongle['state']}",
                "Dongle ID": dongle['dongle_id'],
                "Current Owner": current_owner,
                "HALCON Version": dongle['halcon_version'],
                "Assignment Date": dongle['assignment_date'] or "",
                "Notes": dongle['notes']
            })
        
        # Display table
        df = pd.DataFrame(display_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
        UIComponents.display_summary_metrics(display_data)
        UIComponents.display_state_breakdown(display_data)
    
    @staticmethod
    def display_summary_metrics(display_data: List[Dict[str, Any]]) -> None:
        """Display summary metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Dongles", len(display_data))
        
        with col2:
            checked_out = len([d for d in display_data if "Checked Out" in d["Status"]])
            st.metric("Checked Out", checked_out)
        
        with col3:
            available = len(display_data) - checked_out
            st.metric("Available", available)
        
        with col4:
            working = len([d for d in display_data if "Working" in d["State"]])
            st.metric("Working", working)
    
    @staticmethod
    def display_state_breakdown(display_data: List[Dict[str, Any]]) -> None:
        """Display state breakdown."""
        st.markdown("---")
        st.subheader("Summary")
        
        state_counts = {}
        for row in display_data:
            state = row["State"].split(" ", 1)[1]  # Remove emoji
            state_counts[state] = state_counts.get(state, 0) + 1
        
        if state_counts:
            state_cols = st.columns(len(state_counts))
            for i, (state, count) in enumerate(state_counts.items()):
                with state_cols[i]:
                    emoji = UIComponents.get_state_emoji(state)
                    st.metric(f"{emoji} {state}", count)
    
    @staticmethod
    def dongle_form(title: str, dongle_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Reusable dongle form."""
        st.subheader(title)
        
        with st.form("dongle_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                dongle_id = st.text_input(
                    "Dongle ID *", 
                    value=dongle_data.get('dongle_id', '') if dongle_data else '',
                    help="Unique identifier for the dongle"
                )
                halcon_version = st.text_input(
                    "HALCON Version", 
                    value=dongle_data.get('halcon_version', '') if dongle_data else '',
                    help="e.g., 22.11, 23.05"
                )
                default_owner = st.text_input(
                    "Default Owner", 
                    value=dongle_data.get('default_owner', 'Admin') if dongle_data else 'Admin',
                    help="Person responsible when dongle is not checked out"
                )
            
            with col2:
                current_state = dongle_data.get('state', DongleState.WORKING.value) if dongle_data else DongleState.WORKING.value
                state_options = [state.value for state in DongleState]
                state_index = state_options.index(current_state) if current_state in state_options else 0
                
                state = st.selectbox(
                    "State", 
                    options=state_options,
                    index=state_index,
                    help="Current condition of the dongle"
                )
                notes = st.text_area(
                    "Notes", 
                    value=dongle_data.get('notes', '') if dongle_data else '',
                    help="Additional information about this dongle"
                )
            
            submitted = st.form_submit_button("Submit", type="primary")
            
            if submitted and dongle_id.strip():
                return {
                    'dongle_id': dongle_id.strip(),
                    'halcon_version': halcon_version.strip(),
                    'default_owner': default_owner.strip(),
                    'state': state,
                    'notes': notes.strip()
                }
            elif submitted:
                st.warning("⚠️ Dongle ID is required.")
        
        return None
    
    @staticmethod
    def assignment_form(title: str, dongles: List[str], is_checkout: bool = True) -> Optional[Dict[str, Any]]:
        """Reusable assignment form."""
        st.subheader(title)
        
        if not dongles:
            info_msg = "No working dongles are currently available for check-out." if is_checkout else "No dongles are currently checked out."
            st.info(f"📭 {info_msg}")
            return None
        
        with st.form("assignment_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                if is_checkout:
                    selected = st.selectbox("Select Available Working Dongle", dongles)
                    assignee = st.text_input("Assign To *", help="Name of the person checking out the dongle")
                else:
                    selected = st.selectbox("Select Dongle to Check In", dongles)
                    assignee = ""
            
            with col2:
                notes = st.text_area(
                    "Notes (Optional)", 
                    help="Purpose of checkout, expected return date, etc." if is_checkout else "Condition of dongle, issues found, etc."
                )
            
            action_text = "Check Out Dongle" if is_checkout else "Check In Dongle"
            submitted = st.form_submit_button(action_text, type="primary")
            
            if submitted:
                if is_checkout and not assignee.strip():
                    st.warning("⚠️ Assignee name is required.")
                    return None
                
                return {
                    'selected': selected,
                    'assignee': assignee.strip(),
                    'notes': notes.strip()
                }
        
        return None
    
    @staticmethod
    def display_checked_out_dongles(checked_out_dongles: List[Tuple[str, str, str]]) -> None:
        """Display currently checked out dongles."""
        if checked_out_dongles:
            st.write("**Currently Checked Out Dongles:**")
            for dongle_id, assigned_to, checkout_date in checked_out_dongles:
                st.write(f"- **{dongle_id}** (assigned to: {assigned_to}, since: {checkout_date})")
        else:
            st.info("📬 No dongles are currently checked out.")
    
    @staticmethod
    def edit_dongle_form(dongle_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Edit dongle form."""
        st.markdown("---")
        st.write(f"**Editing Dongle: {dongle_data['dongle_id']}**")
        st.write(f"*Current State: {dongle_data['state']} | Current Default Owner: {dongle_data['default_owner']}*")
        
        with st.form("edit_dongle_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_default_owner = st.text_input(
                    "Default Owner", 
                    value=dongle_data['default_owner'],
                    help="Person responsible when dongle is not checked out"
                )
                
                state_options = [state.value for state in DongleState]
                current_state_index = state_options.index(dongle_data['state']) if dongle_data['state'] in state_options else 0
                
                new_state = st.selectbox(
                    "State", 
                    options=state_options,
                    index=current_state_index,
                    help="Current condition of the dongle"
                )
            
            with col2:
                new_notes = st.text_area(
                    "Notes", 
                    value=dongle_data['notes'],
                    help="Additional information about this dongle"
                )
                changed_by = st.text_input(
                    "Changed By *", 
                    help="Your name for the edit history (required)"
                )
            
            change_notes = st.text_area(
                "Reason for Change", 
                help="Brief explanation of why these changes are being made"
            )
            
            submitted = st.form_submit_button("Update Dongle", type="primary")
            
            if submitted:
                if not changed_by.strip():
                    st.warning("⚠️ 'Changed By' field is required for tracking.")
                    return None
                
                return {
                    'default_owner': new_default_owner.strip(),
                    'state': new_state,
                    'notes': new_notes.strip(),
                    'changed_by': changed_by.strip(),
                    'change_notes': change_notes.strip()
                }
        
        return None
    
    @staticmethod
    def display_edit_history(edit_history: List[Dict[str, Any]]) -> None:
        """Display edit history."""
        st.markdown("---")
        st.subheader("Recent Edit History")
        
        if edit_history:
            df = pd.DataFrame(edit_history)
            df.columns = ["Field", "Old Value", "New Value", "Changed By", "Date", "Reason"]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No edit history found for this dongle.")
    
    @staticmethod
    def history_filters(filter_options: Dict[str, List[str]]) -> Dict[str, str]:
        """Display history filters."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dongle_filter = st.selectbox(
                "Filter by Dongle ID", 
                options=["All"] + filter_options.get('dongle_ids', []),
                index=0
            )
        
        with col2:
            assignee_filter = st.selectbox(
                "Filter by Assignee", 
                options=["All"] + filter_options.get('assignees', []),
                index=0
            )
        
        with col3:
            action_filter = st.selectbox(
                "Filter by Action",
                options=["All", "Check Out", "Check In"],
                index=0
            )
        
        return {
            'dongle_filter': dongle_filter if dongle_filter != "All" else None,
            'assignee_filter': assignee_filter if assignee_filter != "All" else None,
            'action_filter': action_filter if action_filter != "All" else None
        }
    
    @staticmethod
    def display_history_table(history: List[Dict[str, Any]], title: str = "Assignment History") -> None:
        """Display history table with export option."""
        if not history:
            st.info("No history found matching your filters.")
            return
        
        st.write(f"**Showing {len(history)} records**")
        
        # Prepare dataframe
        df = pd.DataFrame(history)
        if 'action' in df.columns:
            df['action'] = df['action'].apply(UIComponents.format_action)
            df.rename(columns={'action': 'Action'}, inplace=True)
        
        # Capitalize column names
        df.columns = [col.replace('_', ' ').title() for col in df.columns]
        
        st.dataframe(df, use_container_width=True)
        
        # Export option
        if st.button("📊 Export to CSV"):
            csv = df.to_csv(index=False)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dongle_{title.lower().replace(' ', '_')}_{timestamp}.csv"
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=filename,
                mime="text/csv"
            )
    
    @staticmethod
    def edit_history_filters(filter_options: Dict[str, List[str]]) -> Dict[str, str]:
        """Display edit history filters."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            dongle_filter = st.selectbox(
                "Filter by Dongle ID", 
                options=["All"] + filter_options.get('dongle_ids', []),
                index=0
            )
        
        with col2:
            editor_filter = st.selectbox(
                "Filter by Editor", 
                options=["All"] + filter_options.get('editors', []),
                index=0
            )
        
        with col3:
            field_filter = st.selectbox(
                "Filter by Field", 
                options=["All"] + filter_options.get('fields', []),
                index=0
            )
        
        return {
            'dongle_filter': dongle_filter if dongle_filter != "All" else None,
            'editor_filter': editor_filter if editor_filter != "All" else None,
            'field_filter': field_filter if field_filter != "All" else None
        }
    
    @staticmethod
    def handle_database_error(error: Exception) -> None:
        """Handle database errors consistently."""
        if isinstance(error, DatabaseError):
            st.error(f"❌ {error}")
        else:
            st.error(f"❌ An unexpected error occurred: {error}")
    
    @staticmethod
    def success_message(message: str) -> None:
        """Display success message."""
        st.success(f"✅ {message}")
    
    @staticmethod
    def info_message(message: str) -> None:
        """Display info message."""
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def warning_message(message: str) -> None:
        """Display warning message."""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def display_dongle_selector(dongles: List[Dict[str, Any]], label: str = "Select Dongle") -> Optional[str]:
        """Display dongle selector."""
        if not dongles:
            st.info("No dongles found. Add some dongles first!")
            return None
        
        dongle_options = [
            f"{dongle['dongle_id']} (Owner: {dongle['default_owner']}, State: {dongle['state']})" 
            for dongle in dongles
        ]
        
        selected_option = st.selectbox(label, dongle_options)
        
        if selected_option:
            return selected_option.split(" (Owner:")[0]
        
        return None