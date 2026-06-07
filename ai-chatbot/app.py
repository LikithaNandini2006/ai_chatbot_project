import json
import os

from flask import Flask, jsonify, render_template, request, send_file

from ai.text_to_sql import default_model, generate_sql

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history", "queries.json")
GENERATED_DIR = os.path.join(BASE_DIR, "generated")
GENERATED_SQL = os.path.join(GENERATED_DIR, "generated_query.sql")
DEFAULT_MODEL = default_model()


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_history(question, query):
    if not question or not query:
        return

    history = load_history()
    history.insert(
        0,
        {
            "question": question,
            "query": query,
        },
    )

    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history[:10], file, indent=4)


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    question = ""
    dialect = "MySQL"
    model = DEFAULT_MODEL

    if request.method == "POST":
        question = request.form.get("question") or request.form.get("prompt", "")
        dialect = request.form.get("dialect", "MySQL")
        model = request.form.get("model", DEFAULT_MODEL)
        result = generate_sql(question, dialect, model)

        if result.get("query"):
            save_history(question, result["query"])

    return render_template(
        "index.html",
        result=result,
        question=question,
        dialect=dialect,
        model=model,
        history=load_history(),
    )


@app.route("/generate", methods=["POST"])
def generate():
    payload = request.get_json(silent=True) or request.form
    question = payload.get("question") or payload.get("prompt", "")
    dialect = payload.get("dialect", "MySQL")
    model = payload.get("model", DEFAULT_MODEL)

    result = generate_sql(question, dialect, model)
    if result.get("query"):
        save_history(question, result["query"])

    return jsonify(
        {
            "result": result,
            "question": question,
            "dialect": dialect,
            "model": model,
            "history": load_history(),
        }
    )


@app.route("/download")
def download():
    sql = request.args.get("query", "")
    os.makedirs(GENERATED_DIR, exist_ok=True)

    with open(GENERATED_SQL, "w", encoding="utf-8") as file:
        file.write(sql)

    return send_file(GENERATED_SQL, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
