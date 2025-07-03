"""View functions for HALCON Dongle Tracker."""

import streamlit as st
from typing import Optional
from database import DongleDatabase, DongleState, DatabaseError
from ui_components import UIComponents


class DongleViews:
    """View functions for different app sections."""
    
    def __init__(self, db: DongleDatabase):
        self.db = db
        self.ui = UIComponents()
    
    def view_dongles(self) -> None:
        """Display all dongles overview."""
        st.subheader("All Dongles Overview")
        
        try:
            dongles = self.db.get_all_dongles()
            self.ui.display_dongle_overview(dongles)
            
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def add_dongle(self) -> None:
        """Add a new dongle."""
        form_data = self.ui.dongle_form("Add a New Dongle")
        
        if form_data:
            try:
                self.db.add_dongle(
                    dongle_id=form_data['dongle_id'],
                    halcon_version=form_data['halcon_version'],
                    notes=form_data['notes'],
                    default_owner=form_data['default_owner'],
                    state=DongleState(form_data['state'])
                )
                self.ui.success_message(
                    f"Dongle '{form_data['dongle_id']}' added successfully with default owner '{form_data['default_owner']}' and state '{form_data['state']}'!"
                )
                st.rerun()
            except DatabaseError as e:
                self.ui.handle_database_error(e)
    
    def check_out_dongle(self) -> None:
        """Check out a dongle."""
        try:
            available_dongles = self.db.get_available_dongles()
            
            if not available_dongles:
                self._show_checkout_unavailable_info()
                return
            
            form_data = self.ui.assignment_form("Check Out a Dongle", available_dongles, is_checkout=True)
            
            if form_data:
                self.db.check_out_dongle(
                    dongle_id=form_data['selected'],
                    assigned_to=form_data['assignee'],
                    notes=form_data['notes']
                )
                self.ui.success_message(f"Dongle '{form_data['selected']}' checked out to '{form_data['assignee']}' successfully!")
                st.rerun()
                
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def _show_checkout_unavailable_info(self) -> None:
        """Show information about why no dongles are available for checkout."""
        st.info("📭 No working dongles are currently available for check-out.")
        
        try:
            # Show breakdown of why dongles aren't available
            all_dongles = self.db.get_all_dongles()
            if all_dongles:
                st.write("**Dongle Status Summary:**")
                
                non_working = [
                    f"{dongle['dongle_id']} ({dongle['state']})" 
                    for dongle in all_dongles 
                    if dongle['state'] != DongleState.WORKING.value
                ]
                
                if non_working:
                    st.write("Non-working dongles:", ", ".join(non_working))
                
                checked_out = [
                    dongle['dongle_id'] 
                    for dongle in all_dongles 
                    if dongle['assigned_to']
                ]
                
                if checked_out:
                    st.write("Currently checked out:", ", ".join(checked_out))
                    
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def check_in_dongle(self) -> None:
        """Check in a dongle."""
        try:
            checked_out_dongles = self.db.get_checked_out_dongles()
            
            if not checked_out_dongles:
                st.info("📬 No dongles are currently checked out.")
                return
            
            # Display currently checked out dongles
            self.ui.display_checked_out_dongles(checked_out_dongles)
            st.markdown("---")
            
            # Create options for the form
            dongle_options = [
                f"{dongle_id} (assigned to: {assigned_to})" 
                for dongle_id, assigned_to, _ in checked_out_dongles
            ]
            
            form_data = self.ui.assignment_form("Check In a Dongle", dongle_options, is_checkout=False)
            
            if form_data:
                # Extract dongle_id from the selected option
                selected_dongle = form_data['selected'].split(" (assigned to:")[0]
                
                self.db.check_in_dongle(
                    dongle_id=selected_dongle,
                    notes=form_data['notes']
                )
                self.ui.success_message(f"Dongle '{selected_dongle}' checked in successfully!")
                st.rerun()
                
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def edit_dongle(self) -> None:
        """Edit dongle information."""
        st.subheader("Edit Dongle Information")
        
        try:
            dongles = self.db.get_all_dongles()
            selected_dongle_id = self.ui.display_dongle_selector(dongles, "Select Dongle to Edit")
            
            if selected_dongle_id:
                # Get current dongle data
                current_dongle = next(
                    (dongle for dongle in dongles if dongle['dongle_id'] == selected_dongle_id),
                    None
                )
                
                if current_dongle:
                    form_data = self.ui.edit_dongle_form(current_dongle)
                    
                    if form_data:
                        try:
                            changes_made = self.db.update_dongle(
                                dongle_id=selected_dongle_id,
                                notes=form_data['notes'],
                                default_owner=form_data['default_owner'],
                                state=DongleState(form_data['state']),
                                changed_by=form_data['changed_by'],
                                change_notes=form_data['change_notes']
                            )
                            
                            if changes_made:
                                self.ui.success_message(
                                    f"Dongle '{selected_dongle_id}' updated successfully! Changed: {', '.join(changes_made)}"
                                )
                                st.rerun()
                            else:
                                self.ui.info_message("No changes detected.")
                                
                        except DatabaseError as e:
                            self.ui.handle_database_error(e)
                    
                    # Show recent edit history
                    try:
                        edit_history = self.db.get_dongle_edit_history(selected_dongle_id)
                        self.ui.display_edit_history(edit_history)
                    except DatabaseError as e:
                        self.ui.handle_database_error(e)
                        
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def view_history(self) -> None:
        """View assignment history."""
        st.subheader("Dongle Assignment History")
        
        try:
            filter_options = self.db.get_filter_options()
            filters = self.ui.history_filters(filter_options)
            
            history = self.db.get_assignment_history(
                dongle_filter=filters['dongle_filter'],
                assignee_filter=filters['assignee_filter'],
                action_filter=filters['action_filter']
            )
            
            self.ui.display_history_table(history, "Assignment History")
            
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def view_edit_history(self) -> None:
        """View complete edit history."""
        st.subheader("Complete Edit History")
        
        try:
            filter_options = self.db.get_filter_options()
            filters = self.ui.edit_history_filters(filter_options)
            
            # Get edit history from database
            history = self._get_filtered_edit_history(filters)
            
            self.ui.display_history_table(history, "Edit History")
            
        except DatabaseError as e:
            self.ui.handle_database_error(e)
    
    def _get_filtered_edit_history(self, filters: dict) -> list:
        """Get filtered edit history."""
        # Build query manually since we have specific edit history filtering needs
        cursor = self.db.conn.cursor()
        
        query = "SELECT dongle_id, field_changed, old_value, new_value, changed_by, change_date, notes FROM dongle_edits"
        params = []
        conditions = []
        
        if filters['dongle_filter']:
            conditions.append("dongle_id = ?")
            params.append(filters['dongle_filter'])
        
        if filters['editor_filter']:
            conditions.append("changed_by = ?")
            params.append(filters['editor_filter'])
        
        if filters['field_filter']:
            conditions.append("field_changed = ?")
            params.append(filters['field_filter'])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY change_date DESC LIMIT 200"
        
        rows = cursor.execute(query, params).fetchall()
        
        return [
            {
                'dongle_id': row[0],
                'field_changed': row[1],
                'old_value': row[2],
                'new_value': row[3],
                'changed_by': row[4],
                'change_date': row[5],
                'notes': row[6]
            }
            for row in rows
        ]