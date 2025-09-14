import uuid
import datetime
from typing import Dict, List, Optional, Tuple
from database import DatabaseManager
import json
import logging


class ConversationManager:
    def __init__(self, db_manager: DatabaseManager):
        """Initialize conversation manager with database connection"""
        self.db_manager = db_manager

    def create_new_session(self, user_id: str, title: str = None) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())

        # Auto-generate title if not provided
        if title is None:
            title = f"Travel Chat - {datetime.datetime.now().strftime('%m/%d %H:%M')}"

        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return session_id

            cursor = conn.cursor()

            # Create new session record
            cursor.execute("""
                INSERT INTO conversation_sessions 
                (session_id, user_id, title, created_at, last_updated)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (session_id, user_id, title))

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logging.error(f"Error creating session: {e}")

        return session_id

    def get_user_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get all conversation sessions for a user"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return []

            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, title, created_at, last_updated, message_count
                FROM conversation_sessions 
                WHERE user_id = %s 
                ORDER BY last_updated DESC 
                LIMIT %s
            """, (user_id, limit))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'session_id': row[0],
                    'title': row[1],
                    'created_at': row[2],
                    'last_updated': row[3],
                    'message_count': row[4] or 0
                })

            cursor.close()
            conn.close()
            return sessions

        except Exception as e:
            logging.error(f"Error getting sessions: {e}")
            return []

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get all messages from a specific session"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return []

            cursor = conn.cursor()

            cursor.execute("""
                SELECT message_data, created_at
                FROM conversation_messages 
                WHERE session_id = %s 
                ORDER BY created_at ASC
            """, (session_id,))

            messages = []
            for row in cursor.fetchall():
                message_data = row[0]
                if isinstance(message_data, str):
                    message_data = json.loads(message_data)
                messages.append(message_data)

            cursor.close()
            conn.close()
            return messages

        except Exception as e:
            logging.error(f"Error getting session messages: {e}")
            return []

    def save_message_to_session(self, session_id: str, user_id: str, role: str, content: str,
                                metadata: Optional[Dict] = None):
        """Save a message to a specific session"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            message_data = {
                'role': role,
                'content': content,
                'timestamp': datetime.datetime.now().isoformat(),
                'metadata': metadata or {}
            }

            # Insert message
            cursor.execute("""
                INSERT INTO conversation_messages 
                (session_id, user_id, message_data, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """, (session_id, user_id, json.dumps(message_data)))

            # Update session last_updated and message count
            cursor.execute("""
                UPDATE conversation_sessions 
                SET last_updated = CURRENT_TIMESTAMP,
                    message_count = COALESCE(message_count, 0) + 1
                WHERE session_id = %s
            """, (session_id,))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logging.error(f"Error saving message: {e}")
            return False

    def update_session_title(self, session_id: str, new_title: str) -> bool:
        """Update the title of a conversation session"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            cursor.execute("""
                UPDATE conversation_sessions 
                SET title = %s, last_updated = CURRENT_TIMESTAMP
                WHERE session_id = %s
            """, (new_title, session_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logging.error(f"Error updating session title: {e}")
            return False

    def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a conversation session and all its messages"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            # Delete messages first (due to foreign key)
            cursor.execute("""
                DELETE FROM conversation_messages 
                WHERE session_id = %s AND user_id = %s
            """, (session_id, user_id))

            # Delete session
            cursor.execute("""
                DELETE FROM conversation_sessions 
                WHERE session_id = %s AND user_id = %s
            """, (session_id, user_id))

            conn.commit()
            cursor.close()
            conn.close()
            return True

        except Exception as e:
            logging.error(f"Error deleting session: {e}")
            return False

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a specific session"""
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                return None

            cursor = conn.cursor()

            cursor.execute("""
                SELECT session_id, user_id, title, created_at, last_updated, message_count
                FROM conversation_sessions 
                WHERE session_id = %s
            """, (session_id,))

            result = cursor.fetchone()
            if result:
                session_info = {
                    'session_id': result[0],
                    'user_id': result[1],
                    'title': result[2],
                    'created_at': result[3],
                    'last_updated': result[4],
                    'message_count': result[5] or 0
                }

                cursor.close()
                conn.close()
                return session_info

            cursor.close()
            conn.close()
            return None

        except Exception as e:
            logging.error(f"Error getting session info: {e}")
            return None

    def auto_generate_title(self, session_id: str, first_message: str) -> str:
        """Auto-generate a meaningful title based on the first message"""
        # Simple title generation - you can enhance this with AI
        words = first_message.split()[:6]  # First 6 words
        title = " ".join(words)

        if len(title) > 50:
            title = title[:47] + "..."
        elif len(title) < 10:
            title = f"Travel Chat - {datetime.datetime.now().strftime('%m/%d')}"

        # Update the session with new title
        self.update_session_title(session_id, title)
        return title