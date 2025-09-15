import streamlit as st
import hashlib
import datetime
import json
from database import DatabaseManager
from conversation_manager import ConversationManager
from groq_client import GroqClient
from logger import Logger
from auth import authenticate_user
from travel_prompts import TravelPrompts


# Initialize components
@st.cache_resource
def init_components():
    db_manager = DatabaseManager()
    logger = Logger()
    groq_client = GroqClient()
    travel_prompts = TravelPrompts()
    conversation_manager = ConversationManager(db_manager)
    return db_manager, logger, groq_client, travel_prompts, conversation_manager

                                
def main():
    # Page configuration
    st.set_page_config(
        page_title="Travel Assistant AI",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize components
    db_manager, logger, groq_client, travel_prompts, conversation_manager = init_components()

    # Authentication check
    if not authenticate_user():
        return

    # Main application header
    st.title("Travel Assistant AI")
    st.markdown("Your intelligent travel companion for planning, booking, and exploring")

    # Sidebar for user management and settings
    with st.sidebar:
        st.header(" User Profile")

        if "user_id" not in st.session_state:
            user_email = st.text_input("Enter your email:", placeholder="user@example.com")
            if user_email and st.button("Continue"):
                user_id = hashlib.md5(user_email.encode()).hexdigest()
                st.session_state.user_id = user_id
                st.session_state.user_email = user_email
                user_data = db_manager.get_user_data(user_id)
                st.session_state.user_preferences = user_data.get('preferences', {})
                st.session_state.conversation_history = user_data.get('conversations', [])

                logger.log_user_action(user_id, "login", {"email": user_email})
                st.rerun()
        else:
            st.success(f"Welcome back! {st.session_state.user_email}")
            # your code continues here...

            # User preferences
            st.subheader(" Travel Preferences")
            budget_range = st.selectbox("Budget Range",
                                        ["Budget", "Mid-range", "Luxury", "No preference"])
            travel_style = st.multiselect("Travel Style",
                                          ["Adventure", "Relaxation", "Culture", "Business", "Family", "Solo"])
            preferred_climate = st.selectbox("Preferred Climate",
                                             ["Tropical", "Temperate", "Cold", "Desert", "No preference"])

            # Update preferences
            new_preferences = {
                "budget_range": budget_range,
                "travel_style": travel_style,
                "preferred_climate": preferred_climate,
                "last_updated": datetime.datetime.now().isoformat()
            }
            # then the rest of your sidebar code...

            if new_preferences != st.session_state.get('user_preferences', {}):
                st.session_state.user_preferences = new_preferences
                db_manager.update_user_preferences(st.session_state.user_id, new_preferences)

            # Clear conversation button
            if st.button(" Clear Conversation"):
                st.session_state.messages = []
                st.session_state.conversation_history = []
                db_manager.clear_user_conversations(st.session_state.user_id)
                logger.log_user_action(st.session_state.user_id, "clear_conversation", {})
                st.rerun()

    # Main chat interface
    if "user_id" in st.session_state:
        # Initialize chat messages
        if "messages" not in st.session_state:
            st.session_state.messages = []
            # Add welcome message with travel context
            welcome_msg = travel_prompts.get_welcome_message(st.session_state.user_preferences)
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask me anything about travel..."):
            # Log user input
            logger.log_user_input(st.session_state.user_id, prompt)

            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Prepare context for AI
                        context = travel_prompts.build_context(
                            user_preferences=st.session_state.user_preferences,
                            conversation_history=st.session_state.messages[-5:],  # Last 5 messages
                            user_query=prompt
                        )

                        # Get response from Groq
                        # Debug: Print context sent to Groq API
                        print(f"[DEBUG] Sending context to Groq API: {context}")

                        try:
                            response = groq_client.get_response(context)
                            print(f"[DEBUG] Received response from Groq API: {response}")
                        except Exception as e:
                            print(f"[ERROR] Exception while calling Groq API: {e}")
                            response = None

                        if response:
                            st.markdown(response)

                            # Add assistant response to chat history
                            st.session_state.messages.append({"role": "assistant", "content": response})

                            # Save conversation to database
                            conversation_data = {
                                "timestamp": datetime.datetime.now().isoformat(),
                                "user_message": prompt,
                                "assistant_response": response,
                                "context_used": len(st.session_state.messages) > 2
                            }

                            db_manager.save_conversation(st.session_state.user_id, conversation_data)
                            logger.log_ai_response(st.session_state.user_id, response, len(response))

                        else:
                            error_msg = "I apologize, but I'm having trouble connecting to my AI service right now. Please try again in a moment."
                            st.error(error_msg)
                            print(f"[ERROR] No response or bad response from Groq API for prompt: {prompt}")
                            logger.log_error(st.session_state.user_id, "groq_api_error",
                                             {"user_query": prompt, "context": context})

                    except Exception as e:
                        error_msg = f"I encountered an error while processing your request. Please try again."
                        st.error(error_msg)
                        logger.log_error(st.session_state.user_id, "general_error", {
                            "error": str(e),
                            "user_query": prompt
                        })

        # Travel quick actions
        st.markdown("---")
        st.subheader("Quick Travel Actions")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Plan Vacation"):
                quick_prompt = "I want to plan a vacation. Can you help me with destination suggestions based on my preferences?"
                st.session_state.quick_query = quick_prompt

        with col2:
            if st.button(" Find Flights"):
                quick_prompt = "Help me find flight options. What information do you need from me?"
                st.session_state.quick_query = quick_prompt

        with col3:
            if st.button("Book Hotels"):
                quick_prompt = "I need help finding and booking accommodations. What are my options?"
                st.session_state.quick_query = quick_prompt

        with col4:
            if st.button("Local Guide"):
                quick_prompt = "I'm looking for local recommendations and travel tips for my destination."
                st.session_state.quick_query = quick_prompt

        # Process quick query if set
        if hasattr(st.session_state, 'quick_query'):
            prompt = st.session_state.quick_query
            delattr(st.session_state, 'quick_query')
            st.session_state.messages.append({"role": "user", "content": prompt})

            # Run AI response generation for quick prompt (same as chat section)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        context = travel_prompts.build_context(
                            user_preferences=st.session_state.user_preferences,
                            conversation_history=st.session_state.messages[-5:],
                            user_query=prompt
                        )
                        print(f"[DEBUG] (quick_query) Sending context to Groq API: {context}")
                        response = groq_client.get_response(context)
                        print(f"[DEBUG] (quick_query) Received response from Groq API: {response}")

                        if response:
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})

                            conversation_data = {
                                "timestamp": datetime.datetime.now().isoformat(),
                                "user_message": prompt,
                                "assistant_response": response,
                                "context_used": len(st.session_state.messages) > 2
                            }
                            db_manager.save_conversation(st.session_state.user_id, conversation_data)
                            logger.log_ai_response(st.session_state.user_id, response, len(response))
                        else:
                            error_msg = "I apologize, but I'm having trouble connecting to my AI service right now. Please try again in a moment."
                            st.error(error_msg)
                            print(f"[ERROR] (quick_query) No API response for: {prompt}")
                            logger.log_error(st.session_state.user_id, "groq_api_error",
                                             {"user_query": prompt, "context": context})

                    except Exception as e:
                        error_msg = f"I encountered an error while processing your request. Please try again."
                        st.error(error_msg)
                        print(f"[ERROR] (quick_query) Exception: {e}")
                        logger.log_error(st.session_state.user_id, "general_error", {
                            "error": str(e),
                            "user_query": prompt
                        })

            st.rerun()

    # Footer with stats
    if "user_id" in st.session_state:
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
            st.metric("Messages Sent", msg_count)

        with col2:
            pref_count = len(st.session_state.user_preferences)
            st.metric("Preferences Set", pref_count)

        with col3:
            # Get conversation count from database
            conv_count = db_manager.get_conversation_count(st.session_state.user_id)
            st.metric("Total Conversations", conv_count)
        
        with col4:
            # Admin dashboard link
            if st.button("📊 Admin Dashboard"):
                st.switch_page("pages/admin_dashboard.py")


if __name__ == "__main__":
    main()