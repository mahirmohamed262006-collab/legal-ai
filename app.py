import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types

from chatbot_config import CHATBOT_TITLE, SYSTEM_PROMPT, MODEL_NAME

load_dotenv()

app = Flask(__name__)

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


@app.get("/")
def index():
    return render_template(
        "index.html",
        chatbot_title=CHATBOT_TITLE,
    )


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    if client is None:
        return jsonify({
            "error": "Gemini API is not configured. Add GEMINI_API_KEY to the .env file."
        }), 500

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
            ),
        )

        answer = (response.text or "").strip()

        if not answer:
            answer = (
                "I could not generate a response. "
                "Please ask a legal-information or document-guidance question."
            )

        return jsonify({"answer": answer})

    except Exception:
        app.logger.exception("Gemini request failed")
        return jsonify({
            "error": "The chatbot could not process your request right now."
        }), 500


@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "gemini_configured": client is not None,
        "model": MODEL_NAME,
    })


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower() == "true",
    )
