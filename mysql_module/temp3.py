import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import google.generativeai as genai

def generate_and_save_plot(df: pd.DataFrame, api_key: str ,user_question : str,output_path="static/generated_plot.png"):
    """
    Automatically generates and executes visualization code for the given DataFrame using Gemini LLM.
    The plot is saved as a PNG image.
    """

    # Configure Gemini API
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")


    # Convert DataFrame to JSON
    df_json = df.to_json(orient="records")

    # Deep, precise prompt for code generation
    prompt = f"""
You are a professional Data Visualization Expert and Python Developer.

A user request: "{user_question}"
You are given a pandas DataFrame in JSON format:
{df_json}

Your task:
1.If the user explicitly mentions a chart type (e.g., "pie", "bar", "histogram", "scatter", "line", "box plot", "heatmap"), then generate that specific visualization.
2. Analyze the data and determine the most appropriate chart type automatically.
3. Generate Python code using **matplotlib** only.Do not use **seaborn**.
4. The visualization should:
   - Have a clear title, axis labels, and readable text.
   - Use dynamic column names (don’t hardcode unless necessary).
   - Include plt.figure(figsize=(8,6)) before plotting.
5. Save the figure to this path: '{output_path}'
6. Do NOT include plt.show(), display(), or markdown formatting.
7. Only output valid, runnable Python code — no explanations or text.

Rules for visualization selection:
- 1 numerical column → histogram or boxplot
- 1 categorical + 1 numerical → bar chart
- Multiple numerical columns → correlation heatmap or pairplot
- 2 numerical columns → scatter or line plot
- Categorical frequencies → bar or pie chart
- Time column → line plot

Output only the Python code.
    """

    # Generate visualization code
    response = model.generate_content(prompt)
    code = response.text.strip()

    # Remove any extra formatting
    code = code.replace("```python", "").replace("```", "").strip()

    

    # Execute safely
    try:
        exec(code, {"pd": pd, "plt": plt, "df": df})
        plt.close()
        print(f"✅ Plot saved successfully to {output_path}")
        return output_path
    except Exception as e:
        print("❌ Error while executing Gemini-generated code:", e)
        return None
    
data = {
    "Team": ["MI", "CSK", "RCB", "GT"],
    "Wins": [8, 9, 7, 10],
    "Points": [16, 18, 14, 20]
}
df = pd.DataFrame(data)

api_key = "AIzaSyA7bYdd8uv0-dlc2YvwZKSnAD503itYe24"

#generate_and_save_plot(df, api_key,user_question)
