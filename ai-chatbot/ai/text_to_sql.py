import os
import re

from dotenv import load_dotenv

from ai.sql_instructions import DIALECT_NOTES, SYSTEM_PROMPT

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"

DEFAULT_ENTITY_COLUMNS = {
    "student": ["name", "email", "age", "city"],
    "students": ["name", "email", "age", "city"],
    "employee": ["name", "email", "phone", "salary"],
    "employees": ["name", "email", "phone", "salary"],
    "customer": ["name", "email", "phone", "city"],
    "customers": ["name", "email", "phone", "city"],
}

COLUMN_ALIASES = {
    "id": "id",
    "name": "name",
    "email": "email",
    "mail": "email",
    "phone": "phone",
    "mobile": "phone",
    "contact": "phone",
    "age": "age",
    "city": "city",
    "location": "city",
    "address": "address",
    "salary": "salary",
    "sal": "salary",
    "marks": "marks",
    "mark": "marks",
    "grade": "grade",
    "roll": "roll_no",
    "rollno": "roll_no",
    "rollnumber": "roll_no",
    "roll_no": "roll_no",
    "product": "product_name",
    "item": "product_name",
    "quantity": "quantity",
    "qty": "quantity",
    "stock": "quantity",
    "price": "price",
    "amount": "price",
    "cost": "price",
    "date": "sale_date",
    "created": "created_at",
    "timestamp": "created_at",
}


def generate_sql(question, dialect="MySQL", model=DEFAULT_MODEL):
    question = (question or "").strip()
    dialect = dialect or "MySQL"
    model = model or DEFAULT_MODEL

    if not question:
        return {
            "query": "",
            "error": "Please enter a requirement.",
            "model": model,
            "dialect": dialect,
        }

    if not _ai_enabled():
        return _fallback_generate(question, dialect)

    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        try:
            return _generate_with_groq(question, dialect, model, groq_key)
        except Exception as error:
            fallback = _fallback_generate(question, dialect)
            fallback["error"] = _ai_error_message("Groq", error)
            return fallback

    if openai_key:
        try:
            return _generate_with_openai(question, dialect, model, openai_key)
        except Exception as error:
            fallback = _fallback_generate(question, dialect)
            fallback["error"] = _ai_error_message("OpenAI", error)
            return fallback

    fallback = _fallback_generate(question, dialect)
    return fallback


def default_model():
    if not _ai_enabled():
        return "local-fallback"

    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_MODEL", DEFAULT_MODEL)
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    return DEFAULT_MODEL


def _ai_enabled():
    return os.getenv("ENABLE_AI", "").strip().lower() in {"1", "true", "yes", "on"}


def _ai_error_message(provider, error):
    status_code = getattr(getattr(error, "response", None), "status_code", None)
    if status_code == 401:
        reason = "API key is invalid or expired."
    elif status_code == 429:
        reason = "quota or rate limit reached."
    elif status_code:
        reason = f"request failed with HTTP {status_code}."
    else:
        reason = "network is blocked/unavailable or the model name is not allowed."

    return f"Local output shown because {provider} is unavailable: {reason}"


def _generate_with_groq(question, dialect, model, api_key):
    from groq import Groq

    client = Groq(api_key=api_key)
    dialect_note = DIALECT_NOTES.get(dialect, DIALECT_NOTES["MySQL"])
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n{dialect_note}"},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
        max_tokens=1200,
    )
    query = response.choices[0].message.content.strip()
    return {
        "query": query,
        "error": "",
        "model": model,
        "dialect": dialect,
        "provider": "groq",
    }


def _generate_with_openai(question, dialect, model, api_key):
    import httpx

    openai_model = _openai_model(model)
    dialect_note = DIALECT_NOTES.get(dialect, DIALECT_NOTES["MySQL"])
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": openai_model,
            "messages": [
                {"role": "system", "content": f"{SYSTEM_PROMPT}\n{dialect_note}"},
                {"role": "user", "content": question},
            ],
            "temperature": 0.2,
            "max_tokens": 1200,
        },
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    query = data["choices"][0]["message"]["content"].strip()
    return {
        "query": query,
        "error": "",
        "model": openai_model,
        "dialect": dialect,
        "provider": "openai",
    }


def _openai_model(model):
    configured = os.getenv("OPENAI_MODEL", "").strip()
    if configured:
        return configured

    model = (model or "").strip()
    if model and not model.lower().startswith("llama"):
        return model

    return DEFAULT_OPENAI_MODEL


def _fallback_generate(question, dialect):
    table_name = _table_name(question)
    columns = _guess_columns(question)
    create_sql = _create_table_sql(table_name, columns, dialect)
    parts = [f"-- {dialect} SQL\n{create_sql}"]

    if _wants_insert(question):
        parts.append(_insert_sql(table_name, columns, dialect))

    if _wants_python_generator(question):
        parts.extend(["-- Python fake data generator", _python_generator(table_name, columns)])

    query = "\n\n".join(parts)
    return {
        "query": query.strip(),
        "error": "",
        "model": "local-fallback",
        "dialect": dialect,
    }


def _wants_insert(question):
    text = question.lower()
    return any(
        phrase in text
        for phrase in [
            "insert",
            "sample row",
            "sample data",
            "example row",
            "example data",
            "values",
        ]
    )


def _wants_python_generator(question):
    text = question.lower()
    return any(
        phrase in text
        for phrase in [
            "python",
            "fake",
            "faker",
            "csv",
            "generate data",
            "generate records",
            "records",
            "rows",
            "100",
        ]
    )


def _table_name(question):
    before_table = re.search(r"(?:create|make|generate|build)\s+(.+?)\s+table", question, re.I)
    if before_table:
        raw = before_table.group(1)
        raw = re.sub(r"\b(a|an|the|new)\b", " ", raw, flags=re.I)
        words = re.findall(r"[a-zA-Z0-9]+", raw.lower())
        if words:
            return "_".join(words[-3:])

    match = re.search(r"(?:table|for|about)\s+([a-zA-Z][a-zA-Z0-9_\s]{1,40})", question, re.I)
    if match:
        raw = match.group(1).strip().split(" and ")[0].split(" with ")[0]
    else:
        raw = "generated_data"
    words = re.findall(r"[a-zA-Z0-9]+", raw.lower())
    return "_".join(words[:4]) or "generated_data"


def _guess_columns(question):
    text = question.lower()
    columns = [("id", "id")]
    explicit_columns = _extract_requested_columns(text)

    if explicit_columns:
        return _dedupe_columns(columns, explicit_columns)

    candidates = [
        ("name", ["name", "customer", "employee", "user"]),
        ("email", ["email", "mail"]),
        ("phone", ["phone", "mobile", "contact"]),
        ("age", ["age"]),
        ("city", ["city", "location", "address"]),
        ("salary", ["salary", "sal"]),
        ("marks", ["marks", "mark"]),
        ("grade", ["grade"]),
        ("roll_no", ["roll", "rollno", "roll number"]),
        ("product_name", ["product", "item"]),
        ("quantity", ["quantity", "qty", "stock"]),
        ("price", ["price", "amount", "cost"]),
        ("sale_date", ["sale", "date", "order"]),
        ("created_at", ["created", "timestamp"]),
    ]

    for column, keywords in candidates:
        if any(keyword in text for keyword in keywords):
            columns.append((column, column))

    for entity, defaults in DEFAULT_ENTITY_COLUMNS.items():
        if re.search(rf"\b{entity}\b", text):
            columns = _dedupe_columns(columns, defaults)
            break

    if len(columns) == 1:
        columns.extend(
            [
                ("name", "name"),
                ("email", "email"),
                ("created_at", "created_at"),
            ]
        )

    return columns


def _extract_requested_columns(text):
    match = re.search(r"\btable\b\s+(?:with\s+)?(.+)$", text)
    if not match:
        return []

    raw = match.group(1)
    raw = re.split(r"\b(?:and|for)\b\s+\d+\b|\b(?:records|rows|data)\b", raw)[0]
    tokens = re.findall(r"[a-zA-Z_]+", raw)
    columns = []

    for token in tokens:
        normalized = COLUMN_ALIASES.get(token.replace("_", ""))
        if normalized:
            columns.append(normalized)

    return columns


def _dedupe_columns(base_columns, new_columns):
    seen = {name for name, _ in base_columns}
    columns = list(base_columns)

    for column in new_columns:
        if column == "id" or column in seen:
            continue
        columns.append((column, column))
        seen.add(column)

    return columns


def _sql_type(column, dialect):
    if column == "id":
        if dialect == "PostgreSQL":
            return "SERIAL PRIMARY KEY"
        if dialect == "SQL Server":
            return "INT IDENTITY(1,1) PRIMARY KEY"
        if dialect == "SQLite":
            return "INTEGER PRIMARY KEY AUTOINCREMENT"
        return "INT AUTO_INCREMENT PRIMARY KEY"
    if column in {"age", "quantity", "marks"}:
        return "INT"
    if column in {"price", "amount", "cost", "salary"}:
        return "DECIMAL(10, 2)"
    if column.endswith("_date"):
        return "DATE"
    if column == "created_at":
        return "TIMESTAMP"
    return "VARCHAR(255)"


def _create_table_sql(table_name, columns, dialect):
    column_lines = [f"    {name} {_sql_type(name, dialect)}" for name, _ in columns]
    return f"CREATE TABLE {table_name} (\n" + ",\n".join(column_lines) + "\n);"


def _insert_sql(table_name, columns, dialect):
    data_columns = [name for name, _ in columns if name != "id"]
    values = [_sample_value(name, dialect) for name in data_columns]
    return (
        f"INSERT INTO {table_name} ({', '.join(data_columns)})\n"
        f"VALUES ({', '.join(values)});"
    )


def _sample_value(column, dialect):
    if column == "age":
        return "24"
    if column == "quantity":
        return "5"
    if column == "price":
        return "499.00"
    if column.endswith("_date"):
        return "'2026-06-07'"
    if column == "created_at":
        return "CURRENT_TIMESTAMP"
    if column == "email":
        return "'sample@example.com'"
    if column == "phone":
        return "'9876543210'"
    if column == "city":
        return "'Hyderabad'"
    if column == "address":
        return "'Hyderabad'"
    if column == "salary":
        return "50000.00"
    if column == "marks":
        return "85"
    if column == "grade":
        return "'A'"
    if column == "roll_no":
        return "'STU001'"
    if column == "product_name":
        return "'Demo Product'"
    return "'Sample Name'"


def _python_generator(table_name, columns):
    data_columns = [name for name, _ in columns if name != "id"]
    row_items = "\n        ".join(f'"{column}": sample_{column}(i),' for column in data_columns)
    helper_functions = "\n".join(_python_helper(column) for column in data_columns)
    return f'''```python
import csv
from datetime import date, timedelta


{helper_functions}


rows = []
for i in range(1, 101):
    rows.append({{
        {row_items}
    }})

with open("{table_name}.csv", "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Generated 100 rows in {table_name}.csv")
```'''


def _python_helper(column):
    if column == "email":
        return 'def sample_email(i):\n    return f"user{i}@example.com"\n'
    if column == "phone":
        return 'def sample_phone(i):\n    return f"98765{i:05d}"\n'
    if column == "age":
        return "def sample_age(i):\n    return 18 + (i % 35)\n"
    if column == "quantity":
        return "def sample_quantity(i):\n    return 1 + (i % 20)\n"
    if column == "price":
        return "def sample_price(i):\n    return round(99 + (i * 12.5), 2)\n"
    if column == "salary":
        return "def sample_salary(i):\n    return round(30000 + (i * 750), 2)\n"
    if column == "marks":
        return "def sample_marks(i):\n    return 40 + (i % 61)\n"
    if column == "grade":
        return 'def sample_grade(i):\n    return ["A", "B", "C", "D"][i % 4]\n'
    if column == "roll_no":
        return 'def sample_roll_no(i):\n    return f"STU{i:03d}"\n'
    if column.endswith("_date"):
        return f"def sample_{column}(i):\n    return (date.today() - timedelta(days=i)).isoformat()\n"
    if column == "created_at":
        return 'def sample_created_at(i):\n    return date.today().isoformat()\n'
    if column == "city":
        return 'def sample_city(i):\n    return ["Hyderabad", "Chennai", "Bengaluru", "Pune"][i % 4]\n'
    if column == "address":
        return 'def sample_address(i):\n    return f"Street {i}, Hyderabad"\n'
    if column == "product_name":
        return 'def sample_product_name(i):\n    return f"Product {i}"\n'
    return f'def sample_{column}(i):\n    return f"{column.title()} {{i}}"\n'
