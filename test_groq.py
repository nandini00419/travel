#!/usr/bin/env python3
"""
Test script to verify Groq API connection
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config.env')

def test_groq_connection():
    """Test Groq API connection"""
    print("🔍 Testing Groq API Connection...")
    print("=" * 50)
    
    # Check if API key is set
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key or api_key == "your-groq-api-key-here":
        print("❌ GROQ_API_KEY not found or not set!")
        print("Please set your Groq API key in config.env")
        print("Get your API key from: https://console.groq.com/keys")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test the Groq client
    try:
        sys.path.append('travel/configuration')
        from groq_client import GroqClient
        
        client = GroqClient()
        print(f"✅ GroqClient initialized with model: {client.model}")
        
        # Test a simple request
        test_messages = [
            {"role": "user", "content": "Hello! Can you respond with just 'Hi there!'?"}
        ]
        
        print("🔄 Testing API request...")
        response = client.get_response(test_messages, max_tokens=50)
        
        if response:
            print(f"✅ API Response: {response}")
            print("🎉 Groq API is working correctly!")
            return True
        else:
            print("❌ No response received from Groq API")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Groq API: {e}")
        return False

if __name__ == "__main__":
    success = test_groq_connection()
    if not success:
        print("\n🔧 Troubleshooting steps:")
        print("1. Make sure you have a valid Groq API key")
        print("2. Check your internet connection")
        print("3. Verify the API key is correctly set in config.env")
        print("4. Make sure all required packages are installed: pip install -r requirements.txt")
        sys.exit(1)
    else:
        print("\n✅ All tests passed! Your Groq API is ready to use.")
