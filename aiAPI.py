import os
import json
import requests
import random
import re
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv

# ================= CONFIGURATION =================

load_dotenv()

app = Flask(__name__)

API_PROVIDER = os.getenv("API_PROVIDER", "GEMINI")

# --- OpenAI Config ---
API_BASE_URL = os.getenv("API_BASE_URL", "http://evolab:8080/v1")
API_ENDPOINT = f"{API_BASE_URL}/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Google Gemini Config ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

# --- Global State ---
current_data = {"flashcards": []}
used_indices = []
json_file_path = ""

# ================= LLM SETUP =================

if API_PROVIDER == "GEMINI":
    if not GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set.")
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
    except ImportError:
        print("Error: 'google-generativeai' not installed.")

# ================= HELPER FUNCTIONS =================

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
                print(f"OpenAI Error: {response.status_code}")
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

# ================= API ROUTES =================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """List all .json files in the directory."""
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    return jsonify({"files": files})

@app.route('/api/load', methods=['POST'])
def load_file():
    """Load a specific JSON file into memory."""
    global current_data, used_indices, json_file_path
    data = request.json
    filename = data.get('filename')
    
    if os.path.exists(filename):
        json_file_path = filename
        try:
            with open(filename, 'r') as file:
                current_data = json.load(file)
                if "flashcards" not in current_data:
                    current_data["flashcards"] = []
                used_indices = [] # Reset progress
            return jsonify({"status": "success", "count": len(current_data["flashcards"])})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "File not found"}), 404

@app.route('/api/generate', methods=['GET'])
def generate_card():
    """Pick a card and generate a quiz via LLM."""
    global current_data, used_indices

    flashcards = current_data.get("flashcards", [])
    if not flashcards:
        return jsonify({"error": "No cards loaded"}), 400

    # Logic to cycle through cards
    available_indices = [i for i in range(len(flashcards)) if i not in used_indices]
    
    if not available_indices:
        # Reset if all used
        used_indices = []
        available_indices = list(range(len(flashcards)))

    chosen_index = random.choice(available_indices)
    used_indices.append(chosen_index)
    
    card = flashcards[chosen_index]
    
    q_text = card.get("question", "Unknown")
    a_text = card.get("textbook_answer", "Unknown")
    loc_text = card.get("textbook_location", "Unknown")

    mode = random.choice(["MC", "FITB"])
    quiz_data = None

    if mode == "MC":
        system_prompt = "You are a quiz generator. Output only valid JSON."
        user_prompt = (
            f"Question: {q_text}\nCorrect Answer: {a_text}\n\n"
            "Task: Generate 3 plausible but incorrect answers (distractors).\n"
            "Constraints: Matches format of correct answer.\n"
            "Output JSON format: {\"distractors\": [\"wrong1\", \"wrong2\", \"wrong3\"]}"
        )
        llm_data = get_llm_json_response(system_prompt, user_prompt)
        
        if llm_data and "distractors" in llm_data:
            options = llm_data["distractors"]
            options.append(a_text)
            random.shuffle(options)
            quiz_data = {
                "type": "MC",
                "question": q_text,
                "options": options,
                "correct_answer": a_text,
                "source": loc_text
            }

    elif mode == "FITB":
        system_prompt = "You are a quiz generator. Output only valid JSON."
        user_prompt = (
            f"Question: {q_text}\nFull Answer: {a_text}\n\n"
            "Task: Rewrite 'Full Answer' replacing ONE key concept with '______'.\n"
            "Output JSON format: {\"masked_text\": \"The capital is ______.\", \"missing_word\": \"Paris\"}"
        )
        llm_data = get_llm_json_response(system_prompt, user_prompt)

        if llm_data and "masked_text" in llm_data:
            quiz_data = {
                "type": "FITB",
                "question": q_text,
                "masked_text": llm_data["masked_text"],
                "missing_word": llm_data["missing_word"],
                "full_answer": a_text,
                "source": loc_text
            }

    if not quiz_data:
        # Fallback if LLM fails
        return jsonify({"error": "Failed to generate quiz data."}), 500

    return jsonify(quiz_data)

if __name__ == '__main__':
    print(f"Starting server... Open http://127.0.0.1:5000 in your browser.")
    app.run(debug=True, port=5000)