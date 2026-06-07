SYSTEM_PROMPT = """You are an expert data engineer.
Convert the user's requirement into a practical SQL answer.

Rules:
- Return only useful code and short labels.
- Prefer safe, readable SQL.
- Match the requested SQL dialect.
- If the user asks for sample/fake data, include Python code after the SQL.
- Do not invent credentials or destructive statements.
"""


DIALECT_NOTES = {
    "MySQL": "Use MySQL syntax, AUTO_INCREMENT, backticks only when useful.",
    "PostgreSQL": "Use PostgreSQL syntax, SERIAL/IDENTITY, double quotes only when useful.",
    "SQLite": "Use SQLite syntax, INTEGER PRIMARY KEY AUTOINCREMENT.",
    "SQL Server": "Use SQL Server syntax, IDENTITY, TOP, and square brackets only when useful.",
}
