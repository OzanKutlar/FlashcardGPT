# FlashcardGPT

**FlashcardGPT** is a simple and interactive flashcard application that combines the power of **AutoHotkey** and **Python** to help you study more effectively. The app integrates seamlessly with ChatGPT, enabling you to answer flashcard questions and receive real-time evaluations of your responses.

---

## Features

1. **Flashcard Questions and Answering:**
   - The Python script displays flashcard questions.
   - You input your answer directly in the Python console.

2. **ChatGPT Evaluation:**
   - After you submit your answer, the AutoHotkey script automatically switches to your open ChatGPT window.
   - It types out a prompt to ChatGPT that includes your answer and asks for an evaluation.

3. **Hands-Free Prompting:**
   - Once ChatGPT is open, the AutoHotkey script handles switching windows and typing for you.
   - The only requirement is that your ChatGPT window must already be open.

---

## Requirements

- **Python**: The script is written in Python for displaying flashcard questions and accepting answers.
- **AutoHotkey**: Manages window switching and automates typing in ChatGPT.
- **ChatGPT Access**: You must have ChatGPT open and ready to receive prompts.

---

## How It Works

1. **Open ChatGPT in Your Browser:**
   - Open ChatGPT in your preferred browser or application. Make sure it's ready to receive prompts.

2. **Start the Python Script:**
   - Run the Python script to begin the flashcard session.
   - A flashcard question will be displayed.

3. **Answer the Question:**
   - Type your answer in the Python terminal and press Enter.

4. **Automatic Evaluation:**
   - The AutoHotkey script takes over, switches to your ChatGPT window, and types the prompt for you.
   - The prompt sent to ChatGPT includes your answer and a request for evaluation, such as:
     ```
     "Here is a question: <flashcard question>. My answer is: <your answer>. Please evaluate my answer and provide feedback."
     ```

5. **Receive Feedback:**
   - ChatGPT evaluates your answer, provides feedback, and helps you learn from your mistakes.

---

## Setup Instructions

1. **Install Python:**
   - Download and install Python from [python.org](https://www.python.org/).

2. **Install AutoHotkey:**
   - Download and install AutoHotkey from [autohotkey.com](https://www.autohotkey.com/).

3. **Configure AutoHotkey Script:**
   - Edit the AutoHotkey script to specify the hotkey or trigger for switching to your ChatGPT window.
   - Ensure the script points to the correct ChatGPT application or browser tab.

4. **Run the Scripts:**
   - Start the AutoHotkey script and keep it running in the background.
   - Launch the Python script to begin your flashcard session.

---

## Example Workflow

1. **Flashcard Question:**
   - The Python script displays:
     ```
     Question: What is a process in an operating system?
     ```

2. **Your Answer:**
   - You type:
     ```
     A process is something that can be executed by the processor.
     ```

3. **Automated Evaluation:**
   - The AutoHotkey script switches to ChatGPT and types:
     ```
     Q : What is a process in an operating system?
	 A : A process is something that can be executed by the processor.
	 
	 Please evaluate the answer and point out which parts were correct, which parts were incorrect and which parts were misleading. Give feedback on which parts of the answer can be approved.
     ```

4. **Feedback Received:**
   - ChatGPT responds:
     ```
     Evaluation of the Answer:
	Correct Parts:

		"A process is something that can be executed by the processor."
			This is partially correct. A process does represent a program or part of a program in execution and is indeed something the processor executes. However, this definition lacks depth and doesn't capture all the nuances of what a process is in the context of operating systems.

	Incorrect or Misleading Parts:

		Oversimplification:
			The answer oversimplifies the concept of a process. A process is more than "something that can be executed by the processor." It also includes:
				The program code.
				Its associated resources, such as memory, open files, CPU scheduling information, etc.
				Its execution context, which includes registers, the program counter, and stack.

		Ambiguity in "something":
			Using the word "something" is vague and uninformative. It doesn't convey that a process is specifically an instance of a program in execution.

	Feedback for Improvement:

		Expand the Definition: A more comprehensive answer would be:

			"A process is an instance of a program in execution. It consists of the program code, its current activity represented by the program counter, registers, and the process's execution context. It also includes resources allocated to it, such as memory, open files, and I/O devices."

		Clarify Terminology: Replace vague terms like "something" with precise terminology to ensure clarity.

		Mention Key Attributes: Highlight the essential components of a process, such as its state (e.g., running, ready, or waiting), associated resources, and execution context.
     ```

---

## Notes

- **ChatGPT Window**: Ensure your ChatGPT application or browser tab is open before starting the session.
- **Customization**: Modify the Python and AutoHotkey scripts to fit your specific workflow or flashcard topics.
- **Learning Focus**: Use FlashcardGPT as a tool to learn effectively and improve through detailed feedback.

---

**Happy Learning with FlashcardGPT!**

# License

This project is licensed under the MIT License.