"""HALCON Dongle Tracker - Main Application."""

import streamlit as st
import atexit
from typing import Dict, Callable
from database import DongleDatabase, DatabaseError
from views import DongleViews
from ui_components import UIComponents


class DongleTrackerApp:
    """Main application class for HALCON Dongle Tracker."""
    
    def __init__(self):
        """Initialize the application."""
        self._setup_page_config()
        self.db = self._initialize_database()
        self.views = DongleViews(self.db)
        self.ui = UIComponents()
        
        # Register cleanup function
        atexit.register(self._cleanup)
    
    def _setup_page_config(self) -> None:
        """Configure Streamlit page."""
        st.set_page_config(
            page_title="HALCON Dongle Tracker",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    @st.cache_resource
    def _initialize_database(_self) -> DongleDatabase:
        """Initialize database connection."""
        try:
            return DongleDatabase()
        except DatabaseError as e:
            st.error(f"Failed to initialize database: {e}")
            st.stop()
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        if hasattr(self, 'db') and self.db:
            self.db.close()
    
    def _get_menu_options(self) -> Dict[str, Callable]:
        """Get menu options and their corresponding view functions."""
        return {
            "📋 View Dongles": self.views.view_dongles,
            "📤 Check Out": self.views.check_out_dongle,
            "📥 Check In": self.views.check_in_dongle,
            "➕ Add New Dongle": self.views.add_dongle,
            "✏️ Edit Dongle": self.views.edit_dongle,
            "📊 View History": self.views.view_history,
            "📝 View Edit History": self.views.view_edit_history,
        }
    
    def run(self) -> None:
        """Run the main application."""
        # Title and header
        st.title("🔐 HALCON Dongle Tracker")
        st.markdown("---")
        
        # Sidebar menu
        menu_options = self._get_menu_options()
        menu_keys = list(menu_options.keys())
        
        selected_menu = st.sidebar.radio(
            "Select Action",
            menu_keys,
            index=0
        )
        
        # Execute selected view
        try:
            menu_options[selected_menu]()
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.write("Please try again or contact support if the issue persists.")
        
        # Footer
        st.markdown("---")
        st.markdown("*HALCON Dongle Tracker - Keep track of your hardware dongles efficiently* 🔐")


def main():
    """Main entry point."""
    app = DongleTrackerApp()
    app.run()


if __name__ == "__main__":
    main()