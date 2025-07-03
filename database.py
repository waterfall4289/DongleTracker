"""Database operations for HALCON Dongle Tracker."""

import sqlite3
import datetime
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class DongleState(Enum):
    """Dongle states."""
    WORKING = "Working"
    NOT_WORKING = "Not Working"
    MISSING = "Missing"
    RETIRED = "Retired"


class ActionType(Enum):
    """Assignment action types."""
    CHECK_OUT = "check_out"
    CHECK_IN = "check_in"


@dataclass
class Dongle:
    """Dongle data model."""
    id: int
    dongle_id: str
    halcon_version: str
    notes: str
    default_owner: str
    state: DongleState
    created_date: str


@dataclass
class Assignment:
    """Assignment data model."""
    id: int
    dongle_id: str
    assigned_to: str
    action: ActionType
    date: str
    notes: str


@dataclass
class DongleEdit:
    """Dongle edit data model."""
    id: int
    dongle_id: str
    field_changed: str
    old_value: str
    new_value: str
    changed_by: str
    change_date: str
    notes: str


class DatabaseError(Exception):
    """Custom database error."""
    pass


class DongleDatabase:
    """Database operations for dongle tracking."""
    
    def __init__(self, db_path: str = "dongles.db"):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        self._connect()
        self._initialize_schema()
    
    def _connect(self) -> None:
        """Create database connection."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to connect to database: {e}")
    
    def _initialize_schema(self) -> None:
        """Initialize database schema."""
        if not self.conn:
            raise DatabaseError("Database connection not available")
        
        cursor = self.conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dongles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dongle_id TEXT UNIQUE,
                halcon_version TEXT,
                notes TEXT,
                default_owner TEXT DEFAULT 'Admin',
                state TEXT DEFAULT 'Working',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dongle_id TEXT,
                assigned_to TEXT,
                action TEXT,
                date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT DEFAULT ''
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dongle_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dongle_id TEXT,
                field_changed TEXT,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                change_date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        self._migrate_schema()
        self.conn.commit()
    
    def _migrate_schema(self) -> None:
        """Handle schema migrations."""
        cursor = self.conn.cursor()
        
        # Check existing columns for each table
        try:
            cursor.execute("PRAGMA table_info(dongles)")
            dongle_columns = [col[1] for col in cursor.fetchall()]
            
            cursor.execute("PRAGMA table_info(assignments)")
            assignment_columns = [col[1] for col in cursor.fetchall()]
        except sqlite3.Error:
            # If tables don't exist, they'll be created with full schema
            return
        
        # Add missing columns to dongles table
        dongle_migrations = [
            ("default_owner", "TEXT DEFAULT 'Admin'"),
            ("state", "TEXT DEFAULT 'Working'"),
            ("created_date", "TEXT DEFAULT CURRENT_TIMESTAMP"),
        ]
        
        for column, definition in dongle_migrations:
            if column not in dongle_columns:
                try:
                    cursor.execute(f"ALTER TABLE dongles ADD COLUMN {column} {definition}")
                    self.conn.commit()
                except sqlite3.OperationalError:
                    pass  # Column might already exist or other issue
        
        # Add missing columns to assignments table
        if "notes" not in assignment_columns:
            try:
                cursor.execute("ALTER TABLE assignments ADD COLUMN notes TEXT DEFAULT ''")
                self.conn.commit()
            except sqlite3.OperationalError:
                pass
        
        self._remove_deprecated_columns()
    
    def _remove_deprecated_columns(self) -> None:
        """Remove deprecated columns from dongles table."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(dongles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'modules' in columns or 'location' in columns:
                # Create new table without deprecated columns
                cursor.execute('''
                    CREATE TABLE dongles_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dongle_id TEXT UNIQUE,
                        halcon_version TEXT,
                        notes TEXT,
                        default_owner TEXT DEFAULT 'Admin',
                        state TEXT DEFAULT 'Working',
                        created_date TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Copy data from old table
                cursor.execute('''
                    INSERT INTO dongles_new (id, dongle_id, halcon_version, notes, default_owner, state, created_date)
                    SELECT id, dongle_id, halcon_version, 
                           COALESCE(notes, ''), 
                           COALESCE(default_owner, 'Admin'),
                           COALESCE(state, 'Working'),
                           COALESCE(created_date, datetime('now'))
                    FROM dongles
                ''')
                
                # Replace old table
                cursor.execute("DROP TABLE dongles")
                cursor.execute("ALTER TABLE dongles_new RENAME TO dongles")
                
        except sqlite3.OperationalError:
            pass  # Tables might not exist or already be correct
    
    def get_all_dongles(self) -> List[Dict[str, Any]]:
        """Get all dongles with their current status."""
        cursor = self.conn.cursor()
        
        # Check what columns actually exist
        try:
            cursor.execute("PRAGMA table_info(dongles)")
            available_columns = [col[1] for col in cursor.fetchall()]
            
            # Build query based on available columns
            base_columns = ["id", "dongle_id"]
            optional_columns = ["halcon_version", "notes", "default_owner", "state", "created_date"]
            
            select_columns = base_columns.copy()
            for col in optional_columns:
                if col in available_columns:
                    select_columns.append(col)
            
            query = f"SELECT {', '.join(select_columns)} FROM dongles ORDER BY dongle_id"
            rows = cursor.execute(query).fetchall()
            active_assignments = self._get_active_assignments()
            
            dongles = []
            for row in rows:
                # Map columns dynamically based on what's available
                row_dict = dict(zip(select_columns, row))
                
                dongle_dict = {
                    'id': row_dict.get('id'),
                    'dongle_id': row_dict.get('dongle_id', 'Unknown'),
                    'halcon_version': row_dict.get('halcon_version') or 'N/A',
                    'notes': row_dict.get('notes') or '',
                    'default_owner': row_dict.get('default_owner') or 'Admin',
                    'state': row_dict.get('state') or 'Working',
                    'created_date': row_dict.get('created_date', ''),
                    'assigned_to': active_assignments.get(row_dict.get('dongle_id'), (None, None))[0],
                    'assignment_date': active_assignments.get(row_dict.get('dongle_id'), (None, None))[1],
                }
                dongles.append(dongle_dict)
            
            return dongles
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get dongles: {e}")
    
    def _get_active_assignments(self) -> Dict[str, Tuple[Optional[str], Optional[str]]]:
        """Get currently active assignments."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT a1.dongle_id, a1.assigned_to, a1.date 
            FROM assignments a1
            WHERE a1.action = 'check_out'
            AND a1.date = (
                SELECT MAX(a2.date) 
                FROM assignments a2 
                WHERE a2.dongle_id = a1.dongle_id
            )
            AND a1.dongle_id NOT IN (
                SELECT a3.dongle_id 
                FROM assignments a3 
                WHERE a3.action = 'check_in' 
                AND a3.date > a1.date
            )
        '''
        
        try:
            rows = cursor.execute(query).fetchall()
            return {row[0]: (row[1], row[2]) for row in rows}
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get active assignments: {e}")
    
    def add_dongle(self, dongle_id: str, halcon_version: str, notes: str, 
                   default_owner: str, state: DongleState) -> None:
        """Add a new dongle."""
        cursor = self.conn.cursor()
        
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO dongles (dongle_id, halcon_version, notes, default_owner, state, created_date) VALUES (?, ?, ?, ?, ?, ?)",
                (dongle_id, halcon_version, notes, default_owner, state.value, today)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise DatabaseError(f"Dongle ID '{dongle_id}' already exists")
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to add dongle: {e}")
    
    def get_available_dongles(self) -> List[str]:
        """Get available dongles for checkout."""
        cursor = self.conn.cursor()
        
        try:
            # Get working dongles
            working_dongles = cursor.execute(
                "SELECT dongle_id FROM dongles WHERE state = ? ORDER BY dongle_id",
                (DongleState.WORKING.value,)
            ).fetchall()
            
            # Get checked out dongles
            checked_out_query = '''
                SELECT DISTINCT a1.dongle_id 
                FROM assignments a1
                WHERE a1.action = 'check_out'
                AND a1.date = (
                    SELECT MAX(a2.date) 
                    FROM assignments a2 
                    WHERE a2.dongle_id = a1.dongle_id
                )
                AND a1.dongle_id NOT IN (
                    SELECT a3.dongle_id 
                    FROM assignments a3 
                    WHERE a3.action = 'check_in' 
                    AND a3.date > a1.date
                )
            '''
            
            checked_out_ids = {row[0] for row in cursor.execute(checked_out_query).fetchall()}
            
            # Return available dongles
            return [dongle[0] for dongle in working_dongles if dongle[0] not in checked_out_ids]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get available dongles: {e}")
    
    def check_out_dongle(self, dongle_id: str, assigned_to: str, notes: str = "") -> None:
        """Check out a dongle."""
        cursor = self.conn.cursor()
        
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO assignments (dongle_id, assigned_to, action, date, notes) VALUES (?, ?, ?, ?, ?)",
                (dongle_id, assigned_to, ActionType.CHECK_OUT.value, today, notes)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to check out dongle: {e}")
    
    def get_checked_out_dongles(self) -> List[Tuple[str, str, str]]:
        """Get currently checked out dongles."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT a1.dongle_id, a1.assigned_to, a1.date
            FROM assignments a1
            WHERE a1.action = 'check_out'
            AND a1.date = (
                SELECT MAX(a2.date) 
                FROM assignments a2 
                WHERE a2.dongle_id = a1.dongle_id
            )
            AND a1.dongle_id NOT IN (
                SELECT a3.dongle_id 
                FROM assignments a3 
                WHERE a3.action = 'check_in' 
                AND a3.date > a1.date
            )
            ORDER BY a1.date DESC
        '''
        
        try:
            return cursor.execute(query).fetchall()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get checked out dongles: {e}")
    
    def check_in_dongle(self, dongle_id: str, notes: str = "") -> None:
        """Check in a dongle."""
        cursor = self.conn.cursor()
        
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO assignments (dongle_id, assigned_to, action, date, notes) VALUES (?, ?, ?, ?, ?)",
                (dongle_id, '', ActionType.CHECK_IN.value, today, notes)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to check in dongle: {e}")
    
    def update_dongle(self, dongle_id: str, notes: str, default_owner: str, 
                      state: DongleState, changed_by: str, change_notes: str) -> List[str]:
        """Update dongle information and track changes."""
        cursor = self.conn.cursor()
        
        try:
            # Get current data
            current_data = cursor.execute(
                "SELECT notes, default_owner, state FROM dongles WHERE dongle_id = ?",
                (dongle_id,)
            ).fetchone()
            
            if not current_data:
                raise DatabaseError(f"Dongle '{dongle_id}' not found")
            
            changes_made = []
            today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Track changes
            if default_owner != current_data[1]:
                changes_made.append("default_owner")
                cursor.execute(
                    "INSERT INTO dongle_edits (dongle_id, field_changed, old_value, new_value, changed_by, change_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (dongle_id, "Default Owner", current_data[1], default_owner, changed_by, today, change_notes)
                )
            
            if state.value != current_data[2]:
                changes_made.append("state")
                cursor.execute(
                    "INSERT INTO dongle_edits (dongle_id, field_changed, old_value, new_value, changed_by, change_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (dongle_id, "State", current_data[2], state.value, changed_by, today, change_notes)
                )
            
            if notes != current_data[0]:
                changes_made.append("notes")
                cursor.execute(
                    "INSERT INTO dongle_edits (dongle_id, field_changed, old_value, new_value, changed_by, change_date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (dongle_id, "Notes", current_data[0], notes, changed_by, today, change_notes)
                )
            
            if changes_made:
                # Update the dongle
                cursor.execute(
                    "UPDATE dongles SET notes = ?, default_owner = ?, state = ? WHERE dongle_id = ?",
                    (notes, default_owner, state.value, dongle_id)
                )
                self.conn.commit()
            
            return changes_made
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to update dongle: {e}")
    
    def get_dongle_edit_history(self, dongle_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get edit history for a dongle."""
        cursor = self.conn.cursor()
        
        try:
            rows = cursor.execute(
                "SELECT field_changed, old_value, new_value, changed_by, change_date, notes FROM dongle_edits WHERE dongle_id = ? ORDER BY change_date DESC LIMIT ?",
                (dongle_id, limit)
            ).fetchall()
            
            return [
                {
                    'field': row[0],
                    'old_value': row[1],
                    'new_value': row[2],
                    'changed_by': row[3],
                    'change_date': row[4],
                    'notes': row[5]
                }
                for row in rows
            ]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get edit history: {e}")
    
    def get_assignment_history(self, dongle_filter: str = None, assignee_filter: str = None, 
                              action_filter: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get assignment history with filters."""
        cursor = self.conn.cursor()
        
        try:
            query = "SELECT dongle_id, assigned_to, action, date, COALESCE(notes, '') as notes FROM assignments"
            params = []
            conditions = []
            
            if dongle_filter:
                conditions.append("dongle_id = ?")
                params.append(dongle_filter)
            
            if assignee_filter:
                conditions.append("assigned_to = ?")
                params.append(assignee_filter)
            
            if action_filter:
                action_value = ActionType.CHECK_OUT.value if action_filter == "Check Out" else ActionType.CHECK_IN.value
                conditions.append("action = ?")
                params.append(action_value)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY date DESC LIMIT {limit}"
            
            rows = cursor.execute(query, params).fetchall()
            
            return [
                {
                    'dongle_id': row[0],
                    'assigned_to': row[1],
                    'action': row[2],
                    'date': row[3],
                    'notes': row[4]
                }
                for row in rows
            ]
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get assignment history: {e}")
    
    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get filter options for dropdowns."""
        cursor = self.conn.cursor()
        
        try:
            dongle_ids = [row[0] for row in cursor.execute("SELECT DISTINCT dongle_id FROM assignments ORDER BY dongle_id").fetchall()]
            assignees = [row[0] for row in cursor.execute("SELECT DISTINCT assigned_to FROM assignments WHERE assigned_to != '' ORDER BY assigned_to").fetchall()]
            editors = [row[0] for row in cursor.execute("SELECT DISTINCT changed_by FROM dongle_edits WHERE changed_by != '' ORDER BY changed_by").fetchall()]
            fields = [row[0] for row in cursor.execute("SELECT DISTINCT field_changed FROM dongle_edits ORDER BY field_changed").fetchall()]
            
            return {
                'dongle_ids': dongle_ids,
                'assignees': assignees,
                'editors': editors,
                'fields': fields
            }
            
        except sqlite3.Error as e:
            raise DatabaseError(f"Failed to get filter options: {e}")
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None