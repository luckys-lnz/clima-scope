"""
Test script to verify OpenAI API key is working.

This script tests the API key connection without generating a full report.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded .env file from: {env_path}")
    else:
        print(f"⚠ .env file not found at: {env_path}")
        print("  Trying to load from environment variables...")
except ImportError:
    print("⚠ python-dotenv not installed. Install with: pip install python-dotenv")
    print("  Trying to load from environment variables...")

def test_api_key():
    """Test if OpenAI API key is working."""
    print("\n" + "="*60)
    print("OpenAI API Key Test")
    print("="*60)
    print()
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found!")
        print()
        print("Possible solutions:")
        print("1. Make sure .env file exists in pdf_generator/ directory")
        print("2. Check that .env file contains: OPENAI_API_KEY=sk-...")
        print("3. Or set environment variable: export OPENAI_API_KEY='sk-...'")
        print()
        print("See pdf_generator/docs/API_KEY_SETUP.md for detailed instructions.")
        print("Current .env file location:", Path(__file__).parent / ".env")
        return False
    
    # Mask the API key for display
    masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
    print(f"✓ API Key found: {masked_key}")
    print()
    
    # Test API connection
    print("Testing API connection...")
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Make a simple test call
        print("  Making test API call...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            messages=[
                {"role": "user", "content": "Say 'API key is working!' if you can read this."}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"  Response: {result}")
        print()
        print("="*60)
        print("✅ SUCCESS! API key is working correctly!")
        print("="*60)
        print()
        print("You can now use the AI-powered report generator:")
        print("  python -m pdf_generator.generate_ai_sample")
        return True
        
    except ImportError:
        print("❌ ERROR: openai package not installed")
        print("  Install with: pip install openai>=1.0.0")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR: API call failed")
        print(f"  Error: {error_msg}")
        print()
        
        # Provide helpful error messages
        if "Invalid API key" in error_msg or "401" in error_msg or "invalid_api_key" in error_msg.lower():
            print("  → Your API key appears to be invalid")
            print("  → Check that the key in .env file is correct")
            print("  → Get a new key from: https://platform.openai.com/api-keys")
        elif "insufficient_quota" in error_msg.lower() or "exceeded your current quota" in error_msg.lower():
            print("  → Your OpenAI account has insufficient credits/quota")
            print("  → Add credits at: https://platform.openai.com/account/billing")
            print("  → Or upgrade your plan at: https://platform.openai.com/account/limits")
            print()
            print("  Note: The API key is valid, but you need to add billing credits.")
        elif "Rate limit" in error_msg or "429" in error_msg or "rate_limit_exceeded" in error_msg.lower():
            print("  → Rate limit exceeded. Wait a moment and try again.")
            print("  → Check your usage limits: https://platform.openai.com/account/limits")
        else:
            print("  → Check your internet connection")
            print("  → Verify API key is correct")
            print(f"  → Full error: {error_msg[:200]}")
        
        return False

if __name__ == "__main__":
    success = test_api_key()
    sys.exit(0 if success else 1)
