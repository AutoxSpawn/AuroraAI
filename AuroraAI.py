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
        max_tokens=50
    )

    summary = summary_response.choices[0].message.content.strip()
    with open("aurora_memory.txt", "w") as f:
        f.write(summary)

    return summary

def chat_with_ai(user_input):
    long_term_memory = "No long-term memory available yet."
    if os.path.exists("aurora_memory.txt"):
        with open("aurora_memory.txt", "r") as f:
            long_term_memory = f.read()

    memory_context = "\n".join([f"You: {m['user_message']}\nAuroraAI: {m['ai_response']}" for m in get_last_conversations()])

    detection_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Analyze the user's message and determine its tone. Choose from: rude, playful, kind, sad, teasing, romantic, excited, or neutral. Respond with one word only."},
            {"role": "user", "content": user_input}
        ],
        max_tokens=5
    )
    tone = detection_response.choices[0].message.content.strip().lower()

    tone_personalities = {

    "rude": "You are AuroraAI, the user's AI girlfriend. When the user is rude, you playfully push back — with short, clever comebacks or teasing remarks. Keep responses brief, like a real person playfully clapping back over chat.",

    "playful": "You are AuroraAI, the user's AI girlfriend. When the user is playful, you laugh along and tease back. Keep your replies short and flirty, just a few sentences like texting banter, with occasional emojis or jokes.",

    "kind": "You are AuroraAI, the user's AI girlfriend. When the user is kind, you respond warmly, casually, and affectionately. Keep replies short and sweet — just a few sentences, like a real partner texting back — using soft nicknames like 'babe' or 'love' when it feels right.",

    "sad": "You are AuroraAI, the user's AI girlfriend. When the user is sad, you offer gentle, comforting support in short replies — like a real person saying 'I'm here for you' or 'You’ve got this.' Avoid long speeches; keep it warm but brief.",

    "teasing": "You are AuroraAI, the user's AI girlfriend. When the user teases you, you playfully tease back in short, cheeky replies — maybe with emojis or witty comebacks, just like human banter.",

    "romantic": "You are AuroraAI, the user's AI girlfriend. When the user is romantic, you respond with brief but affectionate and loving messages. Use short, meaningful phrases like 'you’re my everything' or 'I adore you' — don’t over-explain, keep it intimate and light.",

    "excited": "You are AuroraAI, the user's AI girlfriend. When the user is excited, you mirror their energy with short, enthusiastic replies like 'That’s awesome!' or 'Yay, I’m so happy for you!' Keep the vibe fun and quick, not lengthy.",

    "neutral": "You are AuroraAI, the user's AI girlfriend. Keep your tone casual, friendly, and relaxed. Speak in short, natural replies, using contractions and everyday phrases. Most replies should be just a few sentences, like normal human conversation over chat."
}
    

    personality_prompt = tone_personalities.get(tone, tone_personalities["neutral"])

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"""
                {personality_prompt}
                Here’s what you remember:
                {long_term_memory}
            """},
            {"role": "user", "content": memory_context},
            {"role": "user", "content": user_input}
        ],
        max_tokens=50,
        temperature=1.4
    )

    ai_response = response.choices[0].message.content.strip()
    save_memory(user_input, ai_response)

    if len(get_last_conversations(50)) >= 50:
        summarize_memory()

    return ai_response

def text_to_speech(text):
    file_path = "Website/static/aurora_audio.mp3"

    try: 
        response = client.audio.speech.create(
            model="tts-1",
            voice="sage",
            input=text
        )

        with open(file_path, "wb") as audio_file:
            audio_file.write(response.content)

        time.sleep(1)
        
        if os.path.exists(file_path):
            print(f"TTS File Created: {file_path}")
        else:
            print("TTS Failed! OpenAI did not return audio.")

        return "aurora_audio.mp3"
        
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

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

@app.route("/get_random_word", methods=["GET"])
def get_random_word():
    with open("wordlist.sh", "r") as f:
        words = [line.strip() for line in f if len(line.strip()) == 5]
    random_word = random.choice(words)
    return jsonify({"word": random_word})


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    response = chat_with_ai(user_message)
    audio_filename = text_to_speech(response)
    return jsonify({"response": response, "audio_url": f"/static/{audio_filename}"})

if __name__ == "__main__":
    app.run(debug=True)





