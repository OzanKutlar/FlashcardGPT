import os
import json
import requests
import time
import random
import sys
from dotenv import load_dotenv

# ================= CONFIGURATION =================

# Load environment variables from .env file
load_dotenv()

# Fetch variables with defaults or raise errors if missing
API_PROVIDER = os.getenv("API_PROVIDER", "GEMINI")

# --- OpenAI / Local LLM Config ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://evolab:8080/v1")
API_ENDPOINT = f"{API_BASE_URL}/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Google Gemini Config ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Path to data file
json_file_path = 'data.json'

# =================================================

data = []

# Validate Configuration
if API_PROVIDER == "GEMINI":
    if not GEMINI_API_KEY or "Placeholder" in GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY not set in .env file.")
        sys.exit(1)
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    except ImportError:
        print("Error: 'google-generativeai' not installed. Run: pip install google-generativeai")
        sys.exit(1)
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        sys.exit(1)

elif API_PROVIDER == "OPENAI":
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set in .env file.")
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

def construct_prompt(question, user_answer, textbook_answer):
    system_instruction = (
        "You are a concise tutor. Compare the User Answer against the provided Textbook Answer. "
        "1. State if the user is Correct or Incorrect. "
        "2. If incorrect, briefly explain why using the Textbook Answer as the source of truth. "
        "3. Keep your response short and to the point."
    )
    
    user_content = (
        f"Question: {question}\n"
        f"Textbook Answer: {textbook_answer}\n"
        f"User Answer: {user_answer}"
    )
    return system_instruction, user_content

def send_question_openai(question, user_answer, textbook_answer):
    system_msg, user_msg = construct_prompt(question, user_answer, textbook_answer)
    
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        "stream": True 
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
                        data_str = decoded_line[6:] 
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            json_obj = json.loads(data_str)
                            content = json_obj['choices'][0]['delta'].get('content', '')
                            if content:
                                print(content, end='', flush=True)
                        except json.JSONDecodeError:
                            continue
            print() 
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except requests.RequestException as e:
        print(f"Request failed: {e}")

def send_question_gemini(question, user_answer, textbook_answer):
    system_msg, user_msg = construct_prompt(question, user_answer, textbook_answer)
    
    # Gemini usually takes system instruction in model init, but appending works for simple cases
    full_prompt = f"{system_msg}\n\n{user_msg}"
    
    print("\nAI Response: ", end="", flush=True)
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            print(chunk.text, end='', flush=True)
        print() 
    except Exception as e:
        print(f"\nGemini Error: {e}")

def send_question(question, user_answer, textbook_answer):
    if API_PROVIDER == "GEMINI":
        send_question_gemini(question, user_answer, textbook_answer)
    else:
        send_question_openai(question, user_answer, textbook_answer)

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
            if left_flashcards < 0: return None
        
        flashcard = random.choice(used_flashcards)
        used_flashcards.remove(flashcard)
        return flashcard

if __name__ == '__main__':
    check_and_run()
    
    if "flashcards" not in data:
        data["flashcards"] = []
        
    print("Done loading.")
    
    if len(data["flashcards"]) == 0:
        print("No flashcards found. Let's add the first one.")
        q_text = input("Enter Question: ")
        a_text = input("Enter Textbook Answer: ")
        data["flashcards"] = [{"question": q_text, "textbook_answer": a_text}]
        with open(json_file_path, "w") as file:
            json.dump(data, file, indent=4)
    
    # Initialize pool
    used_flashcards = data.get("flashcards", []).copy()
    left_flashcards = len(used_flashcards)

    while True:
        # Clear screen command (Cross-platform friendly)
        print("\033[H\033[J", end="")
        
        card_obj = select_random_flashcard()
        
        if card_obj is None:
            print("No flashcards available.")
            break

        # Handle Legacy Data (if file has strings instead of dicts)
        if isinstance(card_obj, str):
            question_text = card_obj
            textbook_answer = "No textbook answer provided."
        else:
            question_text = card_obj.get("question", "Unknown Question")
            textbook_answer = card_obj.get("textbook_answer", "No textbook answer provided.")
        
        print(f"{left_flashcards} left.\nYour question is : {question_text}\n\nType 'e' to exit.\nType 'a' to add new flashcard\nType 's' to skip the question.\n")
        user_input = input("A : ")
        
        if user_input.lower() == 's':
            continue
        if user_input.lower() == 'e':
            exit()
        if user_input.lower() == 'a':
            new_q = input("Enter your new question: ")
            new_a = input("Enter the textbook answer: ")
            
            new_card = {"question": new_q, "textbook_answer": new_a}
            
            data["flashcards"].append(new_card)
            used_flashcards.append(new_card)
            left_flashcards += 1
            
            print(f"New flashcard added.")
            with open(json_file_path, "w") as file:
                json.dump(data, file, indent=4)
            time.sleep(1)
            continue
            
        send_question(question_text, user_input, textbook_answer)
        print("\n")
        input("Press any key to continue.")