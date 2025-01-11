import os
import json
import subprocess
import sys
import time

# Define the path to the 'data.json' and 'recordMouse.ahk' files
json_file_path = 'data.json'
recordPos = 'recordMouse.ahk'
sendToGPT = 'switchGPT.ahk'
data = []

def check_and_run():
    global data
    # Check if the 'data.json' file exists
    if os.path.exists(json_file_path):
        try:
            # Open and read the 'data.json' file
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # Check if both "reset" and "chat" arrays exist
            if "reset" in data and "chat" in data:
                print(f"Reset is [{data['reset'][0]} , {data['reset'][1]}]\nChat is [{data['chat'][0]} , {data['chat'][1]}]\n")
                user_input = input('Do you want to re-position? (yes/No): ').strip().lower()

                if user_input in ('y', 'yes'):
                    print('You chose to re-position')
                else:
                    return


        except json.JSONDecodeError:
            print('Error reading JSON data from data.json.')

    # If the file doesn't exist or the arrays don't exist, run the AHK script
    print(f'Running {recordPos}...')
    subprocess.run(['start', '/wait', recordPos], shell=True)

    print('AHK script finished. Restarting the Python script...')
    
    time.sleep(1)
    check_and_run()
    
def sendQuestion(question, answer):
    global data
    subprocess.run(['start', '/wait', sendToGPT, data['chat'][0], data['chat'][1], data['reset'][0], data['reset'][1], question, answer], shell=True)
    
def selectRandomFlashCard():
    global data
    if "flashcards" in data and len(data["flashcards"]) > 0:
        return random.choice(data["flashcards"])  # Randomly select a flashcard from the list
    else:
        print("No flashcards available!")
        return None

if __name__ == '__main__':
    check_and_run()
    print("Done")
    if not ("flashcards" in data) or len(data["flashcards"]) == 0:
        question = input("Add the first flashcard: ")
        data["flashcards"] = [question]
    
    
    while True:
        randomQuestion = selectRandomFlashCard()
        print(f"Your question is : {randomQuestion}\n\nType 'e' to exit.\nType 'a' to add new flashcard\n"
        answer = input("A : ")
        if answer == 'e':
            exit()
        if answer == 'a':
            new_flashcard = input("Enter your new flashcard question: ")
            data["flashcards"].append(new_flashcard)
            print(f"New flashcard added: {new_flashcard}")
            continue
        sendQuestion(randomQuestion, answer)
    sendQuestion("Describe the OSI model and its layers.", "The OSI Model has 7 layers, Physical, Data Link, Network, Transport, Session, Presentation, Application")
    exit()
    
    
