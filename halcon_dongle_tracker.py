"""HALCON Dongle Tracker - Refactored Main Application.

This is the main entry point for the HALCON Dongle Tracker application.
The application has been refactored to follow clean code principles:
- Database operations separated into database.py
- UI components extracted into ui_components.py  
- View logic organized in views.py
- Main application logic in app.py

Usage:
    streamlit run halcon_dongle_tracker.py

The application will be available at http://localhost:8501
"""

from app import main

if __name__ == "__main__":
    main()