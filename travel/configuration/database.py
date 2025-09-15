import psycopg2
import json
import os
import logging
import toml

from dotenv import load_dotenv

# Try to load from multiple sources
load_dotenv()  # Load from .env file
load_dotenv('config.env')  # Load from config.env file

class DatabaseManager:
    def __init__(self):
        # Debug: Print environment variables
        print(f"[DEBUG] DB_HOST: {os.getenv('DB_HOST')}")
        print(f"[DEBUG] DB_NAME: {os.getenv('DB_NAME')}")
        print(f"[DEBUG] DB_USER: {os.getenv('DB_USER')}")
        print(f"[DEBUG] DB_PORT: {os.getenv('DB_PORT')}")
        
        self.connection_params = {
            'host': os.getenv('DB_HOST'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'sslmode': os.getenv('DB_SSLMODE', 'require')
        }
        
        # Validate required parameters
        if not self.connection_params['host']:
            logging.error("DB_HOST environment variable not set!")
            raise ValueError("DB_HOST environment variable is required")
        if not self.connection_params['database']:
            logging.error("DB_NAME environment variable not set!")
            raise ValueError("DB_NAME environment variable is required")
        if not self.connection_params['user']:
            logging.error("DB_USER environment variable not set!")
            raise ValueError("DB_USER environment variable is required")
        if not self.connection_params['password']:
            logging.error("DB_PASSWORD environment variable not set!")
            raise ValueError("DB_PASSWORD environment variable is required")
            
        logging.info(f"Using database: {self.connection_params['database']} on host {self.connection_params['host']}")
        self.init_database()

    def get_connection(self):
        try:
            return psycopg2.connect(**self.connection_params)
        except psycopg2.OperationalError as e:
            logging.error(f"Database connection error: {e}")
            return None

    def init_database(self):
        """Initialize database tables if they don't exist"""
        conn = self.get_connection()
        if not conn:
            logging.error("Cannot initialize database because connection failed.")
            return

        try:
            cursor = conn.cursor()

            # Create users table
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            user_id VARCHAR(255) PRIMARY KEY,
                            email VARCHAR(255) UNIQUE,
                            preferences JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

            # Create conversations table (legacy)
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS conversations (
                            id SERIAL PRIMARY KEY,
                            user_id VARCHAR(255) REFERENCES users(user_id),
                            conversation_data JSONB,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            session_id VARCHAR(255)
                        )
                    """)

            # Create conversation_sessions table for chat history
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS conversation_sessions (
                            session_id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) REFERENCES users(user_id),
                            title VARCHAR(500) NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            message_count INTEGER DEFAULT 0
                        )
                    """)

            # Create conversation_messages table for individual messages
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS conversation_messages (
                            id SERIAL PRIMARY KEY,
                            session_id VARCHAR(255) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
                            user_id VARCHAR(255) REFERENCES users(user_id),
                            message_data JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)

            # Create user_sessions table for tracking (legacy)
            cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            session_id VARCHAR(255) PRIMARY KEY,
                            user_id VARCHAR(255) REFERENCES users(user_id),
                            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            end_time TIMESTAMP,
                            messages_count INTEGER DEFAULT 0
                        )
                    """)

            conn.commit()
            cursor.close()
            conn.close()

        except psycopg2.Error as e:
            logging.error(f"Database initialization error: {e}")

    def get_user_data(self, user_id):  # <--- This should be aligned with init_database
        """Get user data including preferences and recent conversations"""
        try:
            conn = self.get_connection()
            if not conn:
                return {'preferences': {}, 'conversations': []}

            cursor = conn.cursor()

            # Get user preferences
            cursor.execute("SELECT preferences FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            preferences = result[0] if result else {}

            # Get recent conversations (last 10)
            cursor.execute("""
                SELECT conversation_data FROM conversations 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (user_id,))

            conversations = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()

            return {
                'preferences': preferences,
                'conversations': conversations
            }

        except psycopg2.Error as e:
            logging.error(f"Error getting user data: {e}")
            return {'preferences': {}, 'conversations': []}
    def update_user_preferences(self, user_id, preferences):
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO users (user_id, preferences, last_active)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET 
                    preferences = %s,
                    last_active = CURRENT_TIMESTAMP
                """, (user_id, json.dumps(preferences), json.dumps(preferences)))

            conn.commit()
            cursor.close()
            conn.close()
            return True
        except psycopg2.Error as e:
            logging.error(f"Error updating user preferences: {e}")
            return False

    def save_conversation(self, user_id, conversation_data):
            """Save conversation to database"""
            try:
                conn = self.get_connection()
                if not conn:
                    return False

                cursor = conn.cursor()

                # Ensure user exists
                cursor.execute("""
                        INSERT INTO users (user_id, last_active)
                        VALUES (%s, CURRENT_TIMESTAMP)
                        ON CONFLICT (user_id) 
                        DO UPDATE SET last_active = CURRENT_TIMESTAMP
                    """, (user_id,))

                # Save conversation
                cursor.execute("""
                        INSERT INTO conversations (user_id, conversation_data)
                        VALUES (%s, %s)
                    """, (user_id, json.dumps(conversation_data)))

                conn.commit()
                cursor.close()
                conn.close()
                return True

            except psycopg2.Error as e:
                logging.error(f"Error saving conversation: {e}")
                return False

    def clear_user_conversations(self, user_id):
        """Clear all conversations for a user"""
        try:
            conn = self.get_connection()
            if not conn:
                return False

            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE user_id = %s", (user_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True

        except psycopg2.Error as e:
            logging.error(f"Error clearing conversations: {e}")
            return False

    def get_conversation_count(self, user_id):
        """Get total conversation count for user"""
        try:
            conn = self.get_connection()
            if not conn:
                return 0

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            count = result[0] if result else 0
            cursor.close()
            conn.close()
            return count

        except psycopg2.Error as e:
            logging.error(f"Error getting conversation count: {e}")
            return 0

    def get_user_analytics(self, user_id):
        """Get analytics data for user"""
        try:
            conn = self.get_connection()
            if not conn:
                return {}

            cursor = conn.cursor()

            # Get various metrics
            analytics = {}

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM conversations WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            analytics['total_conversations'] = result[0] if result else 0

            # First interaction
            cursor.execute("""
                    SELECT MIN(created_at) FROM conversations WHERE user_id = %s
                """, (user_id,))
            result = cursor.fetchone()
            first_interaction = result[0] if result else None
            analytics['first_interaction'] = first_interaction.isoformat() if first_interaction else None

            # Last interaction
            cursor.execute("""
                    SELECT MAX(created_at) FROM conversations WHERE user_id = %s
                """, (user_id,))
            result = cursor.fetchone()
            last_interaction = result[0] if result else None
            analytics['last_interaction'] = last_interaction.isoformat() if last_interaction else None

            cursor.close()
            conn.close()
            return analytics

        except psycopg2.Error as e:
            logging.error(f"Error getting analytics: {e}")
            return {}
