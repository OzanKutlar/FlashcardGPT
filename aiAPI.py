import os
import json
import random
import re
from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
import google.generativeai as genai

# ================= CONFIGURATION =================

load_dotenv()

app = Flask(__name__)

# Global State for File Handling
current_data = {"flashcards": []}
used_indices = []
json_file_path = ""

# ================= HELPER FUNCTIONS =================

def clean_json_string(text):
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def generate_quiz_content(api_key, mode, question, answer):
    """
    Configures GenAI with the user's key and generates content.
    Note: In a high-concurrency production app, using the REST API 
    directly is safer than re-configuring the global singleton.
    For this local app, this method is sufficient.
    """
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash") # Or "gemini-1.5-flash"
        
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
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    return jsonify({"files": files})

@app.route('/api/load', methods=['POST'])
def load_file():
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
                used_indices = []
            return jsonify({"status": "success", "count": len(current_data["flashcards"])})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "error", "message": "File not found"}), 404

@app.route('/api/generate', methods=['POST'])
def generate_card():
    global current_data, used_indices

    # 1. Get API Key from Header
    api_key = request.headers.get('X-Gemini-API-Key')
    if not api_key:
        return jsonify({"error": "Missing API Key"}), 401

    # 2. Get Mode from Body
    req_data = request.json
    mode = req_data.get('mode', 'MC') # Default to MC if not sent

    flashcards = current_data.get("flashcards", [])
    if not flashcards:
        return jsonify({"error": "No cards loaded"}), 400

    # 3. Pick Card
    available_indices = [i for i in range(len(flashcards)) if i not in used_indices]
    if not available_indices:
        used_indices = []
        available_indices = list(range(len(flashcards)))

    chosen_index = random.choice(available_indices)
    used_indices.append(chosen_index)
    card = flashcards[chosen_index]
    
    q_text = card.get("question", "Unknown")
    a_text = card.get("textbook_answer", "Unknown")
    loc_text = card.get("textbook_location", "Unknown")

    # 4. Call LLM
    llm_data = generate_quiz_content(api_key, mode, q_text, a_text)
    
    if not llm_data:
        return jsonify({"error": "Failed to generate quiz data."}), 500

    # 5. Format Response
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
            "source": loc_text
        }
    elif mode == "FITB" and "masked_text" in llm_data:
        quiz_data = {
            "type": "FITB",
            "question": q_text,
            "masked_text": llm_data["masked_text"],
            "missing_word": llm_data["missing_word"],
            "full_answer": a_text,
            "source": loc_text
        }
    else:
        return jsonify({"error": "Invalid LLM response format"}), 500

    return jsonify(quiz_data)

if __name__ == '__main__':
    print(f"Starting server... Open http://127.0.0.1:5000")
    app.run(debug=True, port=5000)