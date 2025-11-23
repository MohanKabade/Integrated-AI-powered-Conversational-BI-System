import google.generativeai as genai
from .nl_to_sql import load_schema,format_schema_for_prompt
import os
def is_sql_related(user_question, schema_file, api_key):
    """
    Uses Gemini to determine if the user's question is SQL-related.
    Returns True if SQL can be generated, False if it's just a greeting or unrelated.
    """

    try:
        # Load and format schema (optional but helps context)
        #schema = load_schema(schema_file)
        schema_file = os.path.join(os.path.dirname(__file__), schema_file)
        schema = load_schema(schema_file)
        formatted_schema = format_schema_for_prompt(schema)

        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # ✨ Prompt Engineering
        prompt = f"""
You are a classification assistant.

You are given a user's question and a database schema.

Decide if this question is suitable for generating an SQL query.
- If the question is related to databases, tables, data, or queries → respond with "True".
- If the question is a greeting, casual chat, or unrelated to databases → respond with "False".
- Reply ONLY with True or False — no explanations, no punctuation.

Database schema:
{formatted_schema}

User question: "{user_question}"
"""

        # Generate classification
        response = model.generate_content(prompt)
        answer = response.text.strip().lower()

        # Normalize output
        if "true" in answer:
            return True
        elif "false" in answer:
            return False
        else:
            # Fallback — Gemini gave unexpected text
            return False

    except Exception as e:
        print("Error checking SQL intent:", str(e))
        return False


def handle_greetings(user_question, api_key):
    """
    Handles general conversation or greeting-type queries.
    Returns a short, friendly answer from the perspective of
    a conversational BI (Business Intelligence) analyst.
    """

    try:
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")

        # Prompt Engineering 🧠
        prompt = f"""
You are a friendly Conversational Business Intelligence Analyst.

Your role:
- Greet users and respond to small talk.
- Explain politely what you can do when asked.
- You can mention that you help people analyze data and generate SQL queries.
- Keep replies short, natural, and conversational.
- Do NOT write SQL queries or technical code.

User: {user_question}
Assistant:
"""

        # Generate response
        response = model.generate_content(prompt)
        answer = response.text.strip()

        return answer

    except Exception as e:
        return f"Error generating response: {str(e)}"




user_input = "Give me the batter name who scored most runs"
api_key = "AIzaSyA7bYdd8uv0-dlc2YvwZKSnAD503itYe24"
schema_file = "schema_registry.json"

if is_sql_related(user_input, schema_file, api_key):
    print("✅ Proceed to generate SQL.")
else:
    print("💬 It's just a greeting or general chat.")
