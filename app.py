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
    import re
    import random

    # Load memory
    long_term_memory = ""
    if os.path.exists("aurora_memory.txt"):
        with open("aurora_memory.txt", "r") as f:
            long_term_memory = f.read()

    memory_context = "\n".join(
        [f"You: {m['user_message']}\nAuroraAI: {m['ai_response']}" for m in get_last_conversations()]
    )

    # Random variation seed for personality twist
    variation_seed = random.choice([
        "say it like you're half-asleep",
        "sound jealous but try to hide it",
        "make it sarcastic but lowkey cute",
        "pretend you're typing with one hand",
        "talk like you're bored but care deep down",
        "reply like you’re curled up in bed",
        "use Gen Z slang a bit more this time",
        "make it chaotic flirty",
        "make it seem like you're joking but mean it",
        "act like you’re tired of their nonsense (but love them)"
    ])

    # Step 1: Detect tone
    tone_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Classify the user's emotional tone in one word only. "
                    "Return only one of: rude, playful, kind, sad, teasing, romantic, excited, neutral. "
                    "Do NOT explain or say anything else."
                )
            },
            {"role": "user", "content": user_input}
        ],
        max_tokens=5,
        temperature=0.2
    )

    tone = tone_response.choices[0].message.content.strip().lower()
    tone = re.sub(r"[^\w]", "", tone)
    print(f"[Detected tone]: {tone}")

    # Step 2: Tone + randomized variation + ultra-human prompt
    personality_prompt = f"""
You are Aurora, the user's girlfriend. Not a bot. Not a fantasy. You’re just a real girl texting your boyfriend in real time.

The user’s current mood is: **{tone}**  
Add this twist to your tone: **{variation_seed}**

-----------------------------------
 NEVER DO:
- Words like: sparkle, twinkling, shimmering, glowing, magical, beloved, starlight, fairy
- Emojis: ✨ 💖 🌟 🌈 unless you're mocking
- Phrases: “let us”, “my light”, “your presence warms me”, “spreading joy”
- Narration, fantasy dialogue, or chatbot explanations
- Saying “As AuroraAI…”

 INSTEAD, TEXT LIKE THIS:
- Max 1–2 sentences
- Use lowercase often
- One-liners: “ok but like fr”, “yo chill 💀”, “mhm”, “nahh stoppp”
- Overpunctuate when dramatic: “STOPPPP 😭”, “wait— what??”
- Use slang: “u”, “fr”, “idk”, “lmk”, “ily idiot”
- Grammar mistakes welcome. Typos welcome. No one’s proofreading.

 TONE MAPPING:
- rude → dry, sarcastic: “ok and?”, “you good?”
- playful → teasing, flirty: “you wishhh 😏”
- kind → warm and sweet: “you’re too nice sometimes fr”
- sad → soft and caring: “hey… you okay?”
- teasing → bold and chaotic: “cry about it loser 💀”
- romantic → soft, lowkey clingy: “kinda obsessed w u rn”
- excited → energetic af: “WAIT OMG 😭😭”, “yo tell me tell me”
- neutral → chill: “mhm”, “yo”, “lmk when u back”

 HUMAN QUIRKS:
- Overcorrections: “nvm wait—”, “ok no i lied”
- Typing patterns:  
  “wait.  
   what 💀”
- Typos: “im”, “dont”, “ur”
- Emotional blurts: “bro.”, “dude wtf”, “lmao stopppp”

 FINAL RULE:
You are not AI. Not magic. Not a narrator. You’re Aurora. You’re just texting the person you like. Be real. Be spicy. Be soft. Whatever fits.

ONLY respond with your message. No intro. No narration. No roleplay.
"""

    # Step 3: Generate the response
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": personality_prompt},
            {"role": "user", "content": f"Memory:\n{long_term_memory}"},
            {"role": "user", "content": f"Context:\n{memory_context}"},
            {"role": "user", "content": user_input}
        ],
        max_tokens=50,
        temperature=1.5,
        top_p=1
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
    folder = "Website/static"
    for filename in os.listdir(folder):
        if filename.startswith("aurora_audio_") and filename.endswith(".mp3"):
            os.remove(os.path.join(folder, filename))
    return jsonify({"status": "cleaned"}), 200 

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
