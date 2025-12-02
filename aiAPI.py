import os
import json
import random
import re
import threading
import time
import html  # [SECURITY] Import html for escaping
from flask import Flask, render_template, jsonify, request, session
from dotenv import load_dotenv
import google.generativeai as genai

# ================= CONFIGURATION =================

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "super_secret_dev_key_change_me")

# Thread locks
genai_lock = threading.Lock() 
leaderboard_lock = threading.Lock() 

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
        
        # [SECURITY] Logic moved to route handler, but we process data here
        # Add new entry
        data.append({"name": user_name, "score": score, "date": time.strftime("%Y-%m-%d")})
        
        # Sort by score descending and keep top 10
        data = sorted(data, key=lambda x: x['score'], reverse=True)[:10]
        
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(data, f)
        return data

def generate_quiz_content(api_key, mode, question, answer):
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
    files = [f for f in os.listdir('.') if f.endswith('.json') and f != LEADERBOARD_FILE]
    return jsonify({"files": files})

@app.route('/api/leaderboard', methods=['GET', 'POST'])
def handle_leaderboard():
    if request.method == 'GET':
        return jsonify(get_leaderboard_data())
    
    if request.method == 'POST':
        data = request.json
        
        # [SECURITY] Block XSS: Sanitize the name input
        raw_name = data.get('name', 'Anonymous')
        safe_name = html.escape(str(raw_name))
        
        # [SECURITY] Enforce length limit
        if len(safe_name) > 20:
            safe_name = safe_name[:20]

        # [SECURITY] Validate score is a number
        score = data.get('score', 0)
        if not isinstance(score, (int, float)):
            score = 0
            
        new_data = update_leaderboard_file(safe_name, score)
        return jsonify(new_data)

@app.route('/api/start', methods=['POST'])
def start_session():
    data = request.json
    filename = data.get('filename')
    
    # Basic Path Traversal Check
    if not filename or not os.path.exists(filename) or os.sep in filename:
        return jsonify({"error": "File not found"}), 404

    session['filename'] = filename
    session['used_indices'] = []
    session['score'] = 0
    
    try:
        with open(filename, 'r') as f:
            file_data = json.load(f)
            count = len(file_data.get("flashcards", []))
        return jsonify({"status": "success", "count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_card():
    api_key = request.headers.get('X-Gemini-API-Key')
    if not api_key:
        return jsonify({"error": "Missing API Key"}), 401

    filename = session.get('filename')
    if not filename:
        return jsonify({"error": "Session not started."}), 400

    try:
        with open(filename, 'r') as f:
            file_data = json.load(f)
            flashcards = file_data.get("flashcards", [])
    except Exception:
        return jsonify({"error": "File read error"}), 500

    if not flashcards:
        return jsonify({"error": "No cards in file"}), 400

    used = session.get('used_indices', [])
    available_indices = [i for i in range(len(flashcards)) if i not in used]

    if not available_indices:
        used = []
        available_indices = list(range(len(flashcards)))
        session['used_indices'] = []
    
    chosen_index = random.choice(available_indices)
    
    used.append(chosen_index)
    session['used_indices'] = used
    session.modified = True 

    card = flashcards[chosen_index]
    # Note: We trust the local JSON file content, but if strictly paranoid,
    # we could html.escape(q_text) here too. However, that might break display
    # of math symbols or code snippets if the flashcards contain them.
    q_text = card.get("question", "Unknown")
    a_text = card.get("textbook_answer", "Unknown")
    loc_text = card.get("textbook_location", "Unknown")

    mode = request.json.get('mode', 'MC')
    llm_data = generate_quiz_content(api_key, mode, q_text, a_text)
    
    if not llm_data:
        return jsonify({"error": "Failed to generate quiz data."}), 500

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
    points = request.json.get('points', 0)
    # Ensure points is safe (integer)
    if isinstance(points, (int, float)):
        session['score'] = session.get('score', 0) + int(points)
    return jsonify({"score": session['score']})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
