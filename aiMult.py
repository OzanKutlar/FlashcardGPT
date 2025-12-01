import os
import json
import requests
import time
import random
import sys
import re
import curses # Standard on Linux/Mac. Run 'pip install windows-curses' on Windows.
from dotenv import load_dotenv

# ================= CONFIGURATION =================

load_dotenv()

API_PROVIDER = os.getenv("API_PROVIDER", "GEMINI")

# --- OpenAI / Local LLM Config ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://evolab:8080/v1")
API_ENDPOINT = f"{API_BASE_URL}/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Google Gemini Config ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Global variable for the selected file
json_file_path = 'data.json' # Default fallback

# ================= SETUP =================

data = []

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

# ================= FILE SELECTION (CURSES) =================

def pick_json_file(stdscr):
    # Turn off cursor blinking
    curses.curs_set(0)
    
    # Get all json files in current directory
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    
    if not files:
        return None

    current_row = 0
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        
        title = "Select a JSON file to load (UP/DOWN to move, ENTER to select):"
        stdscr.addstr(0, 0, title, curses.A_BOLD)

        for idx, row in enumerate(files):
            x = 0
            y = 2 + idx
            if y >= h - 1: break # Prevent writing off screen
            
            if idx == current_row:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(y, x, f"> {row}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.addstr(y, x, f"  {row}")

        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(files) - 1:
            current_row += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            return files[current_row]

def init_file_selection():
    global json_file_path
    try:
        # Initialize color pairs inside wrapper
        selected_file = curses.wrapper(lambda stdscr: setup_curses_colors(stdscr))
        
        if selected_file:
            json_file_path = selected_file
            print(f"Selected file: {json_file_path}")
        else:
            print("No .json files found. Creating data.json...")
            json_file_path = "data.json"
    except Exception as e:
        print(f"Curses error (if on Windows, run 'pip install windows-curses'): {e}")
        print("Defaulting to data.json")

def setup_curses_colors(stdscr):
    # Check if we can use colors
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE) # Highlight style
    return pick_json_file(stdscr)

def load_data():
    global data
    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print(f'Error reading JSON data from {json_file_path}.')
            data = {"flashcards": []}
    else:
        data = {"flashcards": []}

# ================= LLM CORE FUNCTIONS =================

def clean_json_string(text):
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def get_llm_json_response(system_instruction, user_content):
    response_text = ""
    if API_PROVIDER == "GEMINI":
        try:
            model = genai.GenerativeModel(GEMINI_MODEL)
            full_prompt = f"{system_instruction}\n\n{user_content}"
            response = model.generate_content(full_prompt)
            response_text = response.text
        except Exception as e:
            print(f"Gemini Error: {e}")
            return None
    elif API_PROVIDER == "OPENAI":
        headers = {
            "Content-Type": "application/json", 
            "Authorization": f"Bearer {OPENAI_API_KEY}"
        }
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.7
        }
        try:
            response = requests.post(API_ENDPOINT, headers=headers, json=payload)
            if response.status_code == 200:
                response_text = response.json()['choices'][0]['message']['content']
            else:
                print(f"OpenAI Error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Request failed: {e}")
            return None

    try:
        cleaned_text = clean_json_string(response_text)
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        print("Failed to parse JSON from LLM response.")
        return None

# ================= QUIZ MODES =================

def prepare_multiple_choice(question, correct_answer):
    print("Generating Multiple Choice Options...", end="", flush=True)
    system_prompt = "You are a quiz generator. Output only valid JSON."
    user_prompt = (
        f"Question: {question}\nCorrect Answer: {correct_answer}\n\n"
        "Task: Generate 3 plausible but incorrect answers (distractors).\n"
        "Constraints: 1. FORMATTING: Match Correct Answer format exactly. 2. SIMILARITY: Strictly related context.\n"
        "Output JSON format: {\"distractors\": [\"wrong1\", \"wrong2\", \"wrong3\"]}"
    )
    data = get_llm_json_response(system_prompt, user_prompt)
    print(" Done.")
    
    if not data or "distractors" not in data: return None

    options = data["distractors"]
    options.append(correct_answer)
    random.shuffle(options)
    
    return {
        "type": "MC",
        "question": question,
        "options": options,
        "correct_answer": correct_answer
    }

def prepare_fill_in_blank(question, correct_answer):
    print("Generating Fill-in-the-Blank...", end="", flush=True)
    system_prompt = "You are a quiz generator. Output only valid JSON."
    user_prompt = (
        f"Question: {question}\nFull Answer: {correct_answer}\n\n"
        "Task: Rewrite 'Full Answer' replacing ONE key piece of info with '______'.\n"
        "Output JSON format: {\"masked_text\": \"The capital of France is ______.\", \"missing_word\": \"Paris\"}"
    )
    data = get_llm_json_response(system_prompt, user_prompt)
    print(" Done.")

    if not data or "masked_text" not in data or "missing_word" not in data: return None

    return {
        "type": "FITB",
        "question": question,
        "masked_text": data["masked_text"],
        "missing_word": data["missing_word"]
    }

# ================= MAIN APP LOGIC =================

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

def run_app():
    global data, left_flashcards, used_flashcards
    
    # 1. Select File via Curses
    init_file_selection()
    
    # 2. Load Data
    load_data()
    
    if "flashcards" not in data:
        data["flashcards"] = []
    
    if len(data["flashcards"]) == 0:
        print(f"No flashcards found in {json_file_path}. Let's add the first one.")
        q_text = input("Enter Question: ")
        a_text = input("Enter Textbook Answer: ")
        data["flashcards"] = [{"question": q_text, "textbook_answer": a_text, "textbook_location": "User Entry"}]
        with open(json_file_path, "w") as file:
            json.dump(data, file, indent=4)

    used_flashcards = data.get("flashcards", []).copy()
    left_flashcards = len(used_flashcards)

    while True:
        # Clear screen
        print("\033[H\033[J", end="")
        
        card_obj = select_random_flashcard()
        if card_obj is None:
            print("No flashcards available.")
            break

        # Normalize data structure
        if isinstance(card_obj, str):
            q_text = card_obj
            a_text = "No textbook answer provided."
            loc_text = "Unknown"
        else:
            q_text = card_obj.get("question", "Unknown Question")
            a_text = card_obj.get("textbook_answer", "No textbook answer provided.")
            loc_text = card_obj.get("textbook_location", "Unknown Location")

        print(f"File: {json_file_path} | Cards Left: {left_flashcards}")
        print("Type 'e' to exit, 'a' to add new card, 's' to skip.\n")

        # --- RANDOM MODE SELECTION ---
        mode = random.choice(["MC", "FITB"])
        quiz_data = None

        if mode == "MC":
            quiz_data = prepare_multiple_choice(q_text, a_text)
        elif mode == "FITB":
            quiz_data = prepare_fill_in_blank(q_text, a_text)

        if not quiz_data:
            print("Error generating quiz content. Skipping card.")
            time.sleep(1)
            continue

        # --- USER INTERACTION ---
        
        # DISPLAY SOURCE LOCATION
        print(f"SOURCE: {loc_text}")
        print("-" * (8 + len(loc_text)))
        
        user_response = ""
        is_correct = False

        if quiz_data["type"] == "MC":
            print(f"QUESTION: {quiz_data['question']}\n")
            options = quiz_data["options"]
            
            labels = ['A', 'B', 'C', 'D']
            option_map = {}
            
            for i, opt in enumerate(options):
                print(f"{labels[i]}) {opt}")
                option_map[labels[i].lower()] = opt

            user_input = input("\nSelect Option (A/B/C/D): ").strip().lower()

            if user_input == 'e': exit()
            if user_input == 's': continue

            selected_text = option_map.get(user_input, "")
            if selected_text == quiz_data["correct_answer"]:
                is_correct = True
            else:
                is_correct = False
                print(f"\nYou chose: {selected_text}")

        elif quiz_data["type"] == "FITB":
            print(f"QUESTION: {quiz_data['question']}\n")
            print(f"Fill in the blank:\n> {quiz_data['masked_text']}\n")
            
            user_input = input("Your Answer: ").strip()

            if user_input.lower() == 'e': exit()
            if user_input.lower() == 's': continue

            if user_input.lower() == quiz_data["missing_word"].lower():
                is_correct = True
            else:
                is_correct = False
        
        # --- RESULTS ---
        if is_correct:
            print("\n✅ CORRECT!")
        else:
            print("\n❌ INCORRECT.")
            if quiz_data["type"] == "MC":
                print(f"The correct answer was: {quiz_data['correct_answer']}")
            else:
                print(f"The missing word was: {quiz_data['missing_word']}")
                print(f"Full answer: {a_text}")

        input("\nPress Enter to continue...")

if __name__ == '__main__':
    run_app()