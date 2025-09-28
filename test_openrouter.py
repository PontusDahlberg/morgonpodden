#!/usr/bin/env python3
"""
Testa olika OpenRouter modeller
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_openrouter():
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Testa olika modeller
    models_to_test = [
        'anthropic/claude-3-haiku',
        'anthropic/claude-3-sonnet',
        'openai/gpt-3.5-turbo',
        'meta-llama/llama-2-70b-chat'
    ]
    
    for model in models_to_test:
        print(f"🧪 Testar {model}...")
        
        data = {
            'model': model,
            'messages': [{'role': 'user', 'content': 'Säg bara "Hej från MMM!" på svenska.'}],
            'max_tokens': 20
        }
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=10
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content']
                print(f"  ✅ Svar: {message.strip()}")
                return model  # Returnera första fungerande modellen
            else:
                print(f"  ❌ Fel: {response.text[:100]}...")
                
        except Exception as e:
            print(f"  ❌ Exception: {e}")
    
    return None

if __name__ == "__main__":
    working_model = test_openrouter()
    if working_model:
        print(f"\n✅ Fungerande modell: {working_model}")
    else:
        print("\n❌ Ingen modell fungerade")