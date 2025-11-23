import pandas as pd

def _text_intent_matches(user_query: str, keywords=None) -> bool:
    """Helper: check if user query contains visualization-related intent words."""
    if not user_query: 
        return False
    if keywords is None:
        keywords = [
            "each", "per", "by", "compare", "trend", "distribution",
            "count", "frequency", "how many", "top", "rank", "vs", "versus",
            "show me", "plot", "chart", "graph", "visualize", "visualise",
            "list top", "breakdown"
        ]
    q = user_query.lower()
    return any(k in q for k in keywords)

def is_visualizable(df: pd.DataFrame, user_query: str = "") -> bool:
    """
    Decide if df is visualizable in the context of user_query.
    Returns only True or False.
    """

    # Guard: invalid or empty DataFrame
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return False

    n_rows, n_cols = df.shape

    # Case 1: Single cell (1×1)
    if n_rows == 1 and n_cols == 1:
        return False

    # Case 2: Single row but multiple columns (usually one observation)
    if n_rows == 1:
        # Allow if user explicitly wants comparison
        return _text_intent_matches(user_query, ["compare", "vs", "versus", "between"])

    # Extract column types
    num_cols = df.select_dtypes(include="number").columns.tolist()
    datetime_cols = df.select_dtypes(include=["datetime", "datetime64"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Case 3: Multiple rows and at least one numeric column
    if n_rows >= 2 and len(num_cols) >= 1:
        return True

    # Case 4: Single categorical column
    if len(cat_cols) == 1 and len(num_cols) == 0:
        # True only if user query asks for frequency, distribution, etc.
        return _text_intent_matches(user_query, ["count", "frequency", "how many", "distribution", "top", "by", "per"])

    # Case 5: Multiple categorical columns (e.g., group comparisons)
    if len(cat_cols) >= 2 and len(num_cols) == 0:
        return _text_intent_matches(user_query, ["count", "group", "by", "breakdown", "distribution", "compare", "vs", "versus"])

    # Case 6: Datetime with numeric → time series
    if datetime_cols and len(num_cols) >= 1:
        return True

    # Case 7: Datetime only
    if datetime_cols and len(num_cols) == 0:
        return _text_intent_matches(user_query, ["trend", "over time", "per", "by"])

    # Default fallback
    return False



