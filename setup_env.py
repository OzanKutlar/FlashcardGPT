import os

def create_env_file():
    print("=== Flashcard Tutor Configuration Generator ===\n")

    # 1. Select Provider
    print("Which AI provider do you want to use?")
    print("1. Google Gemini (Free tier available, high speed)")
    print("2. OpenAI / Local LLM (via Oobabooga/LM Studio)")
    
    choice = input("Enter 1 or 2: ").strip()
    provider = "GEMINI" if choice == "1" else "OPENAI"

    env_content = [
        f"API_PROVIDER={provider}"
    ]

    # 2. Configure Specifics
    if provider == "GEMINI":
        print("\n--- Gemini Configuration ---")
        api_key = input("Enter your Gemini API Key: ").strip()
        model = input("Enter Gemini Model (default: gemini-2.0-flash): ").strip() or "gemini-2.0-flash"
        
        env_content.append(f"GEMINI_API_KEY={api_key}")
        env_content.append(f"GEMINI_MODEL={model}")
        
        # Add placeholders for OpenAI to avoid errors if switched later
        env_content.append("API_BASE_URL=http://localhost:8080/v1")
        env_content.append("OPENAI_API_KEY=sk-placeholder")
        env_content.append("OPENAI_MODEL=gpt-3.5-turbo")

    else:
        print("\n--- OpenAI / Local LLM Configuration ---")
        base_url = input("Enter Base URL (default: http://localhost:8080/v1): ").strip() or "http://localhost:8080/v1"
        api_key = input("Enter API Key (enter 'sk-xxx' for local LLMs): ").strip()
        model = input("Enter Model Name (default: gpt-3.5-turbo): ").strip() or "gpt-3.5-turbo"
        
        env_content.append(f"API_BASE_URL={base_url}")
        env_content.append(f"OPENAI_API_KEY={api_key}")
        env_content.append(f"OPENAI_MODEL={model}")
        
        # Add placeholders for Gemini
        env_content.append("GEMINI_API_KEY=AIza-Placeholder")
        env_content.append("GEMINI_MODEL=gemini-2.0-flash")

    # 3. Write file
    try:
        with open(".env", "w") as f:
            f.write("\n".join(env_content))
        print(f"\nSuccess! '.env' file created with provider set to {provider}.")
    except IOError as e:
        print(f"Error writing .env file: {e}")

if __name__ == "__main__":
    create_env_file()