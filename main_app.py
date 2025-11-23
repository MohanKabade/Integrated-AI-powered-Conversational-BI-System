from flask import Flask, render_template, request
import os

from mysql_module.mysql_handler import process_mysql_file, answer_mysql_question
from pdf_module.pdf_handler import process_pdf_file, answer_pdf_question

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "secret123"

# Global state (simple for single-user / demo use)
chat_history = []          # list of {"user": ..., "bot": ...}
current_mode = None        # "mysql" or "pdf"
current_namespace = None   # used only for PDF/DOC


@app.route("/", methods=["GET", "POST"])
def index():
    global current_mode, current_namespace, chat_history

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return render_template("index.html", error="Please select a file.")

        filename = file.filename.lower()
        ext = filename.split(".")[-1]

        info_msg = ""

        # Decide module based on extension
        if ext in ["csv", "xlsx"]:
            current_mode = "mysql"
            current_namespace = None
            result = process_mysql_file(file, upload_folder=app.config["UPLOAD_FOLDER"])
            info_msg = result["message"]
            chat_history = []   # clear history when new file uploaded

        elif ext in ["pdf", "doc", "docx"]:
            current_mode = "pdf"
            result = process_pdf_file(file, upload_folder=app.config["UPLOAD_FOLDER"])
            current_namespace = result["namespace"]
            info_msg = result["message"]
            chat_history = []   # clear history when new file uploaded

        else:
            return render_template("index.html", error="Unsupported file type.")

        # Go directly to chat page after upload
        return render_template("chat.html", messages=chat_history, info_msg=info_msg)

    return render_template("index.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    global chat_history, current_mode, current_namespace

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            # Store user message
            chat_history.append({"user": question, "bot": None})

            # Decide which module to call
            if current_mode == "mysql":
                answer = answer_mysql_question(question)

            elif current_mode == "pdf":
                if current_namespace is None:
                    answer = {"type": "text", "content": "No document loaded. Please upload a file again."}
                else:
                    answer = answer_pdf_question(question, current_namespace)

            else:
                answer = {"type": "text", "content": "Please upload a file first."}

            # Store bot message (string or image info)
            chat_history[-1]["bot"] = answer

    return render_template("chat.html", messages=chat_history)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True)
