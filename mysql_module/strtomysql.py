import pandas as pd
from sqlalchemy import create_engine
import pymysql
import re, json

# ------------------ COLUMN CLEANING ------------------
def clean_column_names(columns):
    """Clean column names for MySQL compatibility"""
    cleaned = []
    seen = {}
    for col in columns:
        col = col.strip().lower()
        col = re.sub(r'[^a-z0-9_]', '_', col)  # replace special chars
        if col[0].isdigit():
            col = "col_" + col
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
        cleaned.append(col)
    return cleaned

# ------------------ TYPE MAPPING ------------------
def map_dtype_to_mysql(series: pd.Series):
    """Map pandas dtype to optimal MySQL type"""
    if pd.api.types.is_integer_dtype(series):
        min_val, max_val = series.min(), series.max()
        if pd.isnull(min_val) or pd.isnull(max_val):
            return "INT"
        if min_val >= -128 and max_val <= 127:
            return "TINYINT"
        elif min_val >= -32768 and max_val <= 32767:
            return "SMALLINT"
        elif min_val >= -2147483648 and max_val <= 2147483647:
            return "INT"
        else:
            return "BIGINT"
    elif pd.api.types.is_float_dtype(series):
        # If all floats are actually integers, downgrade to INT
        if (series.dropna() % 1 == 0).all():
            return "INT"
        return "DOUBLE"
    elif pd.api.types.is_bool_dtype(series):
        return "TINYINT(1)"
    elif pd.api.types.is_datetime64_any_dtype(series):
        return "DATETIME"
    else:
        max_len = series.astype(str).map(len).max()
        varchar_len = min(max_len + 10, 500)
        return f"VARCHAR({varchar_len})"

# ------------------ PREPROCESSING ------------------
def preprocess_dataframe(df):
    """Basic preprocessing before uploading to MySQL"""
    print(f"Before cleaning: {len(df)} rows")
    # 1. Drop duplicate rows
    df = df.drop_duplicates()

    # 2. Drop rows with missing values
    #df = df.dropna()
    df = df.fillna("NULL")

    print(f"After cleaning: {len(df)} rows")

    # 3. Force integer type if column looks like an ID
    for col in df.columns:
        if "id" in col.lower():
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")  # nullable int

    # 3. Try converting numeric-looking strings to numbers
    for col in df.select_dtypes(include="object").columns:
        if df[col].str.replace(".", "", 1).str.isnumeric().all():
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4. Convert datetime only if column name suggests it's a date
    for col in df.columns:
        if "date" in col.lower():
            df[col] = pd.to_datetime(df[col], errors="coerce")

    return df


# ------------------ MAIN UPLOAD FUNCTION ------------------
def upload_to_mysql(file_path, table_name, db_user, db_password, db_host, db_name, schema_file="schema_registry.json"):
    # 1. Read file
    ext = file_path.split(".")[-1].lower()
    if ext == "csv":
        df = pd.read_csv(file_path)
    elif ext in ["xls", "xlsx"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or Excel.")

    # 2. Clean column names
    df.columns = clean_column_names(df.columns)

    # 3. Preprocess data
    df = preprocess_dataframe(df)

    # 4. Connect to MySQL
    conn = pymysql.connect(host=db_host, user=db_user, password=db_password, database=db_name)
    cursor = conn.cursor()

    # 5. Build CREATE TABLE with intelligent mapping
    col_defs = []
    schema_dict = {}
    for col in df.columns:
        mysql_type = map_dtype_to_mysql(df[col])
        schema_dict[col] = mysql_type
        col_defs.append(f"`{col}` {mysql_type}")

    create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(col_defs)});"

    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")  # fresh table
    cursor.execute(create_table_sql)

    # 6. Insert data
    for _, row in df.iterrows():
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(df.columns)}) VALUES ({placeholders})"
        cursor.execute(insert_sql, tuple(row))
    conn.commit()



    # 7. Save schema as JSON
    schema_json = {
    table_name: {
        "table_name": table_name,
        "columns": [
            {"name": col, "type": mysql_type}
            for col, mysql_type in schema_dict.items()
        ]
    }
    }

    with open(schema_file, "w") as f:
        json.dump(schema_json, f, indent=4)

    conn.close()

    print(f"✅ File '{file_path}' uploaded to MySQL as '{table_name}'.")
    print(f"✅ Schema saved to '{schema_file}'.")
    return schema_dict

# ------------------ Example Usage ------------------
if __name__ == "__main__":
    schema = upload_to_mysql(
        file_path="C:/Users/Admin/Deep Learning Lab/datasets/ipl_matches.csv",   # <-- your CSV/Excel file
        table_name="batsman_season_record",       # <-- MySQL table name
        db_user="root",                # <-- your MySQL username
        db_password="mohan#5928",     # <-- your MySQL password
        db_host="127.0.0.1",           # <-- usually localhost
        db_name="edi"            # <-- your database
    )

    print("\nExtracted Schema:")
    print(json.dumps(schema, indent=4))
