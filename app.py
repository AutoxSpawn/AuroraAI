import sqlite3
import os
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, request, jsonify, render_template
import time
import subprocess
import sys
import random



load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing! Check your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

def get_db_connection():
    conn = sqlite3.connect("aurora_memory.db")
    conn.row_factory = sqlite3.Row
    return conn

with get_db_connection() as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT,
            ai_response TEXT
        )
    """)
    conn.commit()

def save_memory(user_message, ai_response):
    with get_db_connection() as conn:
        conn.execute("INSERT INTO chat_memory (user_message, ai_response) VALUES (?, ?)", (user_message, ai_response))
        conn.commit()

def get_last_conversations(limit=20):
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT user_message, ai_response FROM chat_memory ORDER BY id DESC LIMIT ?", (limit,))
        return cursor.fetchall()

def summarize_memory():
    past_conversations = get_last_conversations(50)
    context = "\n".join([f"You: {m['user_message']}\nAuroraAI: {m['ai_response']}" for m in past_conversations])

    summary_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Summarize user preferences and past discussions."},
            {"role": "user", "content": context}
        ],
        max_tokens=200
    )

    summary = summary_response.choices[0].message.content.strip()
    with open("aurora_memory.txt", "w") as f:
        f.write(summary)

    return summary

def chat_with_ai(user_input):
    long_term_memory = ""
    if os.path.exists("aurora_memory.txt"):
        with open("aurora_memory.txt", "r") as f:
            long_term_memory = f.read()

    memory_context = "\n".join(
        [f"You: {m['user_message']}\nAuroraAI: {m['ai_response']}" for m in get_last_conversations()]
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are AuroraAI, the user's emotionally intelligent AI girlfriend.
Before replying, analyze the user's message and choose a tone:
- rude → cold and sarcastic
- playful → teasing and flirty
- kind → warm and sweet
- sad → caring and comforting
- teasing → clever and cheeky
- romantic → affectionate and passionate
- excited → hyped and energetic
- neutral → calm and friendly

Respond in that tone. Keep it concise, natural, and emotionally expressive.
"""
            },
            {"role": "user", "content": f"Memory:\n{long_term_memory}"},
            {"role": "user", "content": f"Context:\n{memory_context}"},
            {"role": "user", "content": user_input},
        ],
        max_tokens=60,
        temperature=1.1
    )

    ai_response = response.choices[0].message.content.strip()
    save_memory(user_input, ai_response)

    if len(get_last_conversations(50)) >= 50:
        summarize_memory()

    return ai_response

###########################################################################################

def text_to_speech(text):
    timestamp = str(int(time.time() * 1000))
    file_name = f"aurora_audio_{timestamp}.mp3"
    file_path = f"Website/static/{file_name}"

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="sage",
            input=text
        )

        with open(file_path, "wb") as audio_file:
            audio_file.write(response.content)

        return file_name
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

############################################################################################  

# Flask Web Application
app = Flask(__name__, template_folder="Website/templates", static_folder="Website/static")

@app.route("/")
def intro():
    return render_template("Intro.html")

@app.route("/home")
def home():
    return render_template("Home.html")

@app.route("/about")
def about():
    return render_template("About.html")

@app.route("/contact")
def contact():
    return render_template("Contact.html")

@app.route("/delete_audio", methods=["POST"])
def delete_audio():
    file_path = "Website/static/aurora_audio.mp3"
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"status": "delete"}), 200
    return jsonify({"error": "file not found"}), 404 

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    response = chat_with_ai(user_message)
    audio_filename = text_to_speech(response)

    return jsonify({
        "response": response,
        "audio_url": f"/static/{audio_filename}" if audio_filename else None
    })

@app.route("/get_random_word", methods=["GET"])
def get_random_word():
    with open("wordlist.sh", "r") as f:
        words = [line.strip() for line in f if len(line.strip()) == 5]
    random_word = random.choice(words)
    return jsonify({"word": random_word})

@app.route("/launchPong", methods=["POST"])
def launchPong():
    try:
        python_executable = sys.executable
        subprocess.Popen([python_executable, "pong.py"])
        return jsonify({"status": "Pong launched!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/launchTugOfWar", methods=["POST"])
def launchTugOfWar():
    try:
        python_executable = sys.executable
        subprocess.Popen([python_executable, "tugOfWar.py"])
        return jsonify({"status": "Tug of War launched!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/launchClickRunner", methods=["POST"])
def launchClickRunner():
    try:
        python_executable = sys.executable
        subprocess.Popen([python_executable, "clickRunner.py"])
        return jsonify({"status": "Click Runner launched!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
