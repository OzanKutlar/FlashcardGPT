import json
import os
import sys

def get_target_file():
    """Allows user to specify which JSON file to target."""
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    default = 'data.json'
    
    print("Available files:", ", ".join(files) if files else "None")
    filename = input(f"Enter filename to update [default: {default}]: ").strip()
    
    if not filename:
        return default
    
    if not filename.endswith('.json'):
        filename += '.json'
    return filename

def load_existing_data(file_path):
    if not os.path.exists(file_path):
        print(f"'{file_path}' not found. A new file will be created.")
        return {"flashcards": []}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "flashcards" not in data:
                data["flashcards"] = []
            return data
    except json.JSONDecodeError:
        print(f"Error: {file_path} is corrupted. Aborting to prevent data loss.")
        sys.exit(1)

def save_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    print(f"Successfully saved to {file_path}")

def main():
    target_file = get_target_file()
    existing_data = load_existing_data(target_file)
    
    print("==========================================")
    print(f"PASTE YOUR JSON BELOW TO APPEND TO: {target_file}")
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
            # We don't strictly require textbook_location here to allow legacy cards,
            # but the new system prompt generates it.
            existing_data["flashcards"].append(card)
            count += 1
        else:
            print(f"Skipping invalid item: {card}")

    if count > 0:
        save_data(target_file, existing_data)
        print(f"\nSuccess! Added {count} new flashcards to {target_file}.")
    else:
        print("\nNo valid cards were added.")

if __name__ == "__main__":
    main()