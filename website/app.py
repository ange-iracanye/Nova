import os
import sys
import traceback

ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        ".."
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from backend.engine import NovaEngine

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)

nova = NovaEngine()

print("Nova Engine Loaded")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chatpage")
def chatpage():
    return render_template("chat.html")


@app.route("/study")
def study():
    return render_template("study.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/upload")
def upload():
    return render_template("upload.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/history")
def history():
    return render_template("history.html")


@app.route("/new_chat", methods=["POST"])
def new_chat():

    nova.conversation.history.clear()

    return jsonify({
        "success": True
    })


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    message = data["message"]

    answer = nova.reply(message)

    print(type(answer))
    print(answer)

    if not isinstance(answer, str):
        answer = str(answer)

    return jsonify({
        "answer": answer
    })


if __name__ == "__main__":
    app.run(debug=True)