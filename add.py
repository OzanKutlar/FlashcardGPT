import json
import os
import sys

FILE_PATH = 'data.json'

def load_existing_data():
    if not os.path.exists(FILE_PATH):
        print(f"'{FILE_PATH}' not found. Creating new database.")
        return {"flashcards": []}
    
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "flashcards" not in data:
                data["flashcards"] = []
            return data
    except json.JSONDecodeError:
        print("Error: Existing data.json is corrupted. Aborting to prevent data loss.")
        sys.exit(1)

def save_data(data):
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print("Successfully saved to data.json")

def main():
    existing_data = load_existing_data()
    
    print("==========================================")
    print("PASTE YOUR JSON BELOW.")
    print("You can paste a List [...] or a Dict {\"flashcards\": [...]}")
    print("Type 'DONE' on a new line and press Enter when finished.")
    print("==========================================\n")

    # Capture multi-line input
    lines = []
    while True:
        try:
            line = input()
            # Stop if user types DONE
            if line.strip() == 'DONE':
                break
            lines.append(line)
        except EOFError:
            break

    raw_input = "\n".join(lines)
    
    if not raw_input.strip():
        print("No input detected. Exiting.")
        return

    try:
        new_json = json.loads(raw_input)
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON input: {e}")
        print("Make sure you pasted valid JSON format.")
        return

    # Normalize input to a list of cards
    cards_to_add = []
    
    if isinstance(new_json, list):
        cards_to_add = new_json
    elif isinstance(new_json, dict):
        if "flashcards" in new_json and isinstance(new_json["flashcards"], list):
            cards_to_add = new_json["flashcards"]
        else:
            # Maybe the user pasted a single card object?
            if "question" in new_json:
                cards_to_add = [new_json]
    
    if not cards_to_add:
        print("No valid flashcards found in the pasted JSON.")
        return

    # Append valid cards
    count = 0
    for card in cards_to_add:
        if isinstance(card, dict) and "question" in card and "textbook_answer" in card:
            existing_data["flashcards"].append(card)
            count += 1
        else:
            print(f"Skipping invalid item: {card}")

    if count > 0:
        save_data(existing_data)
        print(f"\nSuccess! Added {count} new flashcards.")
    else:
        print("\nNo valid cards were added.")

if __name__ == "__main__":
    main()