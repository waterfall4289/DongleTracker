# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a HALCON Dongle Tracker - a Streamlit-based web application for managing hardware dongles used with HALCON machine vision software. The application provides a complete dongle management system with check-in/check-out functionality, edit tracking, and assignment history.

**The codebase has been refactored following clean code principles:**
- **database.py**: Database operations, models, and schema management
- **ui_components.py**: Reusable UI components and utility functions  
- **views.py**: View functions for different app sections
- **app.py**: Main application logic and routing
- **halcon_dongle_tracker.py**: Entry point (imports from app.py)

## Running the Application

### Prerequisites
- Python 3.12+ (uses Python 3.12.3 in this environment)
- Install dependencies: `pip install -r requirements.txt`
- Required packages: `streamlit`, `pandas`, `sqlite3` (built-in), `datetime` (built-in), `atexit` (built-in)

### Starting the Application
```bash
streamlit run halcon_dongle_tracker.py
```

The app will be available at `http://localhost:8501` by default.

## Architecture

### Core Components

**Database Layer (`dongles.db`)**
- SQLite database with WAL mode enabled for better concurrency
- Three main tables:
  - `dongles`: Core dongle information (ID, version, state, owner, notes)
  - `assignments`: Check-in/check-out history with timestamps
  - `dongle_edits`: Audit trail for dongle modifications

**Application Structure**
- Single-file Streamlit application (`halcon_dongle_tracker.py`)
- Database initialization with automatic schema migration
- Cached database connection using `@st.cache_resource`
- Menu-driven interface with 7 main sections

### Key Features

1. **Dongle Management**: Add, edit, and track dongles with states (Working, Not Working, Missing, Retired)
2. **Check-out System**: Assign dongles to users with automatic availability tracking
3. **Audit Trail**: Complete edit history with user attribution and timestamps
4. **Data Export**: CSV export functionality for history and edit records
5. **State Management**: Track dongle condition and ownership

### Database Schema

The application automatically handles schema migrations for backward compatibility. Key fields:
- `dongles.state`: Current condition (Working, Not Working, Missing, Retired)
- `dongles.default_owner`: Person responsible when not checked out
- `assignments.action`: Either 'check_out' or 'check_in'
- `dongle_edits`: Complete audit log of all changes

## Refactoring Improvements

**Key improvements made:**
- **Separation of Concerns**: Database, UI, and business logic separated into modules
- **Type Safety**: Added type hints throughout the codebase
- **Error Handling**: Consistent error handling with custom DatabaseError class
- **Code Reuse**: Extracted common UI patterns into reusable components
- **Clean Architecture**: Views handle UI logic, database module handles data operations
- **Maintainability**: Eliminated 700+ line monolithic file, removed duplicate code
- **Documentation**: Added comprehensive docstrings and type annotations

**Files created:**
- `requirements.txt`: Project dependencies
- `halcon_dongle_tracker_original.py`: Backup of original code

## Development Guidelines

### Code Organization
- Database operations in `database.py` with proper error handling
- Reusable UI components in `ui_components.py`
- View logic separated in `views.py` 
- Main application routing in `app.py`
- Form-based UI patterns for data entry
- Consistent error handling with user-friendly messages
- Automatic cache clearing and page refresh after data modifications

### Database Operations
- All database operations use parameterized queries for security
- Proper transaction handling with `conn.commit()`
- Foreign key constraints enabled
- Graceful handling of schema evolution

### UI Patterns
- Sidebar navigation with emoji icons
- Form submission with validation
- Real-time data display with pandas DataFrames
- Export functionality for data analysis
- Confirmation dialogs for destructive operations

## Testing

No formal test suite is present. Manual testing should focus on:
- Database schema migrations
- Check-out/check-in workflows
- Edit tracking and audit trails
- Data export functionality
- Concurrent access scenarios

## Common Issues

- Database file permissions in different environments
- Streamlit caching behavior with database connections
- Schema migration for existing databases
- Concurrent access handling with WAL mode