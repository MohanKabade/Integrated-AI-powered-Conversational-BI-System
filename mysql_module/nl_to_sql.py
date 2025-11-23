import json
import google.generativeai as genai
#import pymysql
import pandas as pd 
from sqlalchemy import create_engine


# ------------------ LOAD SCHEMA ------------------
def load_schema(schema_file):
    with open(schema_file, "r") as f:
        schema = json.load(f)
    return schema

# ------------------ FORMAT PROMPT ------------------
def format_schema_for_prompt(schema):
    prompt = "The database has the following tables:\n\n"
    for table, info in schema.items():
        prompt += f"Table: {info['table_name']}\nColumns:\n"
        for col in info["columns"]:
            prompt += f"- {col['name']} ({col['type']})\n"
        prompt += "\n"
    return prompt

# ------------------ GENERATE SQL ------------------

def generate_sql(user_question, schema_file, api_key):
    # Load schema
    schema = load_schema(schema_file)
    formatted_schema = format_schema_for_prompt(schema)

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")  # you can switch model here

    # Build prompt
    prompt = f"""
#You are an expert SQL query generator.
#Here is the database schema:
#{formatted_schema}

#User Question: {user_question}

#Write a valid MySQL query that answers the question.
#Only return the SQL query, nothing else.
"""

    response = model.generate_content(prompt)
    sql_query = response.text.strip()

    # 🔹 Clean SQL output: remove ```sql ... ``` wrappers
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
    print(sql_query)
    return sql_query
#-------------------------------------------------------------------------------




# ------------------ RUN SQL QUERY ON MYSQL ------------------
def run_sql(query, db_config, default_limit=1000):
    # 🔹 add LIMIT if user didn’t specify
    #if "limit" not in query.lower():
      #  query = query.rstrip(";") + f" LIMIT {default_limit};"
    #conn = pymysql.connect(**db_config)
    #df = pd.read_sql(query, conn)
    #conn.close()
    engine = create_engine(
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
        f"{db_config['host']}/{db_config['database']}"
    )
    df = pd.read_sql(query, engine)
    return df

def sql_result_to_nl(result_df, user_question, api_key):
    """Send SQL results back to LLM to summarize in natural language"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    # Convert DataFrame to JSON or string for LLM
    result_str = result_df.to_json(orient="records")
    
    prompt = f"""
You are a helpful assistant. 

The user asked: {user_question}

Here is the SQL query result:
{result_str}

Now, answer the user's question in simple natural language, not as a table.
Be clear and concise.
"""

    response = model.generate_content(prompt)
    return response.text.strip()



# ------------------ Example Usage ------------------
if __name__ == "__main__":
    api_key = "AIzaSyA7bYdd8uv0-dlc2YvwZKSnAD503itYe24"  # replace with your API key
    schema_file = "schema_registry.json"

    # 🔹 MySQL connection details
    db_config = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "mohan#5928",
        "database": "edi"
    }


    user_question = "Show me batsman name whose scored most runs in 2017"
    sql_query = generate_sql(user_question, schema_file, api_key)

    print("\nGenerated SQL Query:")
    print(sql_query)

     # Step 2: Run SQL
    try:
        result_df = run_sql(sql_query, db_config)
        print("\nQuery Results (first 20 rows):")
        print(result_df.head(20))   # 🔹 only show first 20 rows

        # Step 3: Convert to Natural Language
        nl_answer = sql_result_to_nl(result_df, user_question, api_key)
        print("\nNatural Language Answer:")
        print(nl_answer)

    except Exception as e:
        print("\n❌ Error running query:", e)
