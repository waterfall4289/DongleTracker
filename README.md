# HALCON Dongle Tracker

A web-based application for managing and tracking HALCON hardware dongles. Built with Streamlit and SQLite, this tool provides a complete dongle management system with check-in/check-out functionality, edit tracking, and assignment history.

## Features

- 🔐 **Dongle Management**: Add, edit, and track dongles with multiple states
- 📤 **Check-out System**: Assign dongles to users with automatic availability tracking
- 📥 **Check-in System**: Return dongles with condition notes
- 📊 **Assignment History**: Complete audit trail of all check-ins and check-outs
- 📝 **Edit History**: Track all changes to dongle information with user attribution
- 📈 **Dashboard**: Overview of dongle status and availability metrics
- 💾 **Data Export**: CSV export functionality for history and records

## Dongle States

- 🟢 **Working**: Dongle is functional and available for use
- 🔴 **Not Working**: Dongle has issues and needs attention
- ❌ **Missing**: Dongle cannot be located
- 🗄️ **Retired**: Dongle is no longer in active use

## Quick Start

### Prerequisites

- Python 3.12+ 
- pip (Python package manager)

### Installation

1. **Clone or download the repository**
   ```bash
   git clone <repository-url>
   cd halcon_dongle_tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   streamlit run halcon_dongle_tracker.py
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - If not, navigate to the URL shown in the terminal

## Usage

### Adding Dongles
1. Select "➕ Add New Dongle" from the sidebar
2. Fill in the dongle information:
   - **Dongle ID**: Unique identifier (required)
   - **HALCON Version**: Software version (e.g., 22.11, 23.05)
   - **Default Owner**: Person responsible when not checked out
   - **State**: Current condition of the dongle
   - **Notes**: Additional information

### Checking Out Dongles
1. Select "📤 Check Out" from the sidebar
2. Choose an available working dongle
3. Enter the assignee name
4. Add optional notes (purpose, expected return date, etc.)

### Checking In Dongles
1. Select "📥 Check In" from the sidebar
2. Choose from currently checked-out dongles
3. Add optional notes about condition or issues

### Editing Dongles
1. Select "✏️ Edit Dongle" from the sidebar
2. Choose the dongle to edit
3. Update information as needed
4. **Required**: Enter your name in "Changed By" field
5. Add reason for changes

### Viewing History
- **📊 View History**: See all check-in/check-out activities with filtering options
- **📝 View Edit History**: Track all changes made to dongle information

## Architecture

The application has been refactored following clean code principles:

```
├── halcon_dongle_tracker.py  # Main entry point
├── app.py                    # Application logic and routing
├── database.py              # Database operations and models
├── ui_components.py         # Reusable UI components
├── views.py                 # View functions for each page
├── requirements.txt         # Python dependencies
├── dongles.db              # SQLite database (auto-created)
└── README.md               # This file
```

### Key Components

- **Database Layer**: SQLite with WAL mode for better concurrency
- **UI Components**: Reusable Streamlit components for forms and displays  
- **Views**: Separated view logic for each application section
- **Type Safety**: Full type hints and custom data models
- **Error Handling**: Consistent error handling throughout

## Database

The application uses SQLite with three main tables:

- **dongles**: Core dongle information
- **assignments**: Check-in/check-out history
- **dongle_edits**: Complete audit trail for changes

The database automatically handles schema migrations and supports existing data.

## Concurrent Usage

- ✅ Multiple users can view data simultaneously
- ✅ Database supports concurrent reads with WAL mode
- ⚠️ Limited concurrent editing support - last edit wins
- ⚠️ No real-time updates between users

For small teams with coordination, the current implementation works well. For larger teams, consider adding optimistic locking and real-time updates.

## Data Export

Both assignment history and edit history can be exported to CSV format with timestamps for external analysis or backup purposes.

## Troubleshooting

### Database Issues
- If you get column errors, delete the database files and restart (data will be lost)
- Ensure proper file permissions for the SQLite database files

### Performance
- The app uses caching for database connections
- Large datasets may require pagination (currently limited to recent records)

### Port Conflicts
- If port 8501 is in use, Streamlit will automatically try the next available port
- You can specify a custom port: `streamlit run halcon_dongle_tracker.py --server.port 8502`

## Development

For development information and technical details, see `CLAUDE.md`.

## License

[Add your license information here]

## Support

For issues or feature requests, please [add your contact/issue reporting information here].