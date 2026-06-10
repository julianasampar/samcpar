"""
reader.py

This module defines HOW the profiler reads data.
It does NOT profile, describe, or call any LLM.
Its only job: connect to a data source and return data/schema.
"""

from abc import ABC, abstractmethod
import duckdb
import snowflake.connector

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class DataSource(ABC):

    @abstractmethod
    def list_tables(self) -> list[str]:
        """
        Returns a list of table (or file) names available in this source.
        Example: ['rental', 'customer', 'film']
        """
        pass

    @abstractmethod
    def read_table(self, table_name: str, filter: dict = None, sample_size: int = 1000) -> "duckdb.DuckDBPyRelation":
        """
        Returns a DuckDB relation (lazy query) for the given table.
        The data is NOT fully loaded into memory — DuckDB reads it on demand.

        Parameters:
            table_name  : the name of the table to read
            filter      : Optional. Dict containing column name and value to filter.
                          If filter is provided, the JSON schema should contain the following structure:
                             {"<name_of_datasource>": {"column": "<name_of_column>", "value_to_filer":"value_1"}}
            sample_size : max number of rows to sample (default: 1,000)
        """
        pass

    @abstractmethod
    def get_schema(self, table_name: str) -> list[dict]:
        """
        Returns the schema of a table as a list of column definitions.
        Each column is a dict with keys: 'name', 'type', 'nullable'

        Example:
            [
                {"name": "rental_id",   "type": "INTEGER", "nullable": False},
                {"name": "rental_date", "type": "TIMESTAMP", "nullable": True},
            ]
        """
        pass

    @abstractmethod
    def get_table_ref(self, table_name: str) -> str:
        """
        Returns the SQL FROM clause reference for this source.
        DuckDB:   "read_csv_auto('./data/rental.csv')"
        Snowflake: "ANALYTICS.DVD_RENTALS.RENTAL"
        """
        pass

    @abstractmethod
    def get_percentile_sql(self, col: str, percentile: float) -> str:
        """
        Returns the SQL expression for a percentile calculation.
        DuckDB:    QUANTILE_CONT("col", 0.25)
        Snowflake: PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY "col")
        """
        pass

    @abstractmethod
    def execute_query(self, query: str) -> str:
        """
        Executes the SQL query inside the proper database.
        """
        pass


#######################################
#       CSV IMPLEMENTATION            #
#######################################
# This is the concrete implementation for a folder of CSV files.

class CSVDataSource(DataSource):

    def __init__(self, folder_path: str, **kwargs):
        """
        Sets up the data source pointing to a folder of CSV files.

        Parameters:
            folder_path : path to the folder containing your .csv files
                          Example: "./data/dvd_rentals"
        """
        # Path() turns a string like "./data" into a proper filesystem path
        self.folder_path = Path(folder_path)

        # One shared DuckDB connection for all queries in this source
        # duckdb.connect() without arguments = in-memory database
        self.conn = duckdb.connect('discovery_agent_database.db')

        # Validate that the folder actually exists
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")

    def list_tables(self) -> list[str]:
        """
        Scans the folder and returns the name of each CSV file (without extension).
        Example: 'rental.csv' → 'rental'
        """
        # glob("*.csv") finds all files ending in .csv inside the folder
        # .stem gives us the filename without the extension
        return [f.stem for f in self.folder_path.glob("*.csv")]

    def read_table(self, table_name: str, filter: dict = None, sample_size: int = 1000) -> "duckdb.DuckDBPyRelation":
        """
            Reads a CSV file using DuckDB and returns a sampled relation.

            - read_csv_auto() detects column types automatically
            - USING SAMPLE limits rows BEFORE loading into memory (efficient)
            - Returns a DuckDB relation, not a full dataframe
            - The filters dict should be declared like:
                {"column": "<name_of_column>", "value_to_filer":"value_1"}
            """
        path = self.folder_path / f"{table_name}.csv"
        
        if not path.exists():
                raise FileNotFoundError(f"Table not found: {path}")
        
        if not filter:
            query = f"""
                    SELECT *
                    FROM read_csv_auto('{path}')
                    USING SAMPLE {sample_size} ROWS
            """

        else:
            for column, value in filter.items():
                query = f"""
                    SELECT *
                    FROM read_csv_auto('{path}')
                    WHERE {column} = {value}
                    USING SAMPLE {sample_size} ROWS
                """

        return self.conn.execute(query)

    def get_schema(self, table_name: str) -> list[dict]:
        """
        Uses DuckDB's DESCRIBE statement to get column names and types.
        Returns a clean list of dicts — easy to pass to the LLM later.
        """
        path = self.folder_path / f"{table_name}.csv"

        if not path.exists():
            raise FileNotFoundError(f"Table not found: {path}")

        # DESCRIBE returns: column_name, column_type, null, key, default, extra
        rows = self.conn.execute(f"""
            DESCRIBE SELECT * FROM read_csv_auto('{path}')
        """).fetchall()

        # Reshape into clean dicts for easier use downstream
        return [
            {
                "name":     row[0],
                "type":     row[1],
                "nullable": row[2] == "YES",
            }
            for row in rows
        ]
    
    def get_table_ref(self, table_name: str) -> str:
        path = self.folder_path / f"{table_name}.csv"
        return f"read_csv_auto('{path}')"
    
    def get_percentile_sql(self, col: str, percentile: float) -> str:
        return f'QUANTILE_CONT("{col}", {percentile})'
    
    def execute_query(self, query: str):
        return self.conn.execute(query)

#######################################
#   SNOWFLAKE IMPLEMENTATION          #
#######################################
# This is the concrete implementation for data living in Snowflake DW.

class SnowflakeDataSource(DataSource):
    def __init__(
            self, 
            database=os.getenv('SNOWFLAKE_DATABASE'), 
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
            **kwargs
            ):
        self.conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=database,
            schema=schema,
            session_parameters={
                'QUERY_TAG': 'DataDiscoveryAgent',
            }
        )
        self.database=database
        self.schema=schema

    def list_tables(self) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute(f"SHOW TABLES IN SCHEMA {self.database}.{self.schema}")
        return [row[1] for row in cursor.fetchall()]
    
    def read_table(self, table_name: str, filter: dict = None, sample_size: int = 10_000):
        cursor = self.conn.cursor()

        if not filter:
            cursor.execute(f"""
                SELECT *
                FROM {self.database}.{self.schema}.{table_name}
                LIMIT {sample_size}
            """)

        else:
            # Extract filter - handle nested structure {source_type: {column: ..., value_to_filter: ...}}
            actual_filter = filter
            if len(filter) == 1 and isinstance(next(iter(filter.values())), dict):
                actual_filter = next(iter(filter.values()))

            # Get column and value (note: field is "value_to_filter", not "value_to_filer")
            column = actual_filter.get("column")
            # Handle both spellings and check for None explicitly (not falsy!)
            value = actual_filter.get("value_to_filter")
            if value is None:
                value = actual_filter.get("value_to_filer")

            if column is None or value is None:
                # Fallback: get first key-value pair
                column, value = next(iter(actual_filter.items()))

            # Convert column name to uppercase for Snowflake (case-sensitive when quoted)
            column_upper = column.upper() if isinstance(column, str) else column

            query = f"""
                SELECT *
                FROM {self.database}.{self.schema}.{table_name}
                WHERE "{column_upper}" = '{value}'
                LIMIT {sample_size}
            """
            cursor.execute(query)
        return cursor

    def get_schema(self, table_name: str) -> list[dict]:
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = '{self.schema}'
              AND table_name   = '{table_name.upper()}'
        """)
        return [
            {"name": row[0], "type": row[1], "nullable": row[2] == "YES"}
            for row in cursor.fetchall()
        ]
    
    def get_table_ref(self, table_name: str) -> str:
        return f"{self.database}.{self.schema}.{table_name.upper()}"
    
    def get_percentile_sql(self, col: str, percentile: float) -> str:
        return f'PERCENTILE_CONT({percentile}) WITHIN GROUP (ORDER BY "{col}")'
    
    def execute_query(self, query: str):
        """
        Unified execute method so the profiler doesn't care
        whether it's talking to DuckDB or Snowflake.
        """
        cursor = self.conn.cursor()
        cursor.execute(query)
        return cursor
    
    
############################################
#               DEFAULT TOOL              #
############################################
# This function gets the right connection by declaring the source_type

def get_datasource(source_type: str, **kwargs) -> DataSource:
    """
    Returns the correct DataSource implementation based on source_type.

    Usage:
        source = get_datasource("csv", folder_path="./data/dvd_rentals")

    Parameters:
        source_type : one of "csv" (more to come)
        **kwargs    : arguments passed to the DataSource constructor
    """
    sources = {
        "csv": CSVDataSource,
        "snowflake": SnowflakeDataSource,
    }

    if source_type not in sources:
        raise ValueError(f"Unknown source type '{source_type}'. Available: {list(sources.keys())}")

    return sources[source_type](**kwargs)