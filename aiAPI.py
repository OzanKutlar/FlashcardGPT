import os
import json
import random
import re
import threading
import time
from flask import Flask, render_template, jsonify, request, session
from dotenv import load_dotenv
import google.generativeai as genai

# ================= CONFIGURATION =================

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_dev_key_change_me")

# Thread locks
genai_lock = threading.Lock() # Prevents API key race conditions
leaderboard_lock = threading.Lock() # Prevents file write race conditions

LEADERBOARD_FILE = "leaderboard.json"

# ================= HELPER FUNCTIONS =================

def clean_json_string(text):
    """Extracts JSON from Markdown code blocks if present."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def get_leaderboard_data():
    """Reads leaderboard safely."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def update_leaderboard_file(user_name, score):
    """Updates leaderboard safely using a lock."""
    with leaderboard_lock:
        data = get_leaderboard_data()
        
        # Simple logic: Check if user exists, update if score is higher, or append
        # For this arcade style, we will just add the run or update max score.
        # Let's keep it simple: List of Top Scores.
        
        # Add new entry
        data.append({"name": user_name, "score": score, "date": time.strftime("%Y-%m-%d")})
        
        # Sort by score descending and keep top 10
        data = sorted(data, key=lambda x: x['score'], reverse=True)[:10]
        
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data, f)
        return data

def generate_quiz_content(api_key, mode, question, answer):
    """
    Thread-safe GenAI call. 
    We lock this block so User A's key config doesn't bleed into User B's request.
    """
    with genai_lock:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash") # or gemini-2.0-flash
            
            system_prompt = "You are a quiz generator. Output only valid JSON."
            
            if mode == "MC":
                user_prompt = (
                    f"Question: {question}\nCorrect Answer: {answer}\n\n"
                    "Task: Generate 3 plausible but incorrect answers (distractors).\n"
                    "Constraints: Matches format/length of correct answer.\n"
                    "Output JSON format: {\"distractors\": [\"wrong1\", \"wrong2\", \"wrong3\"]}"
                )
            elif mode == "FITB":
                user_prompt = (
                    f"Question: {question}\nFull Answer: {answer}\n\n"
                    "Task: Rewrite 'Full Answer' replacing ONE key concept with '______'.\n"
                    "Output JSON format: {\"masked_text\": \"The capital is ______.\", \"missing_word\": \"Paris\"}"
                )
            else:
                return None

            response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
            cleaned_text = clean_json_string(response.text)
            return json.loads(cleaned_text)

        except Exception as e:
            print(f"GenAI Error: {e}")
            return None

# ================= API ROUTES =================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    # Only list JSON files, ignore leaderboard config
    files = [f for f in os.listdir('.') if f.endswith('.json') and f != LEADERBOARD_FILE]
    return jsonify({"files": files})

@app.route('/api/leaderboard', methods=['GET', 'POST'])
def handle_leaderboard():
    if request.method == 'GET':
        return jsonify(get_leaderboard_data())
    
    if request.method == 'POST':
        data = request.json
        name = data.get('name', 'Anonymous')
        score = data.get('score', 0)
        new_data = update_leaderboard_file(name, score)
        return jsonify(new_data)

@app.route('/api/start', methods=['POST'])
def start_session():
    """Initializes a user session with a specific file."""
    data = request.json
    filename = data.get('filename')
    
    if not os.path.exists(filename):
        return jsonify({"error": "File not found"}), 404

    # Reset Session Data for this specific user
    session['filename'] = filename
    session['used_indices'] = []
    session['score'] = 0
    
    # Get card count just for UI info
    try:
        with open(filename, 'r') as f:
            file_data = json.load(f)
            count = len(file_data.get("flashcards", []))
        return jsonify({"status": "success", "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_card():
    # 1. Get API Key from Header
    api_key = request.headers.get('X-Gemini-API-Key')
    if not api_key:
        return jsonify({"error": "Missing API Key"}), 401

    # 2. Check Session
    filename = session.get('filename')
    if not filename:
        return jsonify({"error": "Session not started. Select a file."}), 400

    # 3. Load File (Stateless read)
    try:
        with open(filename, 'r') as f:
            file_data = json.load(f)
            flashcards = file_data.get("flashcards", [])
    except Exception as e:
        return jsonify({"error": "File read error"}), 500

    if not flashcards:
        return jsonify({"error": "No cards in file"}), 400

    # 4. Pick Card Logic (using session indices)
    used = session.get('used_indices', [])
    available_indices = [i for i in range(len(flashcards)) if i not in used]

    # Reset if all used
    if not available_indices:
        used = []
        available_indices = list(range(len(flashcards)))
        session['used_indices'] = [] # Reset in session
    
    chosen_index = random.choice(available_indices)
    
    # Update Session
    used.append(chosen_index)
    session['used_indices'] = used
    session.modified = True # Ensure Flask saves the cookie update

    card = flashcards[chosen_index]
    q_text = card.get("question", "Unknown")
    a_text = card.get("textbook_answer", "Unknown")
    loc_text = card.get("textbook_location", "Unknown")

    # 5. Call LLM
    mode = request.json.get('mode', 'MC')
    llm_data = generate_quiz_content(api_key, mode, q_text, a_text)
    
    if not llm_data:
        return jsonify({"error": "Failed to generate quiz data."}), 500

    # 6. Format Response
    quiz_data = {}
    if mode == "MC" and "distractors" in llm_data:
        options = llm_data["distractors"]
        options.append(a_text)
        random.shuffle(options)
        quiz_data = {
            "type": "MC",
            "question": q_text,
            "options": options,
            "correct_answer": a_text,
            "source": loc_text,
            "current_score": session.get('score', 0)
        }
    elif mode == "FITB" and "masked_text" in llm_data:
        quiz_data = {
            "type": "FITB",
            "question": q_text,
            "masked_text": llm_data["masked_text"],
            "missing_word": llm_data["missing_word"],
            "full_answer": a_text,
            "source": loc_text,
            "current_score": session.get('score', 0)
        }
    else:
        return jsonify({"error": "Invalid LLM response format"}), 500

    return jsonify(quiz_data)

@app.route('/api/score', methods=['POST'])
def update_score():
    """Updates the user's session score."""
    points = request.json.get('points', 0)
    session['score'] = session.get('score', 0) + points
    return jsonify({"score": session['score']})

if __name__ == '__main__':
    print("Starting server...")
    app.run(debug=True, port=5000)