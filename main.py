#!/usr/bin/env python3
"""
Claude API Project - Simple chatbot interaction
Uses Anthropic API with configured credentials from .env
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic

# Load environment variables
load_dotenv()

def main():
    # Initialize the Anthropic client
    client = Anthropic(
        api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
        base_url=os.getenv("ANTHROPIC_BASE_URL"),
    )
    
    print("Claude API Chat Bot")
    print("=" * 50)
    print("Type 'exit' to quit")
    print("=" * 50)
    
    conversation_history = []
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        # Add user message to conversation history
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Call the API
            response = client.messages.create(
                model="google/gemma-4-31b-it:free",
                max_tokens=1024,
                messages=conversation_history
            )
            
            # Extract the assistant's response
            assistant_message = response.content[0].text
            
            # Add assistant message to conversation history
            conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            print(f"\nClaude: {assistant_message}")
            
        except Exception as e:
            print(f"\nError: {e}")
            # Remove the last user message if API call failed
            conversation_history.pop()


if __name__ == "__main__":
    main()
