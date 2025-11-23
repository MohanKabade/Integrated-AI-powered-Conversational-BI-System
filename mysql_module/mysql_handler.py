import os
import uuid
from .strtomysql import upload_to_mysql
from .nl_to_sql import generate_sql, run_sql, sql_result_to_nl
from .temp import is_sql_related, handle_greetings
from .is_visulizable import is_visualizable
from .temp3 import generate_and_save_plot

API_KEY = "AIzaSyCwcMj-gspG4dRlmBhMFDFmF_7E_L-yPXo"   # <- put your key here
DB_CONFIG = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "mohan#5928",
    "database": "edi"
}

SCHEMA_FILE = os.path.join(os.path.dirname(__file__), "schema_registry.json")



def process_mysql_file(file_storage, upload_folder="uploads"):
    """
    Save CSV / Excel, upload to MySQL, update schema_registry.json.
    Used once when file is uploaded.
    """
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, file_storage.filename)
    file_storage.save(filepath)

    table_name = os.path.splitext(file_storage.filename)[0]

    schema = upload_to_mysql(
        file_path=filepath,
        table_name=table_name,
        db_user=DB_CONFIG["user"],
        db_password=DB_CONFIG["password"],
        db_host=DB_CONFIG["host"],
        db_name=DB_CONFIG["database"]
    )

    print("✅ MySQL schema generated:", schema)
    return {"message": "CSV/Excel uploaded successfully! MySQL BI module activated."}


def answer_mysql_question(user_question):
    """
    Take user question and return:
    - {"type": "text", "content": "..."}  OR
    - {"type": "image", "path": "generated_plot_x.png"}
    """
    # 1) Is it a SQL/data question?
    if is_sql_related(user_question, SCHEMA_FILE, API_KEY):
        # Step 1: NL → SQL
        sql_query = generate_sql(user_question, SCHEMA_FILE, API_KEY)

        # Step 2: run SQL
        df = run_sql(sql_query, DB_CONFIG)

        # Step 3: is it visualizable?
        if is_visualizable(df, user_question):
            unique_id = str(uuid.uuid4())[:8]
            image_filename = f"generated_plot_{unique_id}.png"
            image_path = os.path.join("static", image_filename)

            generate_and_save_plot(
                df,
                API_KEY,
                user_question,
                output_path=image_path
            )

            return {"type": "image", "path": image_filename}

        else:
            # Step 4: result → natural language
            nl_answer = sql_result_to_nl(df, user_question, API_KEY)
            return {"type": "text", "content": nl_answer}

    # 2) Otherwise, treat it as greeting / small talk
    nl_answer = handle_greetings(user_question, API_KEY)
    return {"type": "text", "content": nl_answer}
