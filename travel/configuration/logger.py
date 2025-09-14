import logging
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional


class Logger:
    def __init__(self, log_file: str = "logs.txt", db_file: str = "monitoring.db"):
        """Initialize logging system with both file and SQLite storage"""
        self.log_file = log_file
        self.db_file = db_file

        # Setup file logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Initialize SQLite database
        self.init_db()

    def init_db(self):
        """Initialize SQLite database for monitoring"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Create logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    log_type TEXT,
                    message TEXT,
                    data JSON,
                    level TEXT DEFAULT 'INFO'
                )
            """)

            # Create user_activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    action_type TEXT,
                    details JSON,
                    session_id TEXT
                )
            """)

            # Create api_calls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    api_service TEXT,
                    request_data JSON,
                    response_data JSON,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    error_message TEXT
                )
            """)

            # Create error_logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    stack_trace TEXT,
                    context JSON
                )
            """)

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            self.logger.error(f"Database initialization error: {e}")

    def log_to_file(self, level: str, message: str, data: Optional[Dict] = None):
        """Log message to file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "data": data or {}
        }

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def log_to_db(self, user_id: str, log_type: str, message: str, data: Optional[Dict] = None, level: str = "INFO"):
        """Log to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO logs (user_id, log_type, message, data, level)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, log_type, message, json.dumps(data or {}), level))

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            self.logger.error(f"Database logging error: {e}")

    def log_user_input(self, user_id: str, user_input: str, metadata: Optional[Dict] = None):
        """Log user input"""
        message = f"User input received: {user_input[:100]}{'...' if len(user_input) > 100 else ''}"
        data = {
            "full_input": user_input,
            "input_length": len(user_input),
            "metadata": metadata or {}
        }

        # Log to both file and database
        self.log_to_file("INFO", message, data)
        self.log_to_db(user_id, "user_input", message, data)

        # Log user activity
        self.log_user_activity(user_id, "message_sent", {
            "message_length": len(user_input),
            "timestamp": datetime.now().isoformat()
        })

        self.logger.info(f"User {user_id} sent message: {len(user_input)} characters")

    def log_ai_response(self, user_id: str, ai_response: str, response_length: int, metadata: Optional[Dict] = None):
        """Log AI response"""
        message = f"AI response generated: {response_length} characters"
        data = {
            "response_preview": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
            "response_length": response_length,
            "full_response_stored": True,
            "metadata": metadata or {}
        }

        # Log to both file and database
        self.log_to_file("INFO", message, data)
        self.log_to_db(user_id, "ai_response", message, data)

        self.logger.info(f"AI response generated for user {user_id}: {response_length} characters")

    def log_user_activity(self, user_id: str, action_type: str, details: Optional[Dict] = None):
        """Log user activity"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO user_activity (user_id, action_type, details)
                VALUES (?, ?, ?)
            """, (user_id, action_type, json.dumps(details or {})))

            conn.commit()
            conn.close()

            self.logger.info(f"User activity: {user_id} - {action_type}")

        except sqlite3.Error as e:
            self.logger.error(f"Error logging user activity: {e}")

    def log_user_action(self, user_id: str, action: str, details: Optional[Dict] = None):
        """Log specific user actions (login, logout, etc.)"""
        message = f"User action: {action}"
        data = {
            "action": action,
            "user_id": user_id,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }

        self.log_to_file("INFO", message, data)
        self.log_to_db(user_id, "user_action", message, data)
        self.log_user_activity(user_id, action, details)

    def log_api_call(self, user_id: str, api_service: str, request_data: Dict,
                     response_data: Optional[Dict] = None, status_code: Optional[int] = None,
                     response_time_ms: Optional[int] = None, error_message: Optional[str] = None):
        """Log API calls"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO api_calls 
                (user_id, api_service, request_data, response_data, status_code, response_time_ms, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, api_service, json.dumps(request_data),
                json.dumps(response_data or {}), status_code, response_time_ms, error_message
            ))

            conn.commit()
            conn.close()

            # Also log to file
            message = f"API call to {api_service}: status {status_code}"
            self.log_to_file("INFO", message, {
                "api_service": api_service,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "error": error_message
            })

        except sqlite3.Error as e:
            self.logger.error(f"Error logging API call: {e}")

    def log_error(self, user_id: str, error_type: str, context: Optional[Dict] = None,
                  stack_trace: Optional[str] = None):
        """Log errors"""
        error_message = f"Error occurred: {error_type}"

        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO error_logs (user_id, error_type, error_message, stack_trace, context)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, error_type, error_message, stack_trace, json.dumps(context or {})))

            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            self.logger.error(f"Error logging to database: {e}")

        # Log to file regardless
        self.log_to_file("ERROR", error_message, {
            "error_type": error_type,
            "context": context or {},
            "stack_trace": stack_trace
        })

        self.logger.error(f"Error for user {user_id}: {error_type}")

    def get_user_stats(self, user_id: str) -> Dict:
        """Get statistics for a specific user"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            stats = {}

            # Get total messages
            cursor.execute("SELECT COUNT(*) FROM logs WHERE user_id = ? AND log_type = 'user_input'", (user_id,))
            stats['total_messages'] = cursor.fetchone()[0]

            # Get total AI responses
            cursor.execute("SELECT COUNT(*) FROM logs WHERE user_id = ? AND log_type = 'ai_response'", (user_id,))
            stats['total_responses'] = cursor.fetchone()[0]

            # Get error count
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE user_id = ?", (user_id,))
            stats['total_errors'] = cursor.fetchone()[0]

            # Get first activity
            cursor.execute("SELECT MIN(timestamp) FROM logs WHERE user_id = ?", (user_id,))
            first_activity = cursor.fetchone()[0]
            stats['first_activity'] = first_activity

            # Get recent activity count (last 24 hours)
            cursor.execute("""
                SELECT COUNT(*) FROM user_activity 
                WHERE user_id = ? AND timestamp > datetime('now', '-1 day')
            """, (user_id,))
            stats['recent_activity_count'] = cursor.fetchone()[0]

            conn.close()
            return stats

        except sqlite3.Error as e:
            self.logger.error(f"Error getting user stats: {e}")
            return {}

    def get_system_stats(self) -> Dict:
        """Get overall system statistics"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            stats = {}

            # Total users
            cursor.execute("SELECT COUNT(DISTINCT user_id) FROM logs")
            stats['total_users'] = cursor.fetchone()[0]

            # Total messages today
            cursor.execute("""
                SELECT COUNT(*) FROM logs 
                WHERE log_type = 'user_input' AND date(timestamp) = date('now')
            """)
            stats['messages_today'] = cursor.fetchone()[0]

            # Total errors today
            cursor.execute("SELECT COUNT(*) FROM error_logs WHERE date(timestamp) = date('now')")
            stats['errors_today'] = cursor.fetchone()[0]

            # Average response time (if tracked)
            cursor.execute("SELECT AVG(response_time_ms) FROM api_calls WHERE response_time_ms IS NOT NULL")
            avg_response = cursor.fetchone()[0]
            stats['avg_response_time_ms'] = round(avg_response) if avg_response else 0

            conn.close()
            return stats

        except sqlite3.Error as e:
            self.logger.error(f"Error getting system stats: {e}")
            return {}

    def cleanup_old_logs(self, days_to_keep: int = 30):
        """Clean up logs older than specified days"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Delete old logs
            cursor.execute("""
                DELETE FROM logs 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            cursor.execute("""
                DELETE FROM user_activity 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            cursor.execute("""
                DELETE FROM api_calls 
                WHERE timestamp < datetime('now', '-{} days')
            """.format(days_to_keep))

            # Keep error logs longer (90 days)
            cursor.execute("""
                DELETE FROM error_logs 
                WHERE timestamp < datetime('now', '-90 days')
            """)

            conn.commit()
            deleted_count = cursor.rowcount
            conn.close()

            self.logger.info(f"Cleaned up {deleted_count} old log entries")
            return deleted_count

        except sqlite3.Error as e:
            self.logger.error(f"Error cleaning up logs: {e}")
            return 0