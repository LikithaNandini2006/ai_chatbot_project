
## Output Preview

![AI Data Generator output](ai-chatbot/assets/app-screenshot.png)

# AI Query & Code Generator Chatbot

## Overview

AI Query & Code Generator Chatbot is a Flask-based web application that uses an AI API to generate SQL queries and Python code from natural language prompts. Users can enter a requirement such as:

> Generate 50 employee records with name, age, and salary

The chatbot analyzes the request and generates:

* SQL Queries
* Python Code
* Structured Output
* Sample Data Generation Logic

This project demonstrates the integration of Large Language Models (LLMs) with a Flask web application.

---

## Features

* Natural Language Input
* AI-Powered Response Generation
* SQL Query Generation
* Python Code Generation
* Clean Web Interface
* Flask Backend
* OpenAI API Integration
* Responsive Design
* No Database Required

---

## Tech Stack

### Frontend

* HTML5
* CSS3
* JavaScript

### Backend

* Python
* Flask

### AI Integration

* OpenAI API

### Environment Management

* Python Virtual Environment
* python-dotenv

---

## Project Structure

```text
AI_QUERY_GENERATOR/
│
├── app.py
├── requirements.txt
├── .env
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── script.js
│
└── README.md
```

---

## Installation

### Clone Repository

```bash
git clone https://github.com/your-username/AI_QUERY_GENERATOR.git
cd AI_QUERY_GENERATOR
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Virtual Environment

#### Windows

```bash
venv\Scripts\activate
```

#### Linux / Mac

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure API Key

Create a `.env` file in the project root directory.

```env
OPENAI_API_KEY=your_api_key_here
```

---

## Run the Project

```bash
python app.py
```

Application will run at:

```text
http://127.0.0.1:5000
```

---

## Example Input

```text
Generate 50 employee records with name, age and salary
```

---

## Example Output

### SQL Query

```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    salary DECIMAL(10,2)
);
```

### Python Code

```python
import pandas as pd

data = {
    "name": ["Ravi", "Kiran"],
    "age": [25, 28],
    "salary": [35000, 40000]
}

df = pd.DataFrame(data)
print(df)
```

---


## Requirements

```text
Flask
openai
python-dotenv
```

---

## Future Enhancements

* Download Generated Code
* Download SQL File
* Export Results as CSV
* Multiple AI Models Support
* User Authentication
* Chat History
* Dark Mode
* Code Syntax Highlighting

---

## Learning Outcomes

Through this project you will learn:

* Flask Application Development
* REST API Handling
* OpenAI API Integration
* Prompt Engineering
* Frontend and Backend Integration
* Environment Variable Management
* AI-Powered Application Development

---

## Author

Likitha Nandini

GitHub Profile:

https://github.com/LikithaNandini2006

---

## License

This project is developed for educational and learning purposes.
