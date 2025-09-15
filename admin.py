import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import os
import sys

# Add the travel configuration directory to the path
sys.path.append('travel/configuration')

try:
    from database import DatabaseManager
    from logger import Logger
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

def main():
    st.set_page_config(
        page_title="Travel Assistant Admin Dashboard",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Travel Assistant Admin Dashboard")
    st.markdown("---")
    
    # Initialize components
    try:
        db_manager = DatabaseManager()
        logger = Logger()
    except Exception as e:
        st.error(f"Error initializing components: {e}")
        return
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📈 Dashboard Sections")
        section = st.selectbox(
            "Choose a section:",
            ["Overview", "User Analytics", "System Statistics", "Recent Activity", "Database Tables"]
        )
    
    if section == "Overview":
        show_overview(db_manager, logger)
    elif section == "User Analytics":
        show_user_analytics(db_manager, logger)
    elif section == "System Statistics":
        show_system_statistics(logger)
    elif section == "Recent Activity":
        show_recent_activity(logger)
    elif section == "Database Tables":
        show_database_tables(db_manager)

def show_overview(db_manager, logger):
    """Show overview metrics"""
    st.header("📊 System Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get system stats
        system_stats = logger.get_system_stats()
        
        with col1:
            st.metric(
                label="Total Users",
                value=system_stats.get('total_users', 0),
                delta=None
            )
        
        with col2:
            st.metric(
                label="Messages Today",
                value=system_stats.get('messages_today', 0),
                delta=None
            )
        
        with col3:
            st.metric(
                label="Errors Today",
                value=system_stats.get('errors_today', 0),
                delta=None
            )
        
        with col4:
            avg_response = system_stats.get('avg_response_time_ms', 0)
            st.metric(
                label="Avg Response Time",
                value=f"{avg_response}ms" if avg_response > 0 else "N/A",
                delta=None
            )
    
    except Exception as e:
        st.error(f"Error loading overview: {e}")
    
    # Recent activity chart
    st.subheader("📈 Recent Activity (Last 7 Days)")
    try:
        conn = sqlite3.connect("travel/monitoring.db")
        
        # Get daily activity for last 7 days
        query = """
        SELECT 
            date(timestamp) as date,
            COUNT(*) as activity_count
        FROM user_activity 
        WHERE timestamp > datetime('now', '-7 days')
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            st.line_chart(df.set_index('date'))
        else:
            st.info("No recent activity data available")
            
    except Exception as e:
        st.error(f"Error loading activity chart: {e}")

def show_user_analytics(db_manager, logger):
    """Show detailed user analytics"""
    st.header("👥 User Analytics")
    
    try:
        conn = sqlite3.connect("travel/monitoring.db")
        
        # Get all unique users
        users_query = """
        SELECT DISTINCT user_id, 
               MIN(timestamp) as first_seen,
               MAX(timestamp) as last_seen,
               COUNT(*) as total_activities
        FROM user_activity 
        GROUP BY user_id
        ORDER BY first_seen DESC
        """
        
        users_df = pd.read_sql_query(users_query, conn)
        
        if not users_df.empty:
            st.subheader("📋 All Users")
            
            # Format the dataframe for better display
            users_df['first_seen'] = pd.to_datetime(users_df['first_seen']).dt.strftime('%Y-%m-%d %H:%M')
            users_df['last_seen'] = pd.to_datetime(users_df['last_seen']).dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                users_df,
                use_container_width=True,
                column_config={
                    "user_id": "User ID",
                    "first_seen": "First Seen",
                    "last_seen": "Last Seen", 
                    "total_activities": "Total Activities"
                }
            )
            
            # User details
            st.subheader("🔍 User Details")
            selected_user = st.selectbox(
                "Select a user to view details:",
                users_df['user_id'].tolist()
            )
            
            if selected_user:
                show_user_details(selected_user, db_manager, logger)
        else:
            st.info("No user data available")
            
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading user analytics: {e}")

def show_user_details(user_id, db_manager, logger):
    """Show detailed information for a specific user"""
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 User Statistics")
            
            # Get user stats from logger
            user_stats = logger.get_user_stats(user_id)
            
            st.metric("Total Messages", user_stats.get('total_messages', 0))
            st.metric("Total AI Responses", user_stats.get('total_responses', 0))
            st.metric("Total Errors", user_stats.get('total_errors', 0))
            st.metric("Recent Activity (24h)", user_stats.get('recent_activity_count', 0))
            
            if user_stats.get('first_activity'):
                st.write(f"**First Activity:** {user_stats['first_activity']}")
        
        with col2:
            st.subheader("🗄️ Database Analytics")
            
            # Get user analytics from database
            db_analytics = db_manager.get_user_analytics(user_id)
            
            st.metric("Total Conversations", db_analytics.get('total_conversations', 0))
            
            if db_analytics.get('first_interaction'):
                st.write(f"**First Interaction:** {db_analytics['first_interaction']}")
            
            if db_analytics.get('last_interaction'):
                st.write(f"**Last Interaction:** {db_analytics['last_interaction']}")
        
        # Recent activity for this user
        st.subheader("📝 Recent Activity")
        try:
            conn = sqlite3.connect("travel/monitoring.db")
            
            activity_query = """
            SELECT timestamp, action_type, details
            FROM user_activity 
            WHERE user_id = ?
            ORDER BY timestamp DESC
            LIMIT 10
            """
            
            activity_df = pd.read_sql_query(activity_query, conn, params=(user_id,))
            conn.close()
            
            if not activity_df.empty:
                activity_df['timestamp'] = pd.to_datetime(activity_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
                st.dataframe(activity_df, use_container_width=True)
            else:
                st.info("No recent activity for this user")
                
        except Exception as e:
            st.error(f"Error loading user activity: {e}")
            
    except Exception as e:
        st.error(f"Error loading user details: {e}")

def show_system_statistics(logger):
    """Show system-wide statistics"""
    st.header("⚙️ System Statistics")
    
    try:
        conn = sqlite3.connect("travel/monitoring.db")
        
        # API calls statistics
        st.subheader("🔌 API Calls")
        api_query = """
        SELECT 
            api_service,
            COUNT(*) as total_calls,
            AVG(response_time_ms) as avg_response_time,
            COUNT(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 END) as successful_calls,
            COUNT(CASE WHEN status_code >= 400 THEN 1 END) as error_calls
        FROM api_calls 
        GROUP BY api_service
        """
        
        api_df = pd.read_sql_query(api_query, conn)
        
        if not api_df.empty:
            api_df['avg_response_time'] = api_df['avg_response_time'].round(2)
            st.dataframe(api_df, use_container_width=True)
        else:
            st.info("No API call data available")
        
        # Error statistics
        st.subheader("❌ Error Statistics")
        error_query = """
        SELECT 
            error_type,
            COUNT(*) as error_count,
            MAX(timestamp) as last_occurrence
        FROM error_logs 
        GROUP BY error_type
        ORDER BY error_count DESC
        """
        
        error_df = pd.read_sql_query(error_query, conn)
        
        if not error_df.empty:
            error_df['last_occurrence'] = pd.to_datetime(error_df['last_occurrence']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(error_df, use_container_width=True)
        else:
            st.info("No error data available")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading system statistics: {e}")

def show_recent_activity(logger):
    """Show recent activity logs"""
    st.header("📝 Recent Activity")
    
    try:
        conn = sqlite3.connect("travel/monitoring.db")
        
        # Recent logs
        logs_query = """
        SELECT timestamp, user_id, log_type, message, level
        FROM logs 
        ORDER BY timestamp DESC
        LIMIT 50
        """
        
        logs_df = pd.read_sql_query(logs_query, conn)
        
        if not logs_df.empty:
            logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            
            # Filter options
            log_level = st.selectbox("Filter by log level:", ["All", "INFO", "ERROR", "WARNING"])
            if log_level != "All":
                logs_df = logs_df[logs_df['level'] == log_level]
            
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info("No recent logs available")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")

def show_database_tables(db_manager):
    """Show database table information"""
    st.header("🗄️ Database Tables")
    
    try:
        conn = db_manager.get_connection()
        if not conn:
            st.error("Could not connect to database")
            return
        
        cursor = conn.cursor()
        
        # Get table information
        cursor.execute("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            st.subheader("📋 Available Tables")
            
            for table_name, column_count in tables:
                with st.expander(f"📊 {table_name} ({column_count} columns)"):
                    # Get row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    row_count = cursor.fetchone()[0]
                    st.write(f"**Rows:** {row_count}")
                    
                    # Get column information
                    cursor.execute(f"""
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns 
                        WHERE table_name = '{table_name}'
                        ORDER BY ordinal_position
                    """)
                    
                    columns = cursor.fetchall()
                    
                    if columns:
                        col_df = pd.DataFrame(columns, columns=['Column', 'Type', 'Nullable'])
                        st.dataframe(col_df, use_container_width=True)
                    
                    # Show sample data
                    if st.button(f"Show Sample Data", key=f"sample_{table_name}"):
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                        sample_data = cursor.fetchall()
                        
                        if sample_data:
                            # Get column names
                            cursor.execute(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}'
                                ORDER BY ordinal_position
                            """)
                            column_names = [row[0] for row in cursor.fetchall()]
                            
                            sample_df = pd.DataFrame(sample_data, columns=column_names)
                            st.dataframe(sample_df, use_container_width=True)
                        else:
                            st.info("No data in this table")
        else:
            st.info("No tables found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading database tables: {e}")

if __name__ == "__main__":
    main()
