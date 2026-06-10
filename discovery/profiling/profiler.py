"""
profiler.py

Computes descriptive statistics for every column in a table.
Uses DuckDB SQL — no LLM involved. Pure deterministic computation.

Returns a structured dict that the orchestrator will later pass to the LLM.
"""

from discovery.utils.reader import DataSource


# Setting numeric and date types
NUMERIC_TYPES = {
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
    "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC",
    "REAL", "INT", "INT2", "INT4", "INT8", "BYTEINT",
    "NUMBER",  "FLOAT4", "FLOAT8", "DOUBLE PRECISION"
}

DATE_TYPES = {
    "DATE", "TIMESTAMP", "TIMESTAMPTZ", "TIMESTAMP_NTZ",
    "TIMESTAMP WITH TIME ZONE", "TIMESTAMP WITHOUT TIME ZONE",
    "TIME", "TIMETZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ",
    "DATETIME"
}

def is_numeric(col_type: str) -> bool:
    """Returns True if the DuckDB column type is numeric."""
    # Normalize to uppercase and strip precision info (e.g. "DECIMAL(10,2)" → "DECIMAL")
    base_type = col_type.upper().split("(")[0].strip()
    return base_type in NUMERIC_TYPES

def is_date(col_type: str) -> bool:
    """Returns True if the DuckDB column type is date or timestamp."""
    base_type = col_type.upper().split("(")[0].strip()
    return base_type in DATE_TYPES


def profile_numeric_column(table_ref: str, col: str, source: DataSource) -> dict:
    """
    Runs a single SQL query to compute all numeric metrics for one column.

    Parameters:
        conn      : the active DuckDB connection
        table_ref : SQL reference to the table (e.g. "read_csv_auto('path/to/file.csv')")
        col       : column name to profile
        source    : the variable to access the class depending on the source type (e. g. source = get_datasource('snowflake'))
    """
    # We wrap the column name in double quotes to handle names with spaces or special chars
    query = f"""
        SELECT
            COUNT("{col}")                              AS count,
            AVG("{col}")                                AS mean,
            STDDEV("{col}")                             AS std,
            MIN("{col}")                                AS min,
            {source.get_percentile_sql(col, 0.25)}     AS "25%",
            {source.get_percentile_sql(col, 0.50)}      AS "50%",
            {source.get_percentile_sql(col, 0.75)}     AS "75%",
            MAX("{col}")                                AS max
        FROM {table_ref}
    """

    row = source.execute_query(query).fetchone()

    # fetchone() returns a tuple — we zip it with the column names to make a dict
    keys = ["count", "mean", "std", "min", "25%", "50%", "75%", "max"]
    return dict(zip(keys, row))


def profile_categorical_column(table_ref: str, col: str, source: DataSource) -> dict:
    """
    Runs SQL queries to compute all categorical metrics for one column.

    Parameters:
        conn      : the active DuckDB connection
        table_ref : SQL reference to the table
        col       : column name to profile
    """
    # Query 1: count and unique
    base_query = f"""
        SELECT
            COUNT("{col}")              AS count,
            COUNT(DISTINCT "{col}")     AS count_unique
        FROM {table_ref}
    """
    base_row = source.execute_query(base_query).fetchone()

    # Query 2: top value and its frequency
    # We order by frequency descending and take the first row
    top_query = f"""
        SELECT
            "{col}"         AS top,
            COUNT("{col}")  AS freq
        FROM {table_ref}
        WHERE "{col}" IS NOT NULL
        GROUP BY "{col}"
        ORDER BY freq DESC
        LIMIT 1
    """
    top_row = source.execute_query(top_query).fetchone()

    # top_row could be None if the column is entirely null
    top_val  = top_row[0] if top_row else None
    freq_val = top_row[1] if top_row else 0

    return {
        "count":  base_row[0],
        "unique": base_row[1],
        "top":    top_val,
        "freq":   freq_val,
    }


def get_distinct_values(table_ref: str, col: str, source: DataSource, threshold: int = 25) -> dict:
    """
    Returns the distinct values of a column, ordered by frequency descending.
    If the number of distinct values exceeds `threshold`, returns None instead
    of the list — to avoid cluttering the JSON and the LLM context window.

    Parameters:
        conn      : the active DuckDB connection
        table_ref : SQL reference to the table
        col       : column name
        threshold : max distinct values to list (default: 25)
                    Columns with more distinct values get skipped —
                    their count is already captured in the metrics dict.

    Returns a dict with:
        {
            "distinct_count": 5,
            "values": ["PG", "G", "PG-13", "R", "NC-17"],  ← or None if above threshold
            "skipped": False                                 ← True means too many values
        }
    """
    # Step 1: check how many distinct values exist BEFORE fetching them all
    # This avoids pulling thousands of rows just to decide to skip the column
    count_row = source.execute_query(f"""
        SELECT COUNT(DISTINCT "{col}") FROM {table_ref}
    """).fetchone()

    distinct_count = count_row[0]

    # Step 2: if above threshold, skip fetching the actual values
    if distinct_count > threshold:
        return {
            "distinct_count": distinct_count,
            "values":         None,
            "skipped":        True,
        }

    # Step 3: fetch actual values ordered by frequency (most common first)
    # NULL values are excluded — their presence is already captured in metrics
    rows = source.execute_query(f"""
        SELECT "{col}"
        FROM {table_ref}
        WHERE "{col}" IS NOT NULL
        GROUP BY "{col}"
        ORDER BY COUNT("{col}") DESC
    """).fetchall()

    # fetchall() returns a list of 1-tuples: [("PG",), ("G",), ...]
    # We unpack each tuple to get just the value
    values = [row[0] for row in rows]

    return {
        "distinct_count": distinct_count,
        "values":         values,
        "skipped":        False,
    }

def get_latest_date_values(table_ref: str, col: str, source: DataSource, limit: int = 10) -> list:
    """
    Returns the last `limit` non-null values of a date/timestamp column,
    ordered most-recent first. Nulls are excluded.

    This helps the LLM understand the temporal range and freshness of the data.
    For example, seeing the last 10 rental dates tells it whether the table is
    current, historical, or stale.

    Parameters:
        conn      : the active DuckDB connection
        table_ref : SQL reference to the table
        col       : name of the date/timestamp column
        limit     : how many recent values to return (default: 10)

    Returns a list of ISO-formatted date strings, most recent first:
        ["2006-02-14", "2006-02-13", "2006-02-12", ...]
    """
    rows = source.execute_query(f"""
        SELECT DISTINCT "{col}"
        FROM {table_ref}
        WHERE "{col}" IS NOT NULL
        ORDER BY "{col}" DESC
        LIMIT {limit}
    """).fetchall()

    # Convert each value to string (handles both date and timestamp types cleanly)
    return [str(row[0]) for row in rows]


############################################
#               DEFAULT TOOLS              #
############################################

def profile_table(source: DataSource, table_name: str, distinct_threshold: int = 25) -> dict:
    """
    Profiles all columns in a single table.
    Dispatches to numeric or categorical profiling per column,
    and appends distinct value information for each column.

    Parameters:
        source             : a DataSource instance (e.g. CSVDataSource)
        table_name         : name of the table to profile
        distinct_threshold : max distinct values to list per column (default: 25).
                             Columns with more values get skipped (values=None, skipped=True).
                             Tune down for wide/large tables, up for small lookup tables.
    """
    schema = source.get_schema(table_name)
    table_ref = source.get_table_ref(table_name)

    # Get total row count (includes nulls — this is the full table size)v
    row_count = source.execute_query(f"SELECT COUNT(*) FROM {table_ref}").fetchone()[0]

    columns_profile = {}

    for col_def in schema:
        col_name = col_def["name"]
        col_type = col_def["type"]

        if is_numeric(col_type):
            metrics = profile_numeric_column(table_ref, col_name, source)
            col_kind = "numeric"
        else:
            metrics = profile_categorical_column(table_ref, col_name, source)
            col_kind = "categorical"

        distinct = get_distinct_values(table_ref, col_name, source, threshold=distinct_threshold)

        # For date columns, fetch the last 10 values so the LLM can reason about
        # data freshness, temporal range, and activity patterns
        latest_dates = None
        if is_date(col_type):
            latest_dates = get_latest_date_values(table_ref, col_name, source)

        columns_profile[col_name] = {
            "type":         col_kind,
            "dtype":        col_type,       # original DuckDB type (e.g. "VARCHAR", "INTEGER")
            "nullable":     col_def["nullable"],
            "metrics":      metrics,
            "distinct":     distinct,
            "latest_dates": latest_dates,   # None for non-date columns
        }

    return {
        "table":     table_name,
        "row_count": row_count,
        "columns":   columns_profile,
    }


def profile_all_tables(source: DataSource, distinct_threshold: int = 25) -> dict:
    """
    Profiles every table available in a DataSource.
    Returns a dict keyed by table name.

    Usage:
        source  = get_datasource("csv", folder_path="./data/dvd_rentals")
        results = profile_all_tables(source)
        results = profile_all_tables(source, distinct_threshold=50)  # more permissive

    Parameters:
        source             : a DataSource instance
        distinct_threshold : passed through to profile_table (default: 25)
    """
    results = {}

    tables = source.list_tables()
    print(f"Found {len(tables)} table(s): {tables}\n")

    for table_name in tables:
        print(f"  Profiling: {table_name}...")
        results[table_name] = profile_table(source, table_name, distinct_threshold=distinct_threshold)
        print(f"  Done: {table_name} — {results[table_name]['row_count']} rows")

    return results