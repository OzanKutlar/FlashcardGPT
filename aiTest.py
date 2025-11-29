import os
import json
import requests
import time
import random
import sys

# ================= CONFIGURATION =================

# Set this to "OPENAI" or "GEMINI"
API_PROVIDER = "GEMINI" 

# --- OpenAI / Local LLM Config ---
API_BASE_URL = "http://evolab:8080/v1"
API_ENDPOINT = f"{API_BASE_URL}/chat/completions"
# Using a standard model name, change if your local server requires a specific one
OPENAI_MODEL = "gpt-3.5-turbo" 
OPENAI_API_KEY = "sk-xxx" # usually ignored by local servers, but required by protocol

# --- Google Gemini Config ---
# Get key from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
GEMINI_MODEL = "gemini-1.5-flash"

# Path to data file
json_file_path = 'data.json'

# =================================================

data = []

# Conditional import for Gemini to prevent errors if not installed
if API_PROVIDER == "GEMINI":
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    except ImportError:
        print("Error: 'google-generativeai' not installed. Run: pip install google-generativeai")
        sys.exit(1)

def check_and_run():
    global data
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
            if "reset" in data and "chat" in data:
                print(f"Reset is [{data['reset'][0]} , {data['reset'][1]}]\nChat is [{data['chat'][0]} , {data['chat'][1]}]\n")
                user_input = input('Do you want to re-position? (yes/No): ').strip().lower()
                if user_input in ('y', 'yes'):
                    print('You chose to re-position')
                else:
                    return
        except json.JSONDecodeError:
            print('Error reading JSON data from data.json.')

def construct_prompt(question, answer):
    # Combined prompt ensures compatibility across different AI providers
    system_instruction = (
        "You are an AI assistant tasked with helping the user correct their errors. "
        "List the parts in the answer that are correct, incorrect, incomplete or misleading in separate areas. "
        "Then provide some improvements as keypoints.\n"
        "Finally, provide a more accurate answer to the question."
    )
    
    user_content = f"Question: {question}\nUser Answer: {answer}"
    return system_instruction, user_content

def send_question_openai(question, answer):
    system_msg, user_msg = construct_prompt(question, answer)
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "stream": True  # Enable streaming
    }
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_API_KEY}"}
    
    print("\nAI Response: ", end="", flush=True)
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, stream=True)
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        data_str = decoded_line[6:] # Remove 'data: ' prefix
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            json_obj = json.loads(data_str)
                            # Handle standard OpenAI delta content
                            content = json_obj['choices'][0]['delta'].get('content', '')
                            if content:
                                print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            continue
            print() # Newline at end
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")

def send_question_gemini(question, answer):
    system_msg, user_msg = construct_prompt(question, answer)
    
    # Gemini usually takes system instructions in the config or as the first part of the prompt
    # Using the library's system_instruction if available, or prepending text
    full_prompt = f"{system_msg}\n\n{user_msg}"
    
    print("\nAI Response: ", end="", flush=True)
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            print(chunk.text, end='', flush=True)
        print() # Newline at end
    except Exception as e:
        print(f"\nGemini Error: {e}")

def send_question(question, answer):
    if API_PROVIDER == "GEMINI":
        send_question_gemini(question, answer)
    else:
        send_question_openai(question, answer)

left_flashcards = -1
used_flashcards = []

def select_random_flashcard():
    global data, left_flashcards, used_flashcards
    if left_flashcards > 0:
        flashcard = random.choice(used_flashcards)
        used_flashcards.remove(flashcard)
        left_flashcards -= 1
        return flashcard
    else:
        if not used_flashcards:
            used_flashcards = data.get("flashcards", []).copy()
            left_flashcards = len(used_flashcards) - 1
            if left_flashcards < 0: return "No flashcards found." # Handle empty list
        
        flashcard = random.choice(used_flashcards)
        used_flashcards.remove(flashcard)
        return flashcard

if __name__ == '__main__':
    check_and_run()
    
    # Ensure data dict has necessary keys
    if "flashcards" not in data:
        data["flashcards"] = []
        
    print("Done loading.")
    
    if len(data["flashcards"]) == 0:
        question = input("Add the first flashcard: ")
        data["flashcards"] = [question]
        with open(json_file_path, "w") as file:
            json.dump(data, file, indent=4)
    
    # Initialize pool
    used_flashcards = data.get("flashcards", []).copy()
    left_flashcards = len(used_flashcards)

    while True:
        # Clear screen command
        print("\033[H\033[J", end="")
        
        random_question = select_random_flashcard()
        
        print(f"{left_flashcards} left.\nYour question is : {random_question}\n\nType 'e' to exit.\nType 'a' to add new flashcard\nType 's' to skip the question.\n")
        answer = input("A : ")
        
        if answer.lower() == 's':
            continue
        if answer.lower() == 'e':
            exit()
        if answer.lower() == 'a':
            new_flashcard = input("Enter your new flashcard question: ")
            data["flashcards"].append(new_flashcard)
            # Add to current pool as well so it can be picked up
            used_flashcards.append(new_flashcard)
            left_flashcards += 1
            
            print(f"New flashcard added: {new_flashcard}")
            with open(json_file_path, "w") as file:
                json.dump(data, file, indent=4)
            time.sleep(1)
            continue
            
        send_question(random_question, answer)
        print("\n")
        input("Press any key to continue.")