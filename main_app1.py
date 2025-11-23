from flask import Flask, render_template, request
import os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = "secret123"

# Global state
chat_history = []
current_mode = None        # "mysql" or "pdf"
current_namespace = None   # Only for PDF/DOC
current_filename = None 


@app.route("/", methods=["GET", "POST"])
def index():
    global current_mode, current_namespace, chat_history,current_filename

    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return render_template("index1.html", error="Please select a file.")

        filename = file.filename
        current_filename=filename
        ext = filename.lower().split(".")[-1]

        info_msg = ""

        # ==============================
        # Lazy import (important!)
        # ==============================

        if ext in ["csv", "xlsx"]:
            current_mode = "mysql"
            current_namespace = None

            from mysql_module.mysql_handler import process_mysql_file
            result = process_mysql_file(file, upload_folder=app.config["UPLOAD_FOLDER"])
            info_msg = result["message"]

            chat_history = []  # clear chat

        elif ext in ["pdf", "doc", "docx"]:
            current_mode = "pdf"

            from pdf_module.pdf_handler import process_pdf_file
            result = process_pdf_file(file, upload_folder=app.config["UPLOAD_FOLDER"])
            current_namespace = result["namespace"]
            info_msg = result["message"]

            chat_history = []

        else:
            return render_template("index1.html", error="Unsupported file type.")

        return render_template("chat1.html", messages=chat_history, info_msg=info_msg,filename=current_filename,)

    return render_template("index1.html")


@app.route("/chat1", methods=["GET", "POST"])
def chat():
    global chat_history, current_mode, current_namespace,current_filename

    if current_mode is None:
        return render_template("index1.html", error="Please upload a file first.")

    if request.method == "POST":
        question = request.form.get("question")

        if question:
            chat_history.append({"user": question, "bot": None})

            # ==============================
            # Lazy import here also
            # ==============================

            if current_mode == "mysql":
                from mysql_module.mysql_handler import answer_mysql_question
                answer = answer_mysql_question(question)

            elif current_mode == "pdf":
                from pdf_module.pdf_handler import answer_pdf_question
                answer = answer_pdf_question(question, current_namespace)

            else:
                answer = {"type": "text", "content": "Please upload a file first."}

            chat_history[-1]["bot"] = answer
            current_sql_query = answer.get("sql_query", None)


    return render_template("chat1.html", messages=chat_history,info_msg=None,
        filename=current_filename,sql_query=current_sql_query)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("static", exist_ok=True)

    # Disable auto-reload to prevent duplicate OpenMP loading
    app.run(debug=False, use_reloader=False)
