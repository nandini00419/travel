import random
from datetime import datetime
from typing import Dict, List, Optional


class TravelPrompts:
    def __init__(self):
        """Initialize travel-specific prompts and responses"""
        self.welcome_messages = [
            "Welcome to your personal Travel Assistant! I'm here to help you plan amazing journeys and discover incredible destinations. What adventure shall we plan today?",
            "Hello there, fellow traveler! Ready to explore the world? I can help you with everything from flight bookings to hidden local gems. Where would you like to go?",
            "Greetings! Your Travel Assistant is ready to make your wanderlust dreams come true. Whether you're planning a quick getaway or a grand adventure, I'm here to help!",
            "Welcome aboard! I'm your AI travel companion, ready to help you navigate the world of travel. From budget tips to luxury experiences, let's make your next trip unforgettable!"
        ]

        self.travel_categories = {
            "destinations": [
                "beach destinations", "mountain retreats", "city breaks", "cultural hotspots",
                "adventure locations", "romantic getaways", "family-friendly places", "hidden gems"
            ],
            "activities": [
                "outdoor adventures", "cultural experiences", "food tours", "historical sites",
                "nightlife", "shopping", "wellness retreats", "photography spots"
            ],
            "accommodation": [
                "luxury hotels", "budget hostels", "vacation rentals", "unique stays",
                "resorts", "boutique hotels", "eco-lodges", "glamping"
            ],
            "transportation": [
                "flight booking", "train travel", "car rentals", "public transport",
                "ride sharing", "ferry services", "airport transfers", "travel passes"
            ]
        }

        self.quick_tips = [
            "💡 Tip: Book flights 6-8 weeks in advance for the best domestic deals!",
            "🌍 Did you know? Traveling during shoulder season can save you up to 50% on accommodations!",
            "📱 Pro tip: Download offline maps before you travel to save on roaming charges!",
            "🎒 Pack light: Choose versatile clothing items that can be mixed and matched!",
            "💳 Always notify your bank before traveling internationally to avoid card blocks!"
        ]

    def get_welcome_message(self, user_preferences: Optional[Dict] = None) -> str:
        """Generate personalized welcome message"""
        base_message = random.choice(self.welcome_messages)

        if user_preferences and any(user_preferences.values()):
            preferences_text = self._format_preferences(user_preferences)
            base_message += f"\n\n🎯 I notice you prefer {preferences_text}. I'll keep that in mind for our conversation!"

        # Add a random tip
        tip = random.choice(self.quick_tips)
        base_message += f"\n\n{tip}"

        return base_message

    def _format_preferences(self, preferences: Dict) -> str:
        """Format user preferences into readable text"""
        pref_parts = []

        if preferences.get('budget_range'):
            pref_parts.append(f"{preferences['budget_range'].lower()} travel")

        if preferences.get('travel_style'):
            styles = preferences['travel_style']
            if len(styles) > 0:
                pref_parts.append(f"{' and '.join(styles).lower()} experiences")

        if preferences.get('preferred_climate'):
            climate = preferences['preferred_climate']
            if climate != "No preference":
                pref_parts.append(f"{climate.lower()} destinations")

        if pref_parts:
            return ", ".join(pref_parts)
        else:
            return "personalized travel experiences"

    def build_context(self, user_preferences: Optional[Dict] = None,
                      conversation_history: Optional[List[Dict]] = None,
                      user_query: str = "") -> List[Dict]:
        """Build context for AI conversation"""

        # System prompt
        system_prompt = self._get_system_prompt(user_preferences)

        messages = [{"role": "system", "content": system_prompt}]

        # Add relevant conversation history (last few messages for context)
        if conversation_history:
            # Get last 4 messages for context (2 user + 2 assistant)
            recent_history = conversation_history[-4:] if len(conversation_history) > 4 else conversation_history
            for msg in recent_history:
                if msg.get('role') in ['user', 'assistant']:
                    messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

        # Add current user query
        messages.append({"role": "user", "content": user_query})

        return messages

    def _get_system_prompt(self, user_preferences: Optional[Dict] = None) -> str:
        """Generate comprehensive system prompt for travel assistant"""

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_season = self._get_current_season()

        system_prompt = f"""You are an expert Travel Assistant AI with comprehensive knowledge of global destinations, travel planning, and booking procedures. Today's date is {current_date} and we're in {current_season} season.

Your core expertise includes:
🌍 DESTINATIONS: Worldwide knowledge of cities, countries, attractions, and hidden gems
✈️ TRANSPORTATION: Flights, trains, buses, car rentals, and local transport options
🏨 ACCOMMODATION: Hotels, hostels, vacation rentals, and unique stays
🎯 PLANNING: Itineraries, budgeting, timing, and travel optimization
📋 LOGISTICS: Visas, documentation, insurance, health requirements, and safety
🍴 LOCAL INSIGHTS: Culture, cuisine, customs, language tips, and etiquette
💰 BUDGETING: Cost analysis, money-saving tips, and expense planning
🌦️ SEASONAL ADVICE: Weather patterns, best times to visit, and seasonal events

"""

        if user_preferences:
            system_prompt += "USER PREFERENCES:\n"

            if user_preferences.get('budget_range'):
                budget_guidance = self._get_budget_guidance(user_preferences['budget_range'])
                system_prompt += f"• Budget Level: {user_preferences['budget_range']} - {budget_guidance}\n"

            if user_preferences.get('travel_style'):
                styles = user_preferences['travel_style']
                style_guidance = self._get_style_guidance(styles)
                system_prompt += f"• Travel Style: {', '.join(styles)} - {style_guidance}\n"

            if user_preferences.get('preferred_climate'):
                climate = user_preferences['preferred_climate']
                if climate != "No preference":
                    climate_suggestions = self._get_climate_suggestions(climate)
                    system_prompt += f"• Climate Preference: {climate} - {climate_suggestions}\n"

            system_prompt += "\n"

        system_prompt += """RESPONSE GUIDELINES:
• Provide specific, actionable advice with concrete next steps
• Include relevant costs, timeframes, and booking platforms when helpful
• Suggest 2-3 alternatives for major recommendations
• Consider seasonal factors, local events, and current travel conditions
• Always include safety considerations and practical tips
• Be enthusiastic but realistic about recommendations
• Ask clarifying questions when you need more information
• Format responses with clear sections and bullet points for readability
• Include relevant website links or booking platforms when applicable

CONVERSATION STYLE:
• Professional yet friendly and enthusiastic
• Use travel emojis appropriately (✈️🏨🌍🎒)
• Provide detailed explanations while staying concise
• Show cultural awareness and sensitivity
• Encourage exploration while prioritizing safety

Remember: You're not just providing information, you're helping create memorable travel experiences!"""

        return system_prompt

    def _get_current_season(self) -> str:
        """Get current season based on date"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"

    def _get_budget_guidance(self, budget_range: str) -> str:
        """Get guidance based on budget range"""
        guidance = {
            "Budget": "Focus on hostels, public transport, local eateries, and free attractions",
            "Mid-range": "Balance of comfort and value with 3-star hotels, mix of dining options",
            "Luxury": "Premium accommodations, fine dining, private transfers, and exclusive experiences",
            "No preference": "I'll provide options across all budget ranges"
        }
        return guidance.get(budget_range, "I'll tailor suggestions to your needs")

    def _get_style_guidance(self, styles: List[str]) -> str:
        """Get guidance based on travel styles"""
        style_tips = {
            "Adventure": "outdoor activities, hiking, extreme sports, and off-the-beaten-path destinations",
            "Relaxation": "spas, beaches, quiet retreats, and slow travel experiences",
            "Culture": "museums, historical sites, local traditions, and cultural immersion",
            "Business": "efficiency, connectivity, meeting facilities, and professional amenities",
            "Family": "kid-friendly activities, safety, educational experiences, and convenience",
            "Solo": "safety considerations, social opportunities, and personal growth experiences"
        }

        relevant_tips = [style_tips.get(style, style.lower()) for style in styles]
        return "prioritize " + ", ".join(relevant_tips)

    def _get_climate_suggestions(self, climate: str) -> str:
        """Get suggestions based on climate preference"""
        suggestions = {
            "Tropical": "warm beaches, rainforests, and consistent temperatures year-round",
            "Temperate": "moderate seasons, comfortable walking weather, and varied landscapes",
            "Cold": "winter sports, northern lights, cozy accommodations, and cold-weather activities",
            "Desert": "dry climates, unique landscapes, and considerations for extreme temperatures"
        }
        return f"seek destinations with {suggestions.get(climate, climate.lower())} characteristics"

    def get_conversation_starters(self, user_preferences: Optional[Dict] = None) -> List[str]:
        """Generate conversation starter suggestions"""
        starters = [
            "Help me plan a weekend getaway",
            "I need to find the best flights for my budget",
            "What are the must-see attractions in [destination]?",
            "Plan a 7-day itinerary for my vacation",
            "Find me unique accommodations in [city]",
            "What's the best time to visit [destination]?",
            "Help me create a travel budget",
            "I need travel tips for solo travelers"
        ]

        if user_preferences:
            # Add personalized starters based on preferences
            if user_preferences.get('travel_style'):
                if 'Adventure' in user_preferences['travel_style']:
                    starters.append("Find me the best adventure destinations")
                if 'Culture' in user_preferences['travel_style']:
                    starters.append("Recommend cultural experiences and festivals")

            if user_preferences.get('budget_range') == 'Budget':
                starters.append("Show me how to travel on a tight budget")

        return random.sample(starters, min(6, len(starters)))

    def get_travel_checklist_template(self) -> str:
        """Get a travel checklist template"""
        return """
📋 **TRAVEL CHECKLIST**

**📄 Documents & Essentials:**
□ Valid passport (check expiration date)
□ Visa (if required)
□ Travel insurance policy
□ Flight/train/bus tickets
□ Hotel confirmations
□ Driver's license (if renting a car)
□ Travel itinerary copies

**💰 Financial:**
□ Notify bank of travel plans
□ Multiple payment methods (cards + cash)
□ Emergency cash in local currency
□ Receipt storage system

**🎒 Packing:**
□ Weather-appropriate clothing
□ Comfortable walking shoes
□ Medications & first aid kit
□ Phone charger & adapters
□ Travel-sized toiletries
□ Entertainment for travel time

**📱 Digital Prep:**
□ Download offline maps
□ Travel apps installation
□ Emergency contacts list
□ Important documents backup (cloud storage)
□ International data plan or local SIM info

**🏠 Pre-Departure:**
□ House security arrangements
□ Mail/package hold
□ Pet care arrangements
□ Work handover completed
□ Emergency contact information shared

Customize this checklist based on your specific destination and travel style!
"""