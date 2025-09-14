import streamlit as st
import hashlib
import os
from datetime import datetime


class AuthManager:
    def __init__(self):
        """Initialize authentication manager"""
        # You can change this password or make it configurable
        self.app_password = os.getenv("APP_PASSWORD", "travel2024!")
        self.session_timeout = 3600  # 1 hour in seconds

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return password == self.app_password

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        if "authenticated" not in st.session_state:
            return False

        if "auth_time" not in st.session_state:
            return False

        # Check session timeout
        current_time = datetime.now().timestamp()
        if current_time - st.session_state.auth_time > self.session_timeout:
            # Session expired
            self.logout()
            return False

        return st.session_state.authenticated

    def login(self, password: str) -> bool:
        """Authenticate user with password"""
        if self.verify_password(password):
            st.session_state.authenticated = True
            st.session_state.auth_time = datetime.now().timestamp()
            return True
        return False

    def logout(self):
        """Logout user"""
        st.session_state.authenticated = False
        if "auth_time" in st.session_state:
            del st.session_state.auth_time

    def refresh_session(self):
        """Refresh authentication session"""
        if self.is_authenticated():
            st.session_state.auth_time = datetime.now().timestamp()


def authenticate_user() -> bool:
    """Main authentication function for Streamlit app"""
    auth_manager = AuthManager()

    if auth_manager.is_authenticated():
        # Refresh session on activity
        auth_manager.refresh_session()
        return True

    # Show login form
    st.title(" Travel Assistant - Authentication")
    st.markdown("Please enter the application password to continue.")

    with st.form("login_form"):
        password = st.text_input("Password", type="password", placeholder="Enter application password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if password:
                if auth_manager.login(password):
                    st.success("Authentication successful! Welcome to Travel Assistant.")
                    st.rerun()
                else:
                    st.error(" Invalid password. Please try again.")
            else:
                st.warning("Please enter a password.")

    # Show password hint for demo purposes
    with st.expander(" Password Information"):
        st.info("""
        **Default Password:** travel2024!

        I""")

    return False


def show_logout_option():
    """Show logout option in sidebar"""
    auth_manager = AuthManager()

    if auth_manager.is_authenticated():
        with st.sidebar:
            st.markdown("---")
            if st.button("Logout", key="logout_button"):
                auth_manager.logout()
                st.success("Logged out successfully!")
                st.rerun()

            # Show session info
            with st.expander("Session Info"):
                auth_time = datetime.fromtimestamp(st.session_state.auth_time)
                st.text(f"Logged in: {auth_time.strftime('%Y-%m-%d %H:%M:%S')}")

                # Calculate remaining time
                current_time = datetime.now().timestamp()
                remaining = auth_manager.session_timeout - (current_time - st.session_state.auth_time)
                if remaining > 0:
                    remaining_minutes = int(remaining // 60)
                    st.text(f"Session expires in: {remaining_minutes} minutes")
                else:
                    st.text("Session expired")


# Add logout option to the main app
def add_auth_sidebar():
    """Add authentication sidebar elements"""
    show_logout_option()