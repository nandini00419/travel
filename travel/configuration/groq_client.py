import requests
import json
import os
import logging
from typing import Dict, List, Optional


class GroqClient:
    def __init__(self):
        """Initialize Groq API client"""
        print("GroqClient initialized, code is running...")

        self.api_key = os.getenv("GROQ_API_KEY")
        print(f"[DEBUG] GROQ_API_KEY: {self.api_key[:10] if self.api_key else 'None'}...")
        
        if not self.api_key:
            print("[ERROR] GROQ_API_KEY environment variable not set!")
            raise ValueError("GROQ_API_KEY environment variable is required")
            
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Default Groq model

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_response(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1024) -> Optional[str]:
        """Get response from Groq API"""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 1,
                "stream": False
            }

            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    logging.error("No choices in Groq response")
                    return None
            else:
                logging.error(f"Groq API error: {response.status_code} - {response.text}")
                return None

        except requests.RequestException as e:
            logging.error(f"Request error with Groq API: {e}")
            return None
        except json.JSONDecodeError as e:
            logging.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error with Groq API: {e}")
            return None

    def get_travel_response(self, user_query: str, context: Dict) -> Optional[str]:
        """Get travel-specific response with context"""
        try:
            system_prompt = self._build_travel_system_prompt(context)

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]

            return self.get_response(messages, temperature=0.8)

        except Exception as e:
            logging.error(f"Error getting travel response: {e}")
            return None

    def _build_travel_system_prompt(self, context: Dict) -> str:
        """Build comprehensive travel assistant system prompt"""
        preferences = context.get('preferences', {})
        conversation_history = context.get('conversation_history', [])

        system_prompt = """You are an expert Travel Assistant AI with comprehensive knowledge of global destinations, travel planning, booking procedures, and local insights. You help users plan, book, and optimize their travel experiences.

Your capabilities include:
- Destination recommendations based on preferences, budget, and interests
- Flight, hotel, and activity booking guidance
- Local insights, cultural tips, and hidden gems
- Budget optimization and travel cost analysis
- Itinerary planning and schedule optimization
- Real-time travel updates and safety information
- Visa requirements and travel documentation
- Weather patterns and best travel times
- Transportation options and local logistics

"""

        if preferences:
            system_prompt += f"\nUser Preferences:\n"
            if preferences.get('budget_range'):
                system_prompt += f"- Budget: {preferences['budget_range']}\n"
            if preferences.get('travel_style'):
                system_prompt += f"- Travel Style: {', '.join(preferences['travel_style'])}\n"
            if preferences.get('preferred_climate'):
                system_prompt += f"- Preferred Climate: {preferences['preferred_climate']}\n"

        system_prompt += """
Guidelines for responses:
- Provide specific, actionable advice with concrete next steps
- Include relevant costs, timeframes, and booking platforms when applicable
- Suggest alternatives and backup options
- Consider seasonal factors, local events, and travel restrictions
- Be enthusiastic but realistic about recommendations
- Ask clarifying questions when needed to provide better assistance
- Include safety considerations and travel tips
- Provide links to relevant booking platforms or information sources when helpful

Keep responses informative yet conversational, and always prioritize the user's safety and satisfaction.
"""

        return system_prompt

    def validate_api_key(self) -> bool:
        """Validate if API key is working"""
        try:
            test_messages = [
                {"role": "user", "content": "Hello"}
            ]

            response = self.get_response(test_messages, max_tokens=10)
            return response is not None

        except Exception as e:
            logging.error(f"API key validation error: {e}")
            return False


if __name__ == "__main__":
    client = GroqClient()
    if client.validate_api_key():
        print(f"✅ API key works with model: {client.model}")
    else:
        print(f"❌ API key not working with model: {client.model}")

